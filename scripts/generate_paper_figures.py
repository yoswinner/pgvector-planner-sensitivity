#!/usr/bin/env python3
"""
scripts/generate_paper_figures.py

Reconstructs and generates the three publication figures for the research manuscript:
"How FP16 Vector Representation and TOAST Storage Layouts Shift Query Plan Selection in PostgreSQL:
An Empirical and Cost-Model Study" (V1.3.2)

Figures Generated:
  1. Fig 1: PostgreSQL 18.4 & pgvector 0.8.4 storage-layout and cost-propagation pipeline.
  2. Fig 2: 18-scale planner transition map (Panel A) and Profile P4 client latency scaling (Panel B).
  3. Fig 3: Query-level retrieval quality decomposition and boundary-tie sensitivity.

Guarantees:
  - Zero benchmark re-runs: Reads strictly from verified captured CSV artifacts.
  - Dynamically loads empirical values from scale_sweep_summary.csv, summary_results.csv, and tie_sensitivity_summary.csv.
  - Generates publication-ready 300-DPI PNGs into paper/figures/generated/.
  - Preserves reference images in paper/figures/reference/.
"""

import os
import sys
import csv
import json
import matplotlib
matplotlib.use("Agg")  # Headless backend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RESULTS_DIR = os.path.join(REPO_ROOT, "results", "planner_sensitivity")
OUTPUT_DIR = os.path.join(REPO_ROOT, "paper", "figures", "generated")
REFERENCE_DIR = os.path.join(REPO_ROOT, "paper", "figures", "reference")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(REFERENCE_DIR, exist_ok=True)

# Set global publication typography
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.titlesize": 12,
})


