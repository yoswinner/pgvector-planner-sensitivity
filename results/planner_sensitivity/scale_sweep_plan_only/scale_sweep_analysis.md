# Phase 4E.3 — 18-Scale Plan-Only Sweep Numerical and Boundary Analysis

## 1. Executive Summary & Execution Metrics

- **Total Primary `EXPLAIN (SETTINGS, FORMAT JSON)` Captures:** `972` (`18` scales $\times$ `3` representations $\times$ `9` cost profiles $\times$ `2` plan modes $\times$ `1` canonical query `q0`).
- **Total Summary Cells:** `486` (`18` scales $\times$ `3` representations $\times$ `9` cost profiles).
- **Total Storage/Catalog Configurations:** `54` (`18` scales $\times$ `3` representations).
- **Runtime Provenance & Timing Breakdown:**
  - **Individual Recorded Phase Durations:** Table Provisioning = `5.75 s`; HNSW Index Construction + `ANALYZE` = `31.67 s`; Read-Only `EXPLAIN` Capture (`972` plans) = `5.06 s`.
  - **Sum of Recorded Phase Durations:** `42.48 s` (arithmetic sum of discrete phase timers, not an independently verified continuous end-to-end wall-clock time).
  - **Overall Workflow Timestamps:** Started at `2026-10-31T16:25:08.139125+00:00`, completed at `2026-10-31T16:35:30.225581+00:00` (elapsed workflow span = `622.09 s`, encompassing initial execution, tiebreak diagnosis, validation suite, and finalization).
  - **Artifact-Finalization Timestamps:** Started at `2026-10-31T16:35:28.139125+00:00`, completed at `2026-10-31T16:35:30.225581+00:00` (elapsed = `2.09 s`).
  - **End-to-End Wall-Clock Duration:** Marked as `unavailable` (`null`) due to multi-stage diagnostic workflow. See `timing_provenance_note.md` for full semantics.
- **Closed-Form `Seq Scan + Top-k Sort` Validation:** Verified across `54/54` existing `exact`-mode captures at $N=1{,}001$ and $N=5{,}000$ with `max_startup_cost_diff = 0.0000` and `max_total_cost_diff = 0.0000`.

---

## 2. Boundary A — HNSW Traversal-Ratio (`ratio < 0.5`) Threshold Verification

In `pgvector` 0.8.4 (`src/hnsw.c`), for $256 \le N < 4{{,}}096$ ($\text{entryLevel} = \lfloor \ln N / \ln 16 \rfloor = 2$, $m = 16$, $ef_{\text{search}} = 40$):
$$\text{ratio}(N) = \frac{32 + 54.152441134 \ln N}{N}$$

| Scale $N$ | `entryLevel` | Visited Index Tuples ($N \cdot \text{ratio}$) | $\text{ratio}(N)$ | `ratio < 0.5` | `fp32_extended` `P4` HNSW Startup Cost | `fp32_extended` `P4` HNSW Limit Total Cost | `fp32_extended` `P4` Selected Plan |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `500` | `2` | `368.5360` | `0.737072` | **`False`** | `742.78` | `748.53` | **`Seq Scan`** |
| `700` | `2` | `386.7570` | `0.552510` | **`False`** | `774.20` | `783.57` | **`Seq Scan`** |
| `750` | `2` | `390.4928` | `0.520657` | **`False`** | `781.83` | `791.82` | **`Seq Scan`** |
| `780` | `2` | `392.6169` | `0.503355` | **`False`** | `786.17` | `796.49` | **`Seq Scan`** |
| `785` | `2` | `392.9631` | `0.500590` | **`False`** | `787.87` | `798.27` | **`Seq Scan`** |
| `786` | `2` | `393.0322` | `0.500041` | **`False`** | `787.01` | `797.45` | **`Seq Scan`** |
| `787` | `2` | `393.1010` | `0.499493` | **`True`** | `8.95` | `29.31` | **`Index Scan`** |
| `788` | `2` | `393.1694` | `0.498946` | **`True`** | `8.95` | `29.29` | **`Index Scan`** |
| `790` | `2` | `393.3070` | `0.497857` | **`True`** | `8.95` | `29.29` | **`Index Scan`** |
| `850` | `2` | `397.2713` | `0.467378` | **`True`** | `8.98` | `29.31` | **`Index Scan`** |
| `1001` | `2` | `406.1257` | `0.405720` | **`True`** | `10.05` | `30.37` | **`Index Scan`** |

