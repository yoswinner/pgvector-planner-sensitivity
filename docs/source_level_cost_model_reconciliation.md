# Source-Level Cost-Model Evidence and Mathematical Reconciliation
## PostgreSQL 18.4 (`costsize.c`, `selfuncs.c`, `pathnode.c`) & `pgvector` 0.8.4 (`src/hnsw.c`)

**Project:** Precision-Aware Query Planning for Vector Retrieval in PostgreSQL  
**Recommended Manuscript Title:** *How FP16 Vector Representation and TOAST Storage Layouts Shift Query Plan Selection in PostgreSQL: An Empirical and Cost-Model Study*  
**Author:** Yash Pradhan  
**Repository:** `yoswinner/CompressionAwareRag` (`research/planner-sensitivity`, `11780d6ac733f0884d82a277823185f2c058b3af`)  
**Verified Software Versions:** PostgreSQL `18.4` (`x86_64-windows`) and `pgvector` `0.8.4` (confirmed in `../results/planner_sensitivity/full_run_20261031_01/environment_snapshot.json`)

---

## 1. Purpose and Scope

This document consolidates the verified Phase 4A and Phase 4C.1.1 source-level cost-model analysis and mathematical reconciliations governing Section II (*Background and Source-Level Cost-Model Analysis*) of the manuscript. All equations and intermediate values are reconciled directly against:
- **PostgreSQL 18.4 source code:**
  - `src/backend/optimizer/path/costsize.c` (`cost_seqscan`, `cost_index`, `cost_sort`, `cost_tuplesort`, `adjust_limit_rows_costs`)
  - `src/backend/optimizer/util/pathnode.c` (`create_limit_path`)
  - `src/backend/utils/adt/selfuncs.c` (`genericcostestimate`)
- **`pgvector` 0.8.4 source code:**
  - `src/hnsw.c` (`hnswcostestimate`)
- **Primary experimental artifacts:**
  - [`../results/planner_sensitivity/storage_results.csv`](../results/planner_sensitivity/storage_results.csv)
  - `full_run_20261031_01/plan_capture.jsonl` (47 MB raw execution plan capture trace; archived in supplementary Zenodo evidence package)
  - [`../results/planner_sensitivity/full_run_20261031_01/summary_results.csv`](../results/planner_sensitivity/full_run_20261031_01/summary_results.csv)

---

## 2. Exact Execution Sequence in `pgvector` 0.8.4 `hnswcostestimate` (`src/hnsw.c`)

In `pgvector` 0.8.4 (`src/hnsw.c`), `hnswcostestimate` executes in the following exact six-step sequence:

1. **Zero-initialize `GenericCosts`:**
   ```c
   MemSet(&costs, 0, sizeof(costs));
   ```
   Crucially, `costs.numIndexTuples` is initialized to `0` (`0.0`) and is **not** pre-populated with `ratio * path->indexinfo->tuples` before calling `genericcostestimate`.

2. **Invoke PostgreSQL's generic index cost estimator (`genericcostestimate` in `src/backend/utils/adt/selfuncs.c`):**
   ```c
   genericcostestimate(root, path, loop_count, &costs);
   ```
   - **How `genericcostestimate` derives tuple and page estimates for our unfiltered `ORDER BY` workload:**  
     In PostgreSQL 18.4, `genericcostestimate` checks whether the caller supplied a positive `costs->numIndexTuples`. Because `costs.numIndexTuples == 0` and our nearest-neighbor query (`SELECT id FROM ... ORDER BY embedding <=> $1 LIMIT 10`) contains no `WHERE` restriction clauses (`path->indexclauses == NIL`; the `<=>` operator resides in `path->indexorderbys`), `indexSelectivity` is `1.0`. Consequently, `genericcostestimate` sets:
     $$\text{costs.numIndexTuples} = \text{index->tuples} = 1{,}001 \quad (\text{at } N = 1{,}001)$$
     $$\text{costs.numIndexPages} = \text{index->pages} \quad (\text{499 pages for FP32; 250 pages for FP16 at } N = 1{,}001)$$
     and computes the full-index scan cost `costs.indexTotalCost` (`cpu_index_tuple_cost = 0.005`, `cpu_operator_cost = 0.0025` at Profile P4):
     $$\text{costs.indexTotalCost} = \text{numIndexPages} \cdot \text{spc\_random\_page\_cost} + \text{numIndexTuples} \cdot (\text{cpu\_index\_tuple\_cost} + \text{cpu\_operator\_cost})$$
     At Profile P4 (`random_page_cost = 4.0`, `cpu_operator_cost = 0.0025`) for $N = 1{,}001$:
     - Index CPU component across all 1,001 tuples: $1001 \times (0.005 + 0.0025) = \mathbf{7.5075}$
     - `fp32_extended` and `fp32_plain` (`numIndexPages = 499`): $499 \times 4.0 + 7.5075 = \mathbf{2003.5075} \ (\mathbf{2003.51})$
     - `fp16_extended` (`numIndexPages = 250`): $250 \times 4.0 + 7.5075 = \mathbf{1007.5075} \ (\mathbf{1007.51})$

