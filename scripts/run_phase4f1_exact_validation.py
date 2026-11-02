#!/usr/bin/env python3
"""
Phase 4F.1.1 — Exact Seq Scan Candidate-Cost Full Validation Script
===================================================================
Executes exactly 486 read-only EXPLAIN (SETTINGS, FORMAT JSON) captures
using exact-mode forcing (enable_indexscan=off, enable_bitmapscan=off, enable_seqscan=on)
across all 18 scales, 3 representations, and 9 planner profiles for canonical query q0.

Strict Safety:
  - Read-only database operations (BEGIN READ ONLY / ROLLBACK).
  - EXPLAIN only (zero ANALYZE, zero execution).
  - No DDL, no mutation.
  - Separate outputs under results/planner_sensitivity/phase4f1_validation/

Outputs:
  1. results/planner_sensitivity/phase4f1_validation/exact_mode_cost_validation.jsonl (486 records)
  2. results/planner_sensitivity/phase4f1_validation/seq_cost_formula_validation.csv (486 rows)
"""

import os
import sys
import csv
import json
import time
import hashlib
import argparse
from datetime import datetime, timezone
from collections import defaultdict

import psycopg
from psycopg import sql
from pgvector.psycopg import register_vector

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.config import get_db_connection_string
from scripts.run_phase4e3_scale_sweep import (
    SWEEP_SCALES,
    REPRESENTATIONS,
    PROFILE_IDS,
    PLANNER_COST_PROFILES,
    SCHEMA_NAME,
    FIXED_LIMIT,
    scale_db,
    capture_query_plan,
    extract_child_scan_costs,
)

OUTPUT_DIR = os.path.join(REPO_ROOT, "results", "planner_sensitivity", "phase4f1_validation")
RECOVERED_Q_VECTORS_PATH = os.path.join(
    REPO_ROOT, "results", "planner_sensitivity", "phase3_tie_sensitivity_20261031", "recovered_query_vectors.csv"
)
SCALE_SWEEP_SUMMARY_PATH = os.path.join(
    REPO_ROOT, "results", "planner_sensitivity", "scale_sweep_plan_only", "scale_sweep_summary.csv"
)