- **Verified Lower Threshold:**
  - At $N = 786$: $\text{ratio}(786) = 0.500041 \ge 0.50$ (`ratio < 0.5` is **`False`**). At Profile `P4`, `fp32_extended` HNSW startup cost is unadjusted (`787.01`, root `Limit` total cost `797.45` vs. `Seq Scan + Sort` `32.84`), forcing `Seq Scan` across `8/9` profiles (`P1, P2, P4–P9`).
  - At $N = 787$: $\text{ratio}(787) = 0.499493 < 0.50$ (`ratio < 0.5` is **`True`**). At Profile `P4`, `fp32_extended` HNSW startup cost undergoes a **`88.06×`** same-scale adjustment reduction (same-scale unadjusted `788.15` vs. adjusted **`8.95`**; $788.15 / 8.95 \approx 88.06\times$) and a **`87.93×`** cross-scale reduction relative to $N=786$ (previous-scale `787.01` at $N=786$ vs. adjusted **`8.95`** at $N=787$; $787.01 / 8.95 \approx 87.93\times$). Root `Limit` total cost drops from `797.45` to **`29.31`** (below `Seq Scan + Sort` `32.87`), switching `7/9` profiles (`P1, P2, P4, P5, P6, P8, P9`) from `Seq Scan` to `Index Scan` in a single 1-row step.

---

## 3. Boundary B — Complete TOAST Cost-Adjustment Guard Regions (`startupPages > relpages && ratio < 0.5`)

| Scale $N$ | $\text{ratio}(N)$ | `ratio < 0.5` | `fp32_extended` (`relpages` / `idx_pages` / `startupPages` / **Guard**) | `fp32_plain` (`relpages` / `idx_pages` / `startupPages` / **Guard**) | `fp16_extended` (`relpages` / `idx_pages` / `startupPages` / **Guard**) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| `500` | `0.737072` | `False` | `4` / `251` / `185.01` / **`False`** | `250` / `251` / `185.01` / **`False`** | `100` / `126` / `92.87` / **`False`** |
| `700` | `0.552510` | `False` | `5` / `349` / `192.83` / **`False`** | `350` / `349` / `192.83` / **`False`** | `140` / `175` / `96.69` / **`False`** |
| `750` | `0.520657` | `False` | `5` / `374` / `194.73` / **`False`** | `375` / `374` / `194.73` / **`False`** | `150` / `188` / `97.88` / **`False`** |
| `780` | `0.503355` | `False` | `5` / `389` / `195.81` / **`False`** | `390` / `389` / `195.81` / **`False`** | `156` / `195` / `98.15` / **`False`** |
| `785` | `0.500590` | `False` | `5` / `392` / `196.23` / **`False`** | `393` / `392` / `196.23` / **`False`** | `157` / `197` / `98.62` / **`False`** |
| `786` | `0.500041` | `False` | `6` / `392` / `196.02` / **`False`** | `393` / `392` / `196.02` / **`False`** | `158` / `197` / `98.51` / **`False`** |
| `787` | `0.499493` | `True` | `6` / `393` / `196.30` / **`True`** | `394` / `393` / `196.30` / **`False`** | `158` / `197` / `98.40` / **`False`** |
| `788` | `0.498946` | `True` | `6` / `393` / `196.09` / **`True`** | `394` / `393` / `196.09` / **`False`** | `158` / `197` / `98.29` / **`False`** |
| `790` | `0.497857` | `True` | `6` / `394` / `196.16` / **`True`** | `395` / `394` / `196.16` / **`False`** | `158` / `198` / `98.58` / **`False`** |
| `850` | `0.467378` | `True` | `6` / `424` / `198.17` / **`True`** | `425` / `424` / `198.17` / **`False`** | `170` / `213` / `99.55` / **`False`** |
| `1001` | `0.405720` | `True` | `7` / `499` / `202.45` / **`True`** | `501` / `499` / `202.45` / **`False`** | `201` / `250` / `101.43` / **`False`** |
| `1250` | `0.334524` | `True` | `8` / `623` / `208.41` / **`True`** | `625` / `623` / `208.41` / **`False`** | `250` / `312` / `104.37` / **`False`** |
| `1500` | `0.285352` | `True` | `10` / `748` / `213.44` / **`True`** | `750` / `748` / `213.44` / **`False`** | `300` / `375` / `107.01` / **`False`** |
| `1750` | `0.249358` | `True` | `12` / `873` / `217.69` / **`True`** | `875` / `873` / `217.69` / **`False`** | `350` / `437` / `108.97` / **`False`** |
| `2000` | `0.221804` | `True` | `13` / `998` / `221.36` / **`True`** | `1000` / `998` / `221.36` / **`False`** | `400` / `500` / `110.90` / **`False`** |
| `3000` | `0.155188` | `True` | `20` / `1498` / `232.47` / **`True`** | `1500` / `1498` / `232.47` / **`False`** | `600` / `750` / `116.39` / **`False`** |
| `4000` | `0.120286` | `True` | `26` / `1995` / `239.97` / **`True`** | `2000` / `1995` / `239.97` / **`False`** | `800` / `998` / `120.05` / **`False`** |
| `5000` | `0.101845` | `True` | `32` / `2493` / `253.90` / **`True`** | `2500` / `2494` / `254.00` / **`False`** | `1000` / `1247` / `127.00` / **`False`** |