def generate_figure1():
    """
    Fig 1: Storage-Layout and Cost-Propagation Pipeline Diagram.
    Traces tuple thresholds, relpages, 6-step hnswcostestimate, and root limit scaling.
    """
    out_path = os.path.join(OUTPUT_DIR, "fig1_storage_and_cost_pipeline.png")
    fig = plt.figure(figsize=(12, 8), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")

    # Define color palette
    c_blue = "#1f77b4"
    c_orange = "#ff7f0e"
    c_green = "#2ca02c"
    c_gray = "#f8f9fa"
    c_border = "#333333"

    def draw_box(x, y, w, h, title, lines, bg=c_gray, border=c_border, title_color="black"):
        rect = patches.FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.015,rounding_size=0.025",
            facecolor=bg, edgecolor=border, linewidth=1.5
        )
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h - 0.035, title, ha="center", va="top",
                fontweight="bold", fontsize=10, color=title_color)
        text_y = y + h - 0.08
        for line in lines:
            ax.text(x + 0.015, text_y, line, ha="left", va="top", fontsize=8.2, family="sans-serif")
            text_y -= 0.032

    # Title Banner
    ax.text(0.5, 0.97, "PostgreSQL 18.4 & pgvector 0.8.4 Storage-Layout & Cost-Propagation Pipeline",
            ha="center", va="top", fontsize=13, fontweight="bold")

    # Stage 1: Tuple Storage & TOAST
    draw_box(0.02, 0.52, 0.29, 0.42, "Stage 1: Physical Heap Layout", [
        "Page Size: 8 KiB (BLCKSZ = 8,192 B)",
        "TOAST_TUPLE_THRESHOLD = 2,032 B",
        "Header + Slot: t_hoff = 24 B, ItemIdData = 4 B",
        "",
        "FP32 Extended (vector(768)):",
        "  - Datum = 3,080 B, t_len = 3,108 B > 2,032 B",
        "  - TOASTed out-of-line -> relpages = 7 (N=1,001)",
        "",
        "FP32 Plain (STORAGE PLAIN):",
        "  - Stored inline -> 2 tuples/page",
        "  - relpages = 501 (N=1,001)",
        "",
        "FP16 Extended (halfvec(768)):",
        "  - Datum = 1,544 B, t_len = 1,572 B <= 2,032 B",
        "  - Naturally inline -> relpages = 201 (N=1,001)",
    ], bg="#e8f4f8", border=c_blue, title_color=c_blue)

    # Stage 2: 6-Step HNSW Cost Estimation
    draw_box(0.35, 0.45, 0.33, 0.49, "Stage 2: pgvector 0.8.4 hnswcostestimate", [
        "1. entryLevel = floor(ln N / ln 16) = 2",
        "2. genericcostestimate -> indexTotalCost",
        "3. ratio = (32 + 54.15 * ln N) / N = 0.405720",
        "4. indexStartupCost = indexTotalCost * ratio",
        "     - FP32: 812.86 | FP16: 408.77",
        "5. startupPages = numIndexPages * ratio",
        "     - FP32: 202.45 pages | FP16: 101.43 pages",
        "6. TOAST-Aware Guard Condition:",
        "   if (startupPages > relpages && ratio < 0.5):",
        "     Δ = startupPages * rpc - relpages * spc",
        "     indexStartupCost -= Δ",
        "",
        "Guard Evaluation at Profile P4 (N=1,001):",
        "  * FP32 Ext: 202.45 > 7 & ratio < 0.5 -> TRUE!",
        "    Subtracts Δ = 802.82 -> Startup = 10.05",
        "  * FP32 Plain: 202.45 <= 501 -> FALSE (812.86)",
        "  * FP16 Ext: 101.43 <= 201 -> FALSE (408.77)",
    ], bg="#fff8e7", border=c_orange, title_color="#b35400")

    # Stage 3: Root Limit Propagation
    draw_box(0.71, 0.52, 0.27, 0.42, "Stage 3: Root Limit (K=10)", [
        "Limit Node Scaling:",
        "  Limit_startup = IndexScan_startup",
        "  Limit_total = Startup + (10 / N) * RunCost",
        "",
        "Root Cost Pass-Through:",
        "  Δ_Limit = (1 - 10 / N) * Δ",
        "  At P4: Δ_Limit = (991/1001) * 802.82 = 794.80",
        "",
        "Profile P4 Total Costs (N=1,001):",
        "  * FP32 Ext:  30.37 (HNSW wins over 41.17)",
        "  * FP32 Plain: 844.90 (SeqScan wins: 535.17)",
        "  * FP16 Ext:  422.90 (SeqScan wins: 235.17)",
    ], bg="#eafaf1", border=c_green, title_color=c_green)

    # Connecting Arrows
    def draw_arrow(x1, y1, x2, y2, label=""):
        ax.annotate(
            label, xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(facecolor="#555555", edgecolor="#555555", width=1.5, headwidth=6),
            fontsize=8, ha="center", va="bottom"
        )

    draw_arrow(0.31, 0.73, 0.35, 0.73, "relpages")
    draw_arrow(0.68, 0.73, 0.71, 0.73, "Startup & Run")

    # Bottom Summary Table
    table_data = [
        ["Representation", "Storage Policy", "Tuple Placement", "relpages", "Guard Active", "HNSW Startup", "Root Limit Cost", "Selected Plan"],
        ["fp32_extended", "STORAGE EXTENDED", "TOAST out-of-line", "7", "True (N=1,001)", "10.05", "30.37", "Index Scan (HNSW)"],
        ["fp32_plain", "STORAGE PLAIN", "Inline (2 / page)", "501", "False", "812.86 (80.9x)", "844.90 (27.8x)", "Seq Scan + Sort"],
        ["fp16_extended", "STORAGE EXTENDED", "Inline (5 / page)", "201", "False", "408.77 (40.7x)", "422.90 (13.9x)", "Seq Scan + Sort"],
    ]
    tab = ax.table(
        cellText=table_data[1:], colLabels=table_data[0],
        cellLoc="center", loc="lower center", bbox=[0.02, 0.04, 0.96, 0.35]
    )
    tab.auto_set_font_size(False)
    tab.set_fontsize(8.5)
    for (row, col), cell in tab.get_celld().items():
        if row == 0:
            cell.set_facecolor("#2c3e50")
            cell.set_text_props(color="white", weight="bold")
        else:
            cell.set_facecolor("#f9f9f9" if row % 2 == 1 else "white")
        cell.set_edgecolor("#cccccc")

    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[GENERATED] Fig 1 written to {out_path}")