EXPECTED_Q0_SHA256 = "4a0428709013d77d8d284b369cb144734421bfdc4f6e4a83faf17db8114cf478"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Phase 4F.1.1 — Exact Seq Scan Candidate-Cost Full Validation Script (486 cells)"
    )
    parser.add_argument(
        "--output-dir",
        default=OUTPUT_DIR,
        help="Target output directory for validation artifacts (default: results/planner_sensitivity/phase4f1_validation)",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        default=False,
        help="Verify existing validation artifacts without re-executing PostgreSQL EXPLAIN queries.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)
    jsonl_path = os.path.join(output_dir, "exact_mode_cost_validation.jsonl")
    csv_path = os.path.join(output_dir, "seq_cost_formula_validation.csv")

    print("================================================================================")
    print("PHASE 4F.1.1 — EXACT SEQ SCAN COST VALIDATION (486 CELLS)")
    print(f"Target Output Directory: {output_dir}")
    print(f"Mode: {'Verify Existing Artifacts' if args.verify_only else 'Live Read-Only EXPLAIN Capture'}")
    print("================================================================================")

    if args.verify_only:
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Missing CSV validation artifact: {csv_path}")
        with open(csv_path, "r", encoding="utf-8") as cf:
            csv_rows = list(csv.DictReader(cf))
            for r in csv_rows:
                r["startup_cost_diff"] = float(r["startup_cost_diff"])
                r["total_cost_diff"] = float(r["total_cost_diff"])
                r["cost_match_le_0_01"] = (r["cost_match_le_0_01"] == "True")
                r["scale"] = int(r["scale"])
    else:
        # 1. Load and verify q0
        if not os.path.exists(RECOVERED_Q_VECTORS_PATH):
            raise FileNotFoundError(f"Missing recovered query vectors: {RECOVERED_Q_VECTORS_PATH}")

        q0_vec = None
        with open(RECOVERED_Q_VECTORS_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["query_id"] == "0":
                    actual_sha = row["sha256"]
                    if actual_sha != EXPECTED_Q0_SHA256:
                        raise ValueError(f"q0 SHA-256 mismatch: got {actual_sha}, expected {EXPECTED_Q0_SHA256}")
                    q0_vec = json.loads(row["serialized_vector"])
                    break

        if q0_vec is None or len(q0_vec) != 768:
            raise ValueError("Failed to load valid 768-dimensional q0 vector.")
        print(f"[VERIFIED] Canonical query q0 loaded successfully (SHA-256: {EXPECTED_Q0_SHA256})")

        # 2. Load Phase 4E.3 summary CSV for comparison
        with open(SCALE_SWEEP_SUMMARY_PATH, "r", encoding="utf-8") as f:
            summary_records = list(csv.DictReader(f))
        summary_lookup = {
            (int(r["scale"]), r["representation"], r["profile_id"]): r
            for r in summary_records
        }
        print(f"[LOADED] Phase 4E.3 summary baseline loaded ({len(summary_lookup)} cells)")

        # 3. Open persistent read-only connections to both databases
        connections = {}
        for db in ["compression_aware_rag_exp", "compression_aware_rag_scale"]:
            conn = psycopg.connect(get_db_connection_string(db), autocommit=True)
            register_vector(conn)
            with conn.cursor() as cur:
                cur.execute("SET default_transaction_read_only = on;")
            connections[db] = conn
        print("[CONNECTED] Read-only connections established to both target databases.")

        jsonl_records = []
        csv_rows = []

        t0_start = time.perf_counter()
        cell_idx = 0

        try:
            for sc in SWEEP_SCALES:
                db = scale_db(sc)
                conn = connections[db]

                for rep in REPRESENTATIONS:
                    tbl_name = f"chunks_{sc}_{rep}"
                    cast_type = "halfvec(768)" if "fp16" in rep else "vector(768)"

                    for prof_id in PROFILE_IDS:
                        cell_idx += 1
                        prof_params = PLANNER_COST_PROFILES[prof_id]

                        # Execute exact-mode EXPLAIN capture
                        plan_info = capture_query_plan(
                            conn=conn,
                            query_vector=q0_vec,
                            schema_name=SCHEMA_NAME,
                            table_name=tbl_name,
                            cast_type=cast_type,
                            profile_params=prof_params,
                            mode="exact",
                            top_k=FIXED_LIMIT,
                        )

                        scan_type = plan_info.get("scan_node_type")
                        if scan_type != "Seq Scan":
                            raise RuntimeError(
                                f"EXACT MODE FORCING FAILURE at N={sc}, {rep}, {prof_id}: "
                                f"expected 'Seq Scan', got '{scan_type}'!"
                            )

                        cost_breakdown = extract_child_scan_costs(plan_info["raw_plan"])
                        obs_startup = cost_breakdown["root_startup_cost"]
                        obs_total = cost_breakdown["root_total_cost"]

                        # Baseline reconstructed values from Phase 4E.3
                        base = summary_lookup[(sc, rep, prof_id)]
                        recon_startup = float(base["seqscan_sort_startup_cost"])
                        recon_total = float(base["seqscan_sort_total_cost"])

                        diff_startup = abs(obs_startup - recon_startup)
                        diff_total = abs(obs_total - recon_total)

                        status = "EXACT_MATCH" if (diff_startup <= 0.01 and diff_total <= 0.01) else "MISMATCH"

                        record = {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "scale": sc,
                            "database": db,
                            "representation": rep,
                            "profile_id": prof_id,
                            "mode": "exact",
                            "query_id": 0,
                            "selected_scan_node": scan_type,
                            "root_node_type": cost_breakdown["root_node_type"],
                            "child_node_type": cost_breakdown["child_node_type"],
                            "observed_limit_startup_cost": obs_startup,
                            "observed_limit_total_cost": obs_total,
                            "reconstructed_startup_cost": recon_startup,
                            "reconstructed_total_cost": recon_total,
                            "startup_cost_diff": round(diff_startup, 4),
                            "total_cost_diff": round(diff_total, 4),
                            "status": status,
                            "phase4e3_selected_plan_type": base["selected_plan_type"],
                            "settings": plan_info.get("settings"),
                            "raw_plan": plan_info.get("raw_plan"),
                        }
                        jsonl_records.append(record)

                        csv_rows.append({
                            "scale": sc,
                            "representation": rep,
                            "profile_id": prof_id,
                            "phase4e3_selected_plan_type": base["selected_plan_type"],
                            "observed_scan_node": scan_type,
                            "observed_limit_startup_cost": obs_startup,
                            "observed_limit_total_cost": obs_total,
                            "reconstructed_startup_cost": recon_startup,
                            "reconstructed_total_cost": recon_total,
                            "startup_cost_diff": round(diff_startup, 4),
                            "total_cost_diff": round(diff_total, 4),
                            "cost_match_le_0_01": (diff_startup <= 0.01 and diff_total <= 0.01),
                        })

        finally:
            for c in connections.values():
                c.close()

        elapsed = time.perf_counter() - t0_start
        print(f"[CAPTURED] 486 exact-mode plans captured in {elapsed:.2f}s.")

        # Write JSONL
        with open(jsonl_path, "w", encoding="utf-8") as jf:
            for rec in jsonl_records:
                jf.write(json.dumps(rec) + "\n")
        print(f"[EXPORTED] {len(jsonl_records)} records written to {jsonl_path}")

        # Write CSV
        with open(csv_path, "w", newline="", encoding="utf-8") as cf:
            writer = csv.DictWriter(cf, fieldnames=list(csv_rows[0].keys()))
            writer.writeheader()
            for r in csv_rows:
                writer.writerow(r)
        print(f"[EXPORTED] {len(csv_rows)} comparison rows written to {csv_path}")

    # Validation summary
    total_cells = len(csv_rows)
    matches = sum(1 for r in csv_rows if r["cost_match_le_0_01"])
    max_s_diff = max(r["startup_cost_diff"] for r in csv_rows)
    max_t_diff = max(r["total_cost_diff"] for r in csv_rows)

    hnsw_selected_cells = [r for r in csv_rows if r["phase4e3_selected_plan_type"] == "Index Scan"]
    seq_selected_cells = [r for r in csv_rows if r["phase4e3_selected_plan_type"] == "Seq Scan"]

    hnsw_matches = sum(1 for r in hnsw_selected_cells if r["cost_match_le_0_01"])
    seq_matches = sum(1 for r in seq_selected_cells if r["cost_match_le_0_01"])

    print("\n--- Validation Summary ---")
    print(f"Total cells validated: {total_cells} (expected: 486)")
    print(f"Exact cost matches (diff <= 0.01): {matches} / {total_cells}")
    print(f"Max startup cost diff: {max_s_diff:.4f}")
    print(f"Max total cost diff:   {max_t_diff:.4f}")
    print(f"HNSW-selected cells (reconstructed SeqScan cost): {hnsw_matches} / {len(hnsw_selected_cells)} matches")
    print(f"Seq Scan-selected cells (directly observed):     {seq_matches} / {len(seq_selected_cells)} matches")

    # Specific check for N=850, FP32 Plain, P6
    p6_850 = next(r for r in csv_rows if r["scale"] == 850 and r["representation"] == "fp32_plain" and r["profile_id"] == "P6")
    print(f"\nTarget Cell (N=850, fp32_plain, P6):")
    print(f"  Observed:      Startup={p6_850['observed_limit_startup_cost']}, Total={p6_850['observed_limit_total_cost']}")
    print(f"  Reconstructed: Startup={p6_850['reconstructed_startup_cost']}, Total={p6_850['reconstructed_total_cost']}")
    print(f"  Difference:    Startup={p6_850['startup_cost_diff']}, Total={p6_850['total_cost_diff']}")
    print(f"  Matches <= 0.01: {p6_850['cost_match_le_0_01']}")


if __name__ == "__main__":
    main()