### Guard Activation Regions by Representation
1. **`fp32_extended` (`vector(768)`, `STORAGE EXTENDED`):**
   - `startupPages > relpages` holds at **all 18 scales** ($N \in [500, 5{{,}}000]$) because out-of-line TOAST storage keeps main-heap `relpages` at `4`–`32` pages while `startupPages` is `185.01`–`253.90` pages.
   - However, because `ratio < 0.5` is `False` for $N \le 786$, the complete guard (`startupPages > relpages && ratio < 0.5`) is **`False` for $N \in [500, 786]$ (`6/18` scales)** and **`True` for all $N \in [787, 5{{,}}000]$ (`12/18` scales)**.
2. **`fp32_plain` (`vector(768)`, `STORAGE PLAIN`):**
   - For $N \le 786$, `ratio < 0.5` is `False`; for $N \ge 787$, `startupPages` (`196.30`–`254.00`) is strictly less than inline `relpages` (`394`–`2,500`).
   - Complete guard region: **`False` at all `18/18` scales (`0/162` profile-scale cells)**.
3. **`fp16_extended` (`halfvec(768)`, `STORAGE EXTENDED`):**
   - For $N \le 786$, `ratio < 0.5` is `False`; for $N \ge 787$, `startupPages` (`98.40`–`127.00`) is strictly less than inline `relpages` (`158`–`1,000`).
   - Complete guard region: **`False` at all `18/18` scales (`0/162` profile-scale cells)**.

---

## 4. Boundary C — Actual Planner Crossover Intervals (`Seq Scan + Sort` $\to$ `HNSW Index Scan`)