3. **Calculate HNSW graph traversal selectivity (`ratio`):**  
   After `genericcostestimate` returns, `hnswcostestimate` computes the fraction `ratio` of the HNSW graph expected to be traversed for `path->indexinfo->tuples` ($N = 1{,}001$, $m = 16$, `hnsw.ef_search = 40`), yielding:
   $$\text{ratio} = \mathbf{0.405720} \quad (\text{corresponding to } 406.126 \text{ visited index tuples at } N = 1{,}001)$$

4. **Calculate initial (unadjusted) `indexStartupCost`:**
   ```c
   costs.indexStartupCost = costs.indexTotalCost * ratio;
   ```
   Because `costs.indexTotalCost` was computed over all `numIndexPages` and all $1{,}001$ index tuples in Step 2, scaling it by `ratio` in Step 4 yields:
   $$\text{indexStartupCost}_{\text{initial}} = (\text{numIndexPages} \cdot \text{ratio}) \cdot \text{spc\_random\_page\_cost} + 1001 \cdot (\text{cpu\_index\_tuple\_cost} + \text{cpu\_operator\_cost}) \cdot \text{ratio}$$
   At Profile P4 ($N = 1{,}001$):
   - Startup CPU component: $7.5075 \times 0.405720 = \mathbf{3.0460}$
   - `fp32_extended` and `fp32_plain`: $2003.5075 \times 0.405720 = 809.8172 + 3.0460 = \mathbf{812.8632} \ (\mathbf{812.86})$
   - `fp16_extended`: $1007.5075 \times 0.405720 = 405.7200 + 3.0460 = \mathbf{408.7660} \ (\mathbf{408.77})$

5. **Calculate `startupPages`:**
   ```c
   startupPages = costs.numIndexPages * ratio;
   ```
   At $N = 1{,}001$:
   - `fp32_extended` and `fp32_plain`: $499 \times 0.405720 = \mathbf{202.4543}\text{ pages}$
   - `fp16_extended`: $250 \times 0.405720 = \mathbf{101.4300}\text{ pages}$

6. **Apply the `relpages`-dependent conditional HNSW startup-cost adjustment:**
   ```c
   if (startupPages > path->indexinfo->rel->pages && ratio < 0.5)
   {
       /* Change random page cost to sequential page cost */
       costs.indexStartupCost -= startupPages * (costs.spc_random_page_cost - spc_seq_page_cost);

       /* Remove cost of extra pages */
       costs.indexStartupCost -= (startupPages - path->indexinfo->rel->pages) * spc_seq_page_cost;
   }
   ```
   - **Important Terminology Note:** `hnswcostestimate` does **not** explicitly inspect whether a column is stored in `pg_toast`. Rather, its `startupPages > path->indexinfo->rel->pages && ratio < 0.5` guard compares `startupPages` against the main-heap page count (`relpages`), which is indirectly governed by TOAST storage layout (`relpages = 7` for out-of-line `fp32_extended` vs. `501` for inline `fp32_plain` and `201` for inline `fp16_extended` at $N = 1{,}001$).
   - **Algebraic Simplification of $\Delta$:**
     $$\Delta = \text{startupPages} \cdot (\text{random\_page\_cost} - \text{seq\_page\_cost}) + (\text{startupPages} - \text{relpages}) \cdot \text{seq\_page\_cost}$$
     $$\Delta = \text{startupPages} \cdot \text{random\_page\_cost} - \text{relpages} \cdot \text{seq\_page\_cost}$$
   - **Profile-Dependent Values of $\Delta$ for `fp32_extended` at $N = 1{,}001$ (`relpages = 7`, `seq_page_cost = 1.0`):**
     - Under `random_page_cost = 1.0` (`P1–P3`): $\Delta = 202.4543 \times 1.0 - 7 \times 1.0 = \mathbf{195.4543} \ (\mathbf{195.45})$.
     - Under `random_page_cost = 4.0` (`P4–P6`): Term 1 $= 202.4543 \times 3.0 = 607.3629$, Term 2 $= (202.4543 - 7) \times 1.0 = 195.4543$, so $\Delta = \mathbf{802.8172}$ (which rounds to `802.82`, or `802.81` when taking the difference of two-decimal display values $812.86 - 10.05$).
     - Under `random_page_cost = 8.0` (`P7–P9`): $\Delta = 202.4543 \times 8.0 - 7 \times 1.0 = \mathbf{1612.6344} \ (\mathbf{1612.63})$.
   - **Cancellation of `random_page_cost` in Adjusted Startup Cost:** Subtracting $\Delta$ from $\text{indexStartupCost}_{\text{initial}}$ cancels $\text{startupPages} \cdot \text{random\_page\_cost}$ and leaves:
     $$\text{indexStartupCost}_{\text{adjusted}} = \text{relpages} \cdot \text{seq\_page\_cost} + \text{indexCPUCost}_{\text{total}} \cdot \text{ratio}$$
     For `fp32_extended` at $N = 1{,}001$, this yields the exact same adjusted startup cost across all three `random_page_cost` levels: **`10.05`** (`10.0460`) at `P1, P4, P7` (`cpu_op = 0.0025`), **`13.09`** (`13.0919`) at `P2, P5, P8` (`cpu_op = 0.01`), and **`29.34`** (`29.3370`) at `P3, P6, P9` (`cpu_op = 0.05`).
   - Conversely, for `fp32_plain` (`202.4543 <= 501`) and `fp16_extended` (`101.4300 <= 201`), the guard is **False**, so $\Delta = 0.00$ and `*indexStartupCost` remains **`812.86`** (`80.88×` startup-cost ratio vs. `10.05` at P4) and **`408.77`** (`40.67×` startup-cost ratio vs. `10.05` at P4).