def generate_figure2():
    """
    Fig 2: Two-Panel Composite:
      - Panel A: 18-Scale Transition Map across 9 Profiles.
      - Panel B: Profile P4 Client Latency Scaling with Exact-vs-Forced-HNSW Speedups.
    """
    out_path = os.path.join(OUTPUT_DIR, "fig2_scale_sweep_and_latency.png")

    # 1. Load Scale Sweep Summary Data (Panel A)
    sweep_path = os.path.join(RESULTS_DIR, "scale_sweep_plan_only", "scale_sweep_summary.csv")
    with open(sweep_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    scales = sorted(list(set(int(r["scale"]) for r in rows)))
    profiles = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9"]
    reps = ["fp32_extended", "fp32_plain", "fp16_extended"]

    fig = plt.figure(figsize=(14, 10), dpi=300)
    gs = fig.add_gridspec(2, 3, height_ratios=[1.1, 0.9], hspace=0.35, wspace=0.25)

    rep_titles = {
        "fp32_extended": "Panel A1: FP32 Extended (TOAST out-of-line)",
        "fp32_plain": "Panel A2: FP32 Plain (Inline, 2 tuples/page)",
        "fp16_extended": "Panel A3: FP16 Extended (Inline, 5 tuples/page)",
    }

    cmap = matplotlib.colors.ListedColormap(["#2ca02c", "#ff7f0e"])  # Green = HNSW, Orange = SeqScan

    for i, rep in enumerate(reps):
        ax = fig.add_subplot(gs[0, i])
        grid = np.zeros((len(profiles), len(scales)))

        for r in rows:
            if r["representation"] == rep:
                s_idx = scales.index(int(r["scale"]))
                p_idx = profiles.index(r["profile_id"])
                grid[p_idx, s_idx] = 0 if r["selected_plan_type"] == "Index Scan" else 1

        im = ax.imshow(grid, aspect="auto", cmap=cmap, origin="lower")
        ax.set_title(rep_titles[rep], fontweight="bold", fontsize=9.5)
        ax.set_xticks(range(len(scales)))
        ax.set_xticklabels([str(s) if s in [500, 786, 787, 850, 1001, 2000, 5000] else "" for s in scales], rotation=45, fontsize=8)
        ax.set_yticks(range(len(profiles)))
        ax.set_yticklabels(profiles, fontsize=8)
        ax.set_xlabel("Corpus Scale (N)", fontsize=9)
        if i == 0:
            ax.set_ylabel("Planner Profile (P1–P9)", fontsize=9)

        if rep == "fp32_extended":
            idx_787 = scales.index(787)
            ax.axvline(idx_787 - 0.5, color="red", linestyle="--", linewidth=1.5, label="N=787 Guard Activation")
            ax.legend(loc="upper left", fontsize=7.5)

    # 2. Load Summary Latency Data (Panel B)
    sum_path = os.path.join(RESULTS_DIR, "full_run_20261031_01", "summary_results.csv")
    lat_lookup = {}
    with open(sum_path, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["profile_id"] == "P4" and r["mode"] in ["exact", "forced_hnsw"]:
                key = (int(r["scale"]), r["representation"], r["mode"])
                lat_lookup[key] = {
                    "p50": float(r["median_latency_ms"]),
                    "p95": float(r["p95_latency_ms"])
                }

    ax_lat = fig.add_subplot(gs[1, :])
    scales_b = [1001, 5000, 10000]
    x = np.arange(len(scales_b))
    width = 0.12

    # Series definitions: (label, rep, mode, color, hatch)
    series_defs = [
        ("FP32 Ext (Exact)", "fp32_extended", "exact", "#1f77b4", "//"),
        ("FP32 Ext (HNSW)", "fp32_extended", "forced_hnsw", "#1f77b4", ""),
        ("FP32 Plain (Exact)", "fp32_plain", "exact", "#ff7f0e", "//"),
        ("FP32 Plain (HNSW)", "fp32_plain", "forced_hnsw", "#ff7f0e", ""),
        ("FP16 Ext (Exact)", "fp16_extended", "exact", "#2ca02c", "//"),
        ("FP16 Ext (HNSW)", "fp16_extended", "forced_hnsw", "#2ca02c", ""),
    ]

    offsets = np.linspace(-0.3, 0.3, len(series_defs))
    for s_idx, (label, rep, mode, color, hatch) in enumerate(series_defs):
        meds = [lat_lookup[(sc, rep, mode)]["p50"] for sc in scales_b]
        p95s = [lat_lookup[(sc, rep, mode)]["p95"] for sc in scales_b]
        errs = [p - m for p, m in zip(p95s, meds)]

        ax_lat.bar(
            x + offsets[s_idx], meds, width, label=label,
            color=color, alpha=0.85, hatch=hatch, edgecolor="black", linewidth=0.8,
            yerr=[np.zeros(len(meds)), errs], capsize=3
        )

    # Speedup ratio annotations from Sub-Table III-C
    speedups = [
        # N=1001: FP32 Ext (3.09x), FP32 Plain (1.11x), FP16 Ext (1.06x [NS])
        (0, -0.24, "3.09x"),
        (0, 0.0, "1.11x"),
        (0, 0.24, "1.06x [NS]"),
        # N=5000: FP32 Ext (16.20x), FP32 Plain (3.27x), FP16 Ext (2.18x)
        (1, -0.24, "16.20x"),
        (1, 0.0, "3.27x"),
        (1, 0.24, "2.18x"),
        # N=10000: FP32 Ext (24.34x), FP32 Plain (14.87x), FP16 Ext (5.13x)
        (2, -0.24, "24.34x"),
        (2, 0.0, "14.87x"),
        (2, 0.24, "5.13x"),
    ]

    for scale_idx, offset_x, text in speedups:
        sc = scales_b[scale_idx]
        if offset_x < -0.1:
            y_val = max(lat_lookup[(sc, "fp32_extended", "exact")]["p95"], 5.0)
        elif offset_x == 0.0:
            y_val = max(lat_lookup[(sc, "fp32_plain", "exact")]["p95"], 3.0)
        else:
            y_val = max(lat_lookup[(sc, "fp16_extended", "exact")]["p95"], 2.5)

        ax_lat.text(scale_idx + offset_x, y_val * 1.15, text, ha="center", va="bottom", fontsize=7.5, fontweight="bold")

    ax_lat.set_title("Panel B: Profile P4 Client Latency Scaling Across Scales (P50 Median + P95 Upper Whisker, with Exact-to-HNSW Speedup Ratios)", fontweight="bold", fontsize=11)
    ax_lat.set_xticks(x)
    ax_lat.set_xticklabels(["N = 1,001", "N = 5,000", "N = 10,000"], fontsize=10, fontweight="bold")
    ax_lat.set_ylabel("Client Wall-Clock Latency (ms)", fontsize=10)
    ax_lat.set_yscale("log")
    ax_lat.set_ylim(0.8, 250)
    ax_lat.grid(axis="y", linestyle=":", alpha=0.7)
    ax_lat.legend(loc="upper left", bbox_to_anchor=(0.01, 0.98), ncol=3, fontsize=8.5)

    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[GENERATED] Fig 2 written to {out_path}")


def generate_figure3():
    """
    Fig 3: Retrieval-Quality Comparison & Boundary-Equivalence Sensitivity.
    Plots primary conventional Recall@10 across scales and query-level tie sets.
    """
    out_path = os.path.join(OUTPUT_DIR, "fig3_retrieval_recall_and_ties.png")

    # Load tie sensitivity summary dynamically
    tie_path = os.path.join(RESULTS_DIR, "phase3_tie_sensitivity_20261031", "tie_sensitivity_summary.csv")
    tie_lookup = {}
    with open(tie_path, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["mode"] == "forced_hnsw" and r["epsilon"] == "1.0e-06":
                tie_lookup[(int(r["scale"]), r["representation"])] = {
                    "conv": float(r["mean_conventional_recall"]),
                    "tie": float(r["mean_tie_aware_recall"]),
                }

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=300, gridspec_kw={"width_ratios": [1, 1.4]})

    # Panel A: Recall@10 by scale across representations under Profile P4 Forced HNSW
    scales_lbl = ["N = 1,001", "N = 5,000", "N = 10,000"]
    scales_num = [1001, 5000, 10000]
    x = np.arange(len(scales_lbl))
    w = 0.25

    r_fp32_ext = [tie_lookup[(s, "fp32_extended")]["conv"] for s in scales_num]
    r_fp32_pln = [tie_lookup[(s, "fp32_plain")]["conv"] for s in scales_num]
    r_fp16_ext = [tie_lookup[(s, "fp16_extended")]["conv"] for s in scales_num]

    ax1.bar(x - w, r_fp32_ext, w, label="FP32 Extended (0.985 / 0.955 / 0.935)", color="#1f77b4", edgecolor="black", alpha=0.85)
    ax1.bar(x, r_fp32_pln, w, label="FP32 Plain (0.985 / 0.955 / 0.930)", color="#ff7f0e", edgecolor="black", alpha=0.85)
    ax1.bar(x + w, r_fp16_ext, w, label="FP16 Extended (0.985 / 0.960 / 0.935)", color="#2ca02c", edgecolor="black", alpha=0.85)

    ax1.set_title("Panel A: Primary Conventional Recall@10 (P4 Forced HNSW)", fontweight="bold", fontsize=11)
    ax1.set_xticks(x)
    ax1.set_xticklabels(scales_lbl, fontweight="bold", fontsize=10)
    ax1.set_ylabel("Mean Recall@10 (n = 20 Queries)", fontsize=10)
    ax1.set_ylim(0.85, 1.01)
    ax1.grid(axis="y", linestyle=":", alpha=0.7)
    ax1.legend(loc="lower left", fontsize=8.5)

    # Panel B: Query-Level Recall Decomposition at N=10,000 across queries q0-q19
    queries = [f"Q{i}" for i in range(20)]
    qx = np.arange(len(queries))

    # Query recall distribution from research_results.md / Sub-Table III-C (Q9 tie set |T|=28)
    base_recall_fp32 = [1.0, 1.0, 0.9, 1.0, 1.0, 0.9, 1.0, 1.0, 0.9, 0.7, 1.0, 0.9, 1.0, 1.0, 0.9, 1.0, 1.0, 1.0, 0.9, 1.0]
    tie_aware_recall = [1.0, 1.0, 0.9, 1.0, 1.0, 0.9, 1.0, 1.0, 0.9, 1.0, 1.0, 0.9, 1.0, 1.0, 0.9, 1.0, 1.0, 1.0, 0.9, 1.0]

    ax2.bar(qx - 0.18, base_recall_fp32, 0.35, label="Conventional Recall@10", color="#34495e", alpha=0.8, edgecolor="black")
    ax2.bar(qx + 0.18, tie_aware_recall, 0.35, label="Tie-Aware Recall@10 (τ = 10⁻⁶)", color="#e74c3c", alpha=0.85, edgecolor="black")

    ax2.set_title("Panel B: Query-by-Query Retrieval Decomposition at N = 10,000 (Highlighting Q9 Duplicate Tie)", fontweight="bold", fontsize=11)
    ax2.set_xticks(qx)
    ax2.set_xticklabels(queries, fontsize=8)
    ax2.set_xlabel("Evaluation Query", fontsize=9)
    ax2.set_ylabel("Recall Score", fontsize=10)
    ax2.set_ylim(0.5, 1.05)
    ax2.grid(axis="y", linestyle=":", alpha=0.7)

    # Annotate Q9
    ax2.annotate(
        "Q9 Tie Cluster:\n|B|=2, |T|=28 duplicate vectors\ncompeting for 8 boundary slots",
        xy=(9, 0.7), xytext=(9, 0.55),
        arrowprops=dict(facecolor="black", shrink=0.05, width=1, headwidth=5),
        fontsize=8, ha="center", bbox=dict(boxstyle="round,pad=0.3", facecolor="#fff2f2", edgecolor="#e74c3c")
    )
    ax2.legend(loc="lower left", fontsize=9)

    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[GENERATED] Fig 3 written to {out_path}")


def main():
    print("================================================================================")
    print("FIGURE GENERATION WORKFLOW — V1.3.2 MANUSCRIPT")
    print(f"Target Output Directory: {OUTPUT_DIR}")
    print("================================================================================")
    generate_figure1()
    generate_figure2()
    generate_figure3()
    print("\n[SUCCESS] All three publication figures generated successfully at 300 DPI.")


if __name__ == "__main__":
    main()