| Representation | Profile | `(random_page_cost, cpu_operator_cost)` | `Seq Scan` Scales | `HNSW` Scales | Monotonic? | Observed Transition Interval $[N_{\text{Seq}}, N_{\text{HNSW}}]$ | Interval Width | Phase 4E.2 Analytical Estimate | Cost Comparison at Transition Boundary |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `fp32_extended` | `P1` | `(1.0, 0.0025)` | `6/18` | `12/18` | `Yes` | **`[786, 787]`** | `1` | `787 (guard boundary)` | @786: HNSW `201.70` vs Seq `32.84` ($\to$) @787: HNSW `14.10` vs Seq `32.87` |
| `fp32_extended` | `P2` | `(1.0, 0.01)` | `6/18` | `12/18` | `Yes` | **`[786, 787]`** | `1` | `787 (guard boundary)` | @786: HNSW `204.76` vs Seq `89.76` ($\to$) @787: HNSW `17.17` vs Seq `89.87` |
| `fp32_extended` | `P3` | `(1.0, 0.05)` | `0/18` | `18/18` | `Yes` | Always `HNSW` ($N \le 500$) | `0` | `HNSW for N>=787 (<500 unadjusted)` | @500: HNSW `207.42` < Seq `250.60` |
| `fp32_extended` | `P4` | `(4.0, 0.0025)` | `6/18` | `12/18` | `Yes` | **`[786, 787]`** | `1` | `787 (guard boundary)` | @786: HNSW `797.45` vs Seq `32.84` ($\to$) @787: HNSW `29.31` vs Seq `32.87` |
| `fp32_extended` | `P5` | `(4.0, 0.01)` | `6/18` | `12/18` | `Yes` | **`[786, 787]`** | `1` | `787 (guard boundary)` | @786: HNSW `800.51` vs Seq `89.76` ($\to$) @787: HNSW `32.37` vs Seq `89.87` |
| `fp32_extended` | `P6` | `(4.0, 0.05)` | `6/18` | `12/18` | `Yes` | **`[786, 787]`** | `1` | `787 (guard boundary)` | @786: HNSW `816.83` vs Seq `393.36` ($\to$) @787: HNSW `48.70` vs Seq `393.86` |
| `fp32_extended` | `P7` | `(8.0, 0.0025)` | `12/18` | `6/18` | `Yes` | **`[1250, 1500]`** | `250` | `~1,120` | @1250: HNSW `51.63` vs Seq `50.66` ($\to$) @1500: HNSW `53.75` vs Seq `61.19` |
| `fp32_extended` | `P8` | `(8.0, 0.01)` | `6/18` | `12/18` | `Yes` | **`[786, 787]`** | `1` | `787 (guard boundary)` | @786: HNSW `1594.86` vs Seq `89.76` ($\to$) @787: HNSW `52.65` vs Seq `89.87` |
| `fp32_extended` | `P9` | `(8.0, 0.05)` | `6/18` | `12/18` | `Yes` | **`[786, 787]`** | `1` | `787 (guard boundary)` | @786: HNSW `1611.18` vs Seq `393.36` ($\to$) @787: HNSW `68.98` vs Seq `393.86` |
| `fp32_plain` | `P1` | `(1.0, 0.0025)` | `0/18` | `18/18` | `Yes` | Always `HNSW` ($N \le 500$) | `0` | `< 400 (HNSW all)` | @500: HNSW `194.23` < Seq `267.08` |
| `fp32_plain` | `P2` | `(1.0, 0.01)` | `0/18` | `18/18` | `Yes` | Always `HNSW` ($N \le 500$) | `0` | `< 400 (HNSW all)` | @500: HNSW `197.09` < Seq `303.32` |
| `fp32_plain` | `P3` | `(1.0, 0.05)` | `0/18` | `18/18` | `Yes` | Always `HNSW` ($N \le 500$) | `0` | `< 400 (HNSW all)` | @500: HNSW `212.34` < Seq `496.60` |
| `fp32_plain` | `P4` | `(4.0, 0.0025)` | `13/18` | `5/18` | `Yes` | **`[1500, 1750]`** | `250` | `~1,555` | @1500: HNSW `891.42` vs Seq `801.19` ($\to$) @1750: HNSW `909.19` vs Seq `934.72` |
| `fp32_plain` | `P5` | `(4.0, 0.01)` | `12/18` | `6/18` | `Yes` | **`[1250, 1500]`** | `250` | `~1,410` | @1250: HNSW `873.47` vs Seq `758.15` ($\to$) @1500: HNSW `894.76` vs Seq `909.76` |
| `fp32_plain` | `P6` | `(4.0, 0.05)` | `9/18` | `9/18` | `Yes` | **`[790, 850]`** | `60` | `~895` | @790: HNSW `837.15` vs Seq `784.33` ($\to$) @850: HNSW `846.04` vs Seq `843.86` |
| `fp32_plain` | `P7` | `(8.0, 0.0025)` | `16/18` | `2/18` | `Yes` | **`[3000, 4000]`** | `1000` | `~3,240` | @3000: HNSW `1937.20` vs Seq `1602.35` ($\to$) @4000: HNSW `1998.66` vs Seq `2136.46` |
| `fp32_plain` | `P8` | `(8.0, 0.01)` | `16/18` | `2/18` | `Yes` | **`[3000, 4000]`** | `1000` | `~2,950` | @3000: HNSW `1940.83` vs Seq `1819.42` ($\to$) @4000: HNSW `2002.41` vs Seq `2425.85` |
| `fp32_plain` | `P9` | `(8.0, 0.05)` | `14/18` | `4/18` | `Yes` | **`[1750, 2000]`** | `250` | `~1,910` | @1750: HNSW `1836.49` vs Seq `1736.84` ($\to$) @2000: HNSW `1867.37` vs Seq `1984.89` |
| `fp16_extended` | `P1` | `(1.0, 0.0025)` | `0/18` | `18/18` | `Yes` | Always `HNSW` ($N \le 500$) | `0` | `< 450 (HNSW all)` | @500: HNSW `98.44` < Seq `117.08` |
| `fp16_extended` | `P2` | `(1.0, 0.01)` | `0/18` | `18/18` | `Yes` | Always `HNSW` ($N \le 500$) | `0` | `< 450 (HNSW all)` | @500: HNSW `101.30` < Seq `153.32` |
| `fp16_extended` | `P3` | `(1.0, 0.05)` | `0/18` | `18/18` | `Yes` | Always `HNSW` ($N \le 500$) | `0` | `< 450 (HNSW all)` | @500: HNSW `116.55` < Seq `346.60` |
| `fp16_extended` | `P4` | `(4.0, 0.0025)` | `14/18` | `4/18` | `Yes` | **`[1750, 2000]`** | `250` | `~1,850` | @1750: HNSW `454.83` vs Seq `409.72` ($\to$) @2000: HNSW `462.90` vs Seq `468.24` |
| `fp16_extended` | `P5` | `(4.0, 0.01)` | `12/18` | `6/18` | `Yes` | **`[1250, 1500]`** | `250` | `~1,630` | @1250: HNSW `438.70` vs Seq `383.15` ($\to$) @1500: HNSW `449.90` vs Seq `459.76` |
| `fp16_extended` | `P6` | `(4.0, 0.05)` | `1/18` | `17/18` | `Yes` | **`[500, 700]`** | `200` | `~910` | @500: HNSW `403.15` vs Seq `346.60` ($\to$) @700: HNSW `421.35` vs Seq `485.03` |
| `fp16_extended` | `P7` | `(8.0, 0.0025)` | `17/18` | `1/18` | `Yes` | **`[4000, 5000]`** | `1000` | `~4,020` | @4000: HNSW `997.72` vs Seq `936.46` ($\to$) @5000: HNSW `1053.94` vs Seq `1170.57` |
| `fp16_extended` | `P8` | `(8.0, 0.01)` | `16/18` | `2/18` | `Yes` | **`[3000, 4000]`** | `1000` | `~3,580` | @3000: HNSW `971.34` vs Seq `919.42` ($\to$) @4000: HNSW `1001.47` vs Seq `1225.85` |
| `fp16_extended` | `P9` | `(8.0, 0.05)` | `12/18` | `6/18` | `Yes` | **`[1250, 1500]`** | `250` | `~2,120` | @1250: HNSW `888.23` vs Seq `865.74` ($\to$) @1500: HNSW `910.89` vs Seq `1038.79` |