---

## 3. Three-Level Propagation from `hnswcostestimate` to `cost_index` and `create_limit_path`

1. **Level 1 — Index Access Method (`hnswcostestimate` in `src/hnsw.c`):**
   Outputs `*indexStartupCost`, `*indexTotalCost`, and `*indexCorrelation = 0.0`.
2. **Level 2 — `Index Scan` Path (`cost_index` in `src/backend/optimizer/path/costsize.c`):**
   - Sets `IndexScan_startup = *indexStartupCost`.
   - Because `indexCorrelation = 0.0` and an unconstrained scan is estimated to return all $N = 1{,}001$ tuples, `cost_index` adds fetching all `relpages` heap pages at `random_page_cost` plus per-tuple CPU costs `N * (cpu_tuple_cost + cpu_operator_cost)` (`1001 * 0.0125 = 12.5125` at P4):
     $$\text{IndexScan}_{\text{run}} = (\text{indexTotalCost} - \text{IndexScan}_{\text{startup}}) + \text{relpages} \cdot \text{random\_page\_cost} + N \cdot (\text{cpu\_tuple\_cost} + \text{cpu\_operator\_cost})$$
     $$\text{IndexScan}_{\text{total}} = \text{IndexScan}_{\text{startup}} + \text{IndexScan}_{\text{run}} = \text{indexTotalCost} + \text{relpages} \cdot \text{random\_page\_cost} + 12.5125$$
   - Note that `IndexScan_total` (`2044.02` for `fp32_extended`, `4020.02` for `fp32_plain`, `1824.02` for `fp16_extended` at P4 in `plan_capture.jsonl` lines 201, 721, 1281) is invariant to $\Delta$: subtracting $\Delta$ from `IndexScan_startup` increases `IndexScan_run` by $+\Delta$.
3. **Level 3 — Root `Limit (rows=10)` Node (`create_limit_path` / `adjust_limit_rows_costs` in `pathnode.c` / `costsize.c`):**
   - Scales `IndexScan_run` by $\frac{10}{1001}$:
     $$\text{Limit}_{\text{startup}} = \text{IndexScan}_{\text{startup}}, \qquad \text{Limit}_{\text{total}} = \text{IndexScan}_{\text{startup}} + \frac{10}{1001}\text{IndexScan}_{\text{run}}$$
   - Because `IndexScan_startup` drops by $\Delta$ while `IndexScan_run` increases by $+\Delta$, scaling `IndexScan_run` by $\frac{10}{1001}$ produces a net root `Limit` total-cost reduction of:
     $$\Delta_{\text{Limit}} = \left(1 - \frac{10}{1001}\right)\Delta = \frac{991}{1001} \times 802.8172 = \mathbf{794.7970}\text{ cost units at Profile P4}$$
   - Resulting Profile P4 root `Limit` total costs (`est_total_cost` under `forced_hnsw`):
     - `fp32_extended`: $10.0460 + \frac{10}{1001}(2033.9740) = 10.0460 + 20.3194 = \mathbf{30.3654} \ (\mathbf{30.37})$
     - `fp32_plain`: $812.8632 + \frac{10}{1001}(3207.1568) = 812.8632 + 32.0395 = \mathbf{844.9027} \ (\mathbf{844.90})$ (`27.82×` root `Limit` total-cost ratio vs. `30.37`)
     - `fp16_extended`: $408.7660 + \frac{10}{1001}(1415.2540) = 408.7660 + 14.1384 = \mathbf{422.9044} \ (\mathbf{422.90})$ (`13.92×` root `Limit` total-cost ratio vs. `30.37`)