---

## 5. Reconciliation of Discrepancies Against Phase 4E.2 Analytical Estimates

1. **PostgreSQL `STD_FUZZ_FACTOR = 1.01` Fuzzy Tie-Break at `N = 850, fp32_plain, P6` (`[790, 850]` vs. `~895`):**
   - At $N = 850$ (`fp32_plain`, Profile `P6`), `Limit(Sort(SeqScan))` has `startup_cost = 843.36` and `total_cost = 843.86`, whereas `Limit(IndexScan)` has `startup_cost = 814.52` and `total_cost = 846.04` (`+2.18` cost units or `+0.258%` higher total cost).
   - Because `compare_path_costs_fuzzily` in PostgreSQL (`src/backend/optimizer/util/pathnode.c`) uses `STD_FUZZ_FACTOR = 1.01` (`1%`), `846.04 <= 1.01 * 843.86 = 852.30` is treated as fuzzily equal on `total_cost`, and PostgreSQL breaks the tie using `startup_cost` (`814.52 < 843.36 / 1.01 = 835.01`), selecting `Index Scan` at $N = 850$. Across all 486 cells in the sweep, this is the **only** cell where the planner selects a path with a slightly higher raw `total_cost`.
2. **`fp32_extended` at Profile `P3` (`(1.0, 0.05)`):**
   - Even when the TOAST startup-cost guard is inactive ($N \le 786$), under `random_page_cost = 1.0` and `cpu_operator_cost = 0.05` (`P3`), the top-$k$ heapsort + distance CPU term on `Seq Scan + Sort` (`250.60` at $N=500$, `393.36` at $N=786$) exceeds the unadjusted HNSW `Limit` cost (`205.51` at $N=500$, `221.08` at $N=786$), so `fp32_extended` `P3` selects `HNSW Index Scan` across all 18 scales ($N \in [500, 5{{,}}000]$).
3. **`fp32_extended` at Profile `P7` (`[1250, 1500]` vs. `~1,120`):**
   - Phase 4E.2 approximated `relpages` continuously ($N / 143$), predicting crossover near $N \approx 1{{,}}120$. In reality, `relpages` for `fp32_extended` is a discrete step function (`7` pages at $N=1{{,}}001$, `8` pages at $N=1{{,}}250$, `10` pages at $N=1{{,}}500$). Because $N=1{{,}}250$ occupies only `8` main-heap pages, `Seq Scan + Sort` costs `50.66` vs. `HNSW` `51.63` (`+0.97` units), keeping `P7` in `Seq Scan` at $N=1{{,}}250$ before crossing over to `HNSW` in $N \in [1{{,}}250, 1{{,}}500]$ (`53.75 < 61.19` at $N=1{{,}}500$).
4. **Earlier Crossover of `fp16_extended` at High `cpu_operator_cost` (`P5`, `P6`, `P9`):**
   - Phase 4E.2's rough table listed $N_{\text{crit}} \approx 910$ (`P6`), `~1,630` (`P5`), and `~2,120` (`P9`) for `fp16_extended`, whereas the actual observed crossover intervals are **`[500, 700]` (`P6`)**, **`[1250, 1500]` (`P5`)**, and **`[1250, 1500]` (`P9`)**.
   - **Mathematical Cause:** Both `fp16_extended` and `fp32_plain` pay the **exact same** per-tuple CPU sort + distance evaluation cost in `Seq Scan + Sort`: $(0.01 + 9.643856\,\text{cpu\_op}) N$ (`0.4922 N` when `cpu_op = 0.05`), while `fp16_extended` pays **half** the HNSW index page startup I/O ($\text{index\_pages} \approx 0.25 N$ vs. $0.50 N$). Therefore, when `cpu_operator_cost` is high (`0.05` in `P6, P9` or `0.01` in `P5`), `fp16_extended` crosses over from `Seq Scan` to `HNSW` *earlier* than (or simultaneously with) `fp32_plain`!