---

## 4. Competing Exact (`Limit` $\to$ `Sort` $\to$ `Seq Scan`) Cost Chain (`cost_seqscan` & `cost_tuplesort`)

In PostgreSQL 18.4 (`src/backend/optimizer/path/costsize.c`):

1. **Sequential Scan (`cost_seqscan`):**
   $$\text{SeqScan}_{\text{startup}} = 0.00, \qquad \text{SeqScan}_{\text{total}} = \text{relpages} \cdot \text{seq\_page\_cost} + N \cdot (\text{cpu\_tuple\_cost} + \text{cpu\_operator\_cost})$$
   At Profile P4 ($N = 1{,}001$, `spc = 1.0`, `cpu_tuple = 0.01`, `cpu_op = 0.0025`):
   $$\text{SeqScan}_{\text{total}} = \text{relpages} + 1001 \times 0.0125 = \text{relpages} + \mathbf{12.5125}$$
   - `fp32_extended` (`relpages = 7`): $\mathbf{19.5125} \ (\mathbf{19.51})$
   - `fp32_plain` (`relpages = 501`): $\mathbf{513.5125} \ (\mathbf{513.51})$
   - `fp16_extended` (`relpages = 201`): $\mathbf{213.5125} \ (\mathbf{213.51})$

2. **Bounded Top-$N$ Heap Sort (`cost_sort` / `cost_tuplesort`):**
   For `tuples = 1001` and `limit_tuples = 10` (`LIMIT 10`), `cost_tuplesort` sets `output_tuples = 10` and maintains a bounded heap of size $2.0 \times \text{output\_tuples} = \mathbf{20.0}$:
   $$\text{sort\_startup\_comparisons} = 2.0 \cdot \text{cpu\_operator\_cost} \cdot \text{tuples} \cdot \log_2(2.0 \cdot \text{output\_tuples})$$
   At Profile P4 (`cpu_operator_cost = 0.0025`):
   $$\text{sort\_startup\_comparisons} = 2.0 \times 0.0025 \times 1001 \times \log_2(20.0) = 5.005 \times 4.321928095 = \mathbf{21.63125}\text{ cost units}$$
   Adding `sort_startup_comparisons` and per-tuple extraction cost $\text{Sort}_{\text{run}} = \text{cpu\_operator\_cost} \times 1001 = \mathbf{2.5025}$:
   - `fp32_extended`: `Sort` Startup $= 19.5125 + 21.63125 = \mathbf{41.14375} \ (\mathbf{41.14})$, `Sort` Total $= \mathbf{43.64625} \ (\mathbf{43.65})$
   - `fp32_plain`: `Sort` Startup $= 513.5125 + 21.63125 = \mathbf{535.14375} \ (\mathbf{535.14})$, `Sort` Total $= \mathbf{537.64625} \ (\mathbf{537.65})$
   - `fp16_extended`: `Sort` Startup $= 213.5125 + 21.63125 = \mathbf{235.14375} \ (\mathbf{235.14})$, `Sort` Total $= \mathbf{237.64625} \ (\mathbf{237.65})$

3. **Root `Limit (rows=10)` over `Sort` (`create_limit_path`):**
   $$\text{Limit}_{\text{startup}} = \text{Sort}_{\text{startup}}, \qquad \text{Limit}_{\text{total}} = \text{Sort}_{\text{startup}} + \frac{10}{1001} \times 2.5025 = \text{Sort}_{\text{startup}} + \mathbf{0.0250}$$
   - `fp32_extended`: Startup $= \mathbf{41.14}$, Total $= \mathbf{41.17}$ (`41.1688`)
   - `fp32_plain`: Startup $= \mathbf{535.14}$, Total $= \mathbf{535.17}$ (`535.1688`)
   - `fp16_extended`: Startup $= \mathbf{235.14}$, Total $= \mathbf{235.17}$ (`235.1688`)

