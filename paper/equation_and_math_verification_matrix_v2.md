# Phase R4.4.1 — Equation Typography and Mathematical Fidelity Verification Matrix (`v2.1`)

**Candidate Status:** `R4.4.1 — FINAL FORMATTING CANDIDATE, PENDING AUTHOR CONFIRMATIONS`  
**Candidate DOCX:** `research_paper_ieee_a4_v2.docx` (`f88d340896a167a056b22b860d40b945cc94bb8e55e5a1ad7c55ceb24d7df6df`)  
**Candidate PDF:** `research_paper_ieee_a4_v2.pdf` (`00cdef63654e0334879b70c0dbf21a511d0cbcb4b87595d395f1046445017099`)  
**Canonical Source:** `final_research_paper_source_v1.3.2.md` (`8d3b670a9320fe429c9e4fab4f1981afe4a505404a7e437101ffce95f9d5ab4f`)  

## 1. All 11 Displayed Equations (`styleId="equation"`, `Times New Roman` 8.5 pt in DOCX / `LiberationSerif` in Linux PDF)

| # | Source Line | Tag | Source LaTeX (`$$ ... $$`) | Rendered DOCX / PDF Text (with Subscripts/Superscripts) | Visual & Semantic Status |
| :---: | :---: | :---: | :--- | :--- | :---: |
| **1** | `L47` | `(1)` | `\text{TOAST\_TUPLE\_THRESHOLD} = \text{MaximumBytesPerTuple}(4) = \text{MAXALIGN\_DOWN}\!\left(\left\lfloor\frac{8192 - \text{MAXALIGN}(24 + 4 \times 4)}{4}\right\rfloor\right) = \mathbf{2{,}032\text{ B}} \tag{1}` | `TOAST_TUPLE_THRESHOLD = MaximumBytesPerTuple(4) = MAXALIGN_DOWN(⌊(8192 - MAXALIGN(24 + 4 × 4)) / 4⌋) = 2,032 B  (1)` | **PASS (Verified on Page 3–5)** |
| **2** | `L63` | `(2)` | `\text{costs.indexTotalCost} = \text{numIndexPages} \cdot \text{spc\_random\_page\_cost} + N \cdot (\text{cpu\_index\_tuple\_cost} + \text{cpu\_operator\_cost}) \tag{2}` | `costs.indexTotalCost = numIndexPages · spc_random_page_cost + N · (cpu_index_tuple_cost + cpu_operator_cost)  (2)` | **PASS (Verified on Page 3–5)** |
| **3** | `L67` | `(3)` | `\text{candidateTuples}(N) = \text{entryLevel}(N) \cdot m + C_{\text{cal}}(m, ef_{\text{search}}) \cdot \ln N, \qquad \text{ratio}(N) = \frac{\text{candidateTuples}(N)}{N} \tag{3}` | `candidateTuples(N) = entryLevel(N) · m + Ccal(m, efsearch) · ln N,      ratio(N) = candidateTuples(N) / N  (3)` | **PASS (Verified on Page 3–5)** |
| **4** | `L71` | `(4)` | `\text{indexStartupCost}_{\text{initial}} = \text{costs.indexTotalCost} \cdot \text{ratio} = (\text{numIndexPages} \cdot \text{spc\_random\_page\_cost}) \cdot \text{ratio} + \text{indexCPUCost}_{\text{total}} \cdot \text{ratio} \tag{4}` | `indexStartupCostinitial = costs.indexTotalCost · ratio = (numIndexPages · spc_random_page_cost) · ratio + indexCPUCosttotal · ratio  (4)` | **PASS (Verified on Page 3–5)** |
| **5** | `L73` | *(unnumbered)* | `\text{indexStartupCost}_{\text{initial, FP32}} = 1996.0 \times 0.40572022 + 3.045945 = 809.817559 + 3.045945 = \mathbf{812.8635} \ (\mathbf{812.86}\text{ in }\texttt{EXPLAIN})` | `indexStartupCostinitial, FP32 = 1996.0 × 0.40572022 + 3.045945 = 809.817559 + 3.045945 = 812.8635  (812.86 in EXPLAIN)` | **PASS (Verified on Page 3–5)** |
| **6** | `L74` | *(unnumbered)* | `\text{indexStartupCost}_{\text{initial, FP16}} = 1000.0 \times 0.40572022 + 3.045945 = 405.720220 + 3.045945 = \mathbf{408.7662} \ (\mathbf{408.77}\text{ in }\texttt{EXPLAIN})` | `indexStartupCostinitial, FP16 = 1000.0 × 0.40572022 + 3.045945 = 405.720220 + 3.045945 = 408.7662  (408.77 in EXPLAIN)` | **PASS (Verified on Page 3–5)** |
| **7** | `L91` | `(5)` | `\Delta = \text{startupPages} \cdot (\text{random\_page\_cost} - \text{seq\_page\_cost}) + (\text{startupPages} - \text{relpages}) \cdot \text{seq\_page\_cost} = \text{startupPages} \cdot \text{random\_page\_cost} - \text{relpages} \cdot \text{seq\_page\_cost} \tag{5}` | `Δ = startupPages · (random_page_cost - seq_page_cost) + (startupPages - relpages) · seq_page_cost = startupPages · random_page_cost - relpages · seq_page_cost  (5)` | **PASS (Verified on Page 3–5)** |
| **8** | `L93` | `(6)` | `\text{indexStartupCost}_{\text{adjusted}} = \text{relpages} \cdot \text{seq\_page\_cost} + N \cdot (\text{cpu\_index\_tuple\_cost} + \text{cpu\_operator\_cost}) \cdot \text{ratio} \tag{6}` | `indexStartupCostadjusted = relpages · seq_page_cost + N · (cpu_index_tuple_cost + cpu_operator_cost) · ratio  (6)` | **PASS (Verified on Page 3–5)** |
| **9** | `L99` | `(7)` | `\text{IndexScan}_{\text{run}} = (\text{indexTotalCost} - \text{IndexScan}_{\text{startup}}) + \text{relpages} \cdot \text{random\_page\_cost} + N \cdot (\text{cpu\_tuple\_cost} + \text{cpu\_operator\_cost}) \tag{7}` | `IndexScanrun = (indexTotalCost - IndexScanstartup) + relpages · random_page_cost + N · (cpu_tuple_cost + cpu_operator_cost)  (7)` | **PASS (Verified on Page 3–5)** |
| **10** | `L102` | `(8)` | `\text{Limit}_{\text{total, HNSW}} = \text{IndexScan}_{\text{startup}} + \frac{K}{N} \cdot \text{IndexScan}_{\text{run}} \tag{8}` | `Limittotal, HNSW = IndexScanstartup + (K / N) · IndexScanrun  (8)` | **PASS (Verified on Page 3–5)** |
| **11** | `L105` | `(9)` | `\text{Limit}_{\text{total, Seq}} = \text{relpages} \cdot \text{seq\_page\_cost} + N \cdot \big(\text{cpu\_tuple\_cost} + \text{cpu\_operator\_cost}\,[1 + 2\log_2(2K)]\big) + K \cdot \text{cpu\_operator\_cost} \tag{9}` | `Limittotal, Seq = relpages · seq_page_cost + N · (cpu_tuple_cost + cpu_operator_cost [1 + 2log2(2K)]) + K · cpu_operator_cost  (9)` | **PASS (Verified on Page 3–5)** |

## 2. Special Mathematical Constructs & Combinatorial Notation Treatment

| Construct Category | Source LaTeX Example(s) | Rendered Output in DOCX / PDF | Semantic Equivalence & Fidelity Verification |
| :--- | :--- | :--- | :--- |
| **Binomial Notation (`\binom`)** | `\binom{28}{2} = 378` (`L392`) | `C(28, 2) = 378` | Counts unordered 2-element pairs among the 28 duplicate vectors in $T$; $C(28, 2) = 378$ is combinatorially identical and remains 100% extractable in `python-docx` `Paragraph.text` and `pdftotext`. |
| **Combining Overbar & Tilde (`\bar`, `\tilde`)** | `\bar{L}_{P7}(q)`, `\tilde{L}_{P7}(q)` (`L313`) | `L̄` + sub `P7` `(q)`, `L̃` + sub `P7` `(q)` | Rendered using Unicode combining macron (`U+0304`) and combining tilde (`U+0303`) over italic `L` with Word subscript `P7`. |
| **Square Root (`\sqrt`)** | `|z|/\sqrt{20} = 0.8723` (`L313`) | `|z|/√(20) = 0.8723` | Explicit parenthesized radical `√(20)` preserves unambiguous scope of the radicand. |
| **Floor & Ceiling Delimiters (`\lfloor..`, `\lceil..`)** | `\left\lfloor ... \right\rfloor`, `\lceil N/157 \rceil` (`L47, L66, L98, L331`) | `⌊...⌋`, `⌈N/157⌉` | Paired Unicode floor (`U+230A`/`U+230B`) and ceiling (`U+2308`/`U+2309`) glyphs verified in PDF text and 150 DPI PNGs. |
| **Escaped Braces & Underscores (`\{`, `\}`, `\_`)** | `\{1{,}001, 5{,}000, 10{,}000\}`, `\text{spc\_random\_page\_cost}` | `{1,001, 5,000, 10,000}`, `spc_random_page_cost` | Protected via Unicode private-use sentinels before LaTeX group stripping and subscript splitting; zero braces or underscores lost. |
| **Greek Symbols & Operators** | `\Delta, \tau, \alpha, \chi^2_8, \epsilon, \mu_W, \sigma_W, \sim, \iff` | `Δ, τ, α, χ²₈, ϵ, μ_W, σ_W, ~, ⟺` | All Greek symbols and relational operators verified in DOCX XML and PDF text. |
| **Subscripts & Superscripts (`_`, `^`)** | `10^{-7}`, `2^{-23}`, `\chi^2_8`, `p_{\text{adj}}`, `C_{\text{ties}}` | `10`+sup`−7`, `2`+sup`−23`, `χ`+sup`2`+sub`8`, `p`+sub`adj`, `C`+sub`ties` | `129` `<w:vertAlign w:val="subscript"/>` runs and `44` `<w:vertAlign w:val="superscript"/>` runs verified in `word/document.xml`. |

## 3. Complete Inventory of All 241 Distinct Inline Mathematical Expressions (`557` Total Occurrences, All Verified by `test_03`)

| # | Source Inline Math (`$...$`) | Rendered Plain Text | Has Subscript Run | Has Superscript Run |
| :---: | :--- | :--- | :---: | :---: |
| 1 | `$0.0257$` | `0.0257` | No | No |
| 2 | `$1000.0 \times 0.40572022 + 3.045945 = 405.7202 + 3.0459 = 408.7662$` | `1000.0 × 0.40572022 + 3.045945 = 405.7202 + 3.0459 = 408.7662` | No | No |
| 3 | `$1001 \times 0.0075 = 7.5075$` | `1001 × 0.0075 = 7.5075` | No | No |
| 4 | `$101.4301$` | `101.4301` | No | No |
| 5 | `$10^{-5}$` | `10-5` | No | Yes |
| 6 | `$10^{-6}$` | `10-6` | No | Yes |
| 7 | `$10{,}000$` | `10,000` | No | No |
| 8 | `$18 \times 3 \times 9$` | `18 × 3 × 9` | No | No |
| 9 | `$1996.0 \times 0.40572022 + 3.045945 = 809.8176 + 3.0459 = 812.8635$` | `1996.0 × 0.40572022 + 3.045945 = 809.8176 + 3.0459 = 812.8635` | No | No |
| 10 | `$1{,}001$` | `1,001` | No | No |
| 11 | `$2$` | `2` | No | No |
| 12 | `$2.0 \cdot \text{cpu\_operator\_cost} \cdot N \log_2(2.0 K)$` | `2.0 · cpu_operator_cost · N log2(2.0 K)` | Yes | No |
| 13 | `$2.479\text{ ms}$` | `2.479 ms` | No | No |
| 14 | `$2.881\text{ ms}$` | `2.881 ms` | No | No |
| 15 | `$250 \times 0.40572022 = 101.430055$` | `250 × 0.40572022 = 101.430055` | No | No |
| 16 | `$256 \le N < 4{,}096$` | `256 ≤ N < 4,096` | No | No |
| 17 | `$2TN/(2T+N) > T - 1 \iff \mathbf{N > 2T(T-1)/(T+1)}$` | `2TN/(2T+N) > T - 1 ⟺ N > 2T(T-1)/(T+1)` | No | No |
| 18 | `$2^{-23} \approx 1.192 \times 10^{-7}$` | `2-23 ≈ 1.192 × 10-7` | No | Yes |
| 19 | `$2^{20}$` | `220` | No | Yes |
| 20 | `$2d + 8 = 1{,}544\text{ B}$` | `2d + 8 = 1,544 B` | No | No |
| 21 | `$3$` | `3` | No | No |
| 22 | `$3 \times 3$` | `3 × 3` | No | No |
| 23 | `$3 \times 3 \times 3 \times 9 \times 20 = 4{,}860$` | `3 × 3 × 3 × 9 × 20 = 4,860` | No | No |
| 24 | `$405.7200 + 3.0460 = 408.7660$` | `405.7200 + 3.0460 = 408.7660` | No | No |
| 25 | `$408.7662 / 10.0459 = 40.6897\times \approx \mathbf{40.69\times}$` | `408.7662 / 10.0459 = 40.6897× ≈ 40.69×` | No | No |
| 26 | `$422.9044 / 30.3654 = \mathbf{13.93\times}$` | `422.9044 / 30.3654 = 13.93×` | No | No |
| 27 | `$499 \times 0.40572022 = 202.454390$` | `499 × 0.40572022 = 202.454390` | No | No |
| 28 | `$4{,}096 \le N < 65{,}536$` | `4,096 ≤ N < 65,536` | No | No |
| 29 | `$5 \times 1{,}580\text{ B} = 7{,}900\text{ B} \le 8{,}168\text{ B}$` | `5 × 1,580 B = 7,900 B ≤ 8,168 B` | No | No |
| 30 | `$500$` | `500` | No | No |
| 31 | `$5{,}000$` | `5,000` | No | No |
| 32 | `$7 \times 1.0 + 3.045945 = \mathbf{10.0459}$` | `7 × 1.0 + 3.045945 = 10.0459` | No | No |
| 33 | `$7.5075 \times 0.40572022 = 3.045945 \approx 3.0459$` | `7.5075 × 0.40572022 = 3.045945 ≈ 3.0459` | No | No |
| 34 | `$768 \times 4\text{ B} = 3{,}072\text{ B}$` | `768 × 4 B = 3,072 B` | No | No |
| 35 | `$786$` | `786` | No | No |
| 36 | `$787$` | `787` | No | No |
| 37 | `$788.15 / 8.95 = 88.0615\times$` | `788.15 / 8.95 = 88.0615×` | No | No |
| 38 | `$8 \to 10$` | `8 → 10` | No | No |
| 39 | `$809.8172 + 3.0460 = 812.8632$` | `809.8172 + 3.0460 = 812.8632` | No | No |
| 40 | `$812.8635 / 10.0459 = 80.9146\times \approx \mathbf{80.91\times}$` | `812.8635 / 10.0459 = 80.9146× ≈ 80.91×` | No | No |
| 41 | `$844.9027 / 30.3654 = \mathbf{27.82\times}$` | `844.9027 / 30.3654 = 27.82×` | No | No |
| 42 | `$9 \times 20 = 180$` | `9 × 20 = 180` | No | No |
| 43 | `$= 202.4544$` | `= 202.4544` | No | No |
| 44 | `$> 0$` | `> 0` | No | No |
| 45 | `$> 50\text{ ms}$` | `> 50 ms` | No | No |
| 46 | `$B$` | `B` | No | No |
| 47 | `$B = \{8105, 5314\}$` | `B = {8105, 5314}` | No | No |
| 48 | `$B_\tau(q) = \{c \in \mathcal{C}_N \mid d_{\text{FP32}}(c, q) < D(q) - \tau\}$` | `Bτ(q) = {c ∈ CN  \|  dFP32(c, q) < D(q) - τ}` | Yes | No |
| 49 | `$C_{\text{cal}} = 54.152441134$` | `Ccal = 54.152441134` | Yes | No |
| 50 | `$C_{\text{cal}}(16, 40) = 54.152441134$` | `Ccal(16, 40) = 54.152441134` | Yes | No |
| 51 | `$C_{\text{ties}} = 1.0000$` | `Cties = 1.0000` | Yes | No |
| 52 | `$D = 0.44327880887538984$` | `D = 0.44327880887538984` | No | No |
| 53 | `$D = 0.45295169$` | `D = 0.45295169` | No | No |
| 54 | `$D(q) = d_{\text{FP32}}(c_{(10)}, q)$` | `D(q) = dFP32(c(10), q)` | Yes | No |
| 55 | `$K$` | `K` | No | No |
| 56 | `$K = 10$` | `K = 10` | No | No |
| 57 | `$K \cdot \text{cpu\_operator\_cost}$` | `K · cpu_operator_cost` | No | No |
| 58 | `$K/N$` | `K/N` | No | No |
| 59 | `$N$` | `N` | No | No |
| 60 | `$N < 2{,}000$` | `N < 2,000` | No | No |
| 61 | `$N < 500$` | `N < 500` | No | No |
| 62 | `$N = 10{,}000$` | `N = 10,000` | No | No |
| 63 | `$N = 1{,}001$` | `N = 1,001` | No | No |
| 64 | `$N = 1{,}001, 5{,}000$` | `N = 1,001, 5,000` | No | No |
| 65 | `$N = 1{,}001, 5{,}000,$` | `N = 1,001, 5,000,` | No | No |
| 66 | `$N = 1{,}250$` | `N = 1,250` | No | No |
| 67 | `$N = 1{,}500$` | `N = 1,500` | No | No |
| 68 | `$N = 20$` | `N = 20` | No | No |
| 69 | `$N = 500$` | `N = 500` | No | No |
| 70 | `$N = 50{,}000$` | `N = 50,000` | No | No |
| 71 | `$N = 5{,}000$` | `N = 5,000` | No | No |
| 72 | `$N = 786$` | `N = 786` | No | No |
| 73 | `$N = 786 \to 787$` | `N = 786 → 787` | No | No |
| 74 | `$N = 787$` | `N = 787` | No | No |
| 75 | `$N = 850$` | `N = 850` | No | No |
| 76 | `$N \approx 1{,}000$` | `N ≈ 1,000` | No | No |
| 77 | `$N \approx 50{,}000$` | `N ≈ 50,000` | No | No |
| 78 | `$N \ge 2{,}000$` | `N ≥ 2,000` | No | No |
| 79 | `$N \ge 5{,}000$` | `N ≥ 5,000` | No | No |
| 80 | `$N \ge 787$` | `N ≥ 787` | No | No |
| 81 | `$N \in [1{,}250, 1{,}500]$` | `N ∈ [1,250, 1,500]` | No | No |
| 82 | `$N \in [500, 5{,}000]$` | `N ∈ [500, 5,000]` | No | No |
| 83 | `$N \in [500, 786]$` | `N ∈ [500, 786]` | No | No |
| 84 | `$N \in \{1{,}001, 5{,}000, 10{,}000\}$` | `N ∈ {1,001, 5,000, 10,000}` | No | No |
| 85 | `$N \in \{500, 700, 750, 780, 785, 786, 787, 788, 790, 850, 1{,}250, 1{,}500, 1{,}750, 2{,}000, 3{,}000, 4{,}000\}$` | `N ∈ {500, 700, 750, 780, 785, 786, 787, 788, 790, 850, 1,250, 1,500, 1,750, 2,000, 3,000, 4,000}` | No | No |
| 86 | `$N \in \{5{,}000, 10{,}000\}$` | `N ∈ {5,000, 10,000}` | No | No |
| 87 | `$N \le 10{,}000$` | `N ≤ 10,000` | No | No |
| 88 | `$N \le 1{,}250$` | `N ≤ 1,250` | No | No |
| 89 | `$N \le 786$` | `N ≤ 786` | No | No |
| 90 | `$N, m,$` | `N, m,` | No | No |
| 91 | `$N=500$` | `N=500` | No | No |
| 92 | `$N=786$` | `N=786` | No | No |
| 93 | `$N=787$` | `N=787` | No | No |
| 94 | `$P_{50}$` | `P50` | Yes | No |
| 95 | `$P_{50}, P_{95}$` | `P50, P95` | Yes | No |
| 96 | `$P_{95}$` | `P95` | Yes | No |
| 97 | `$Q$` | `Q` | No | No |
| 98 | `$R_{\text{ref}}(q) = (c_{(1)}, \dots, c_{(10)})$` | `Rref(q) = (c(1), …, c(10))` | Yes | No |
| 99 | `$S \subseteq \mathcal{C}_N$` | `S ⊆ CN` | Yes | No |
| 100 | `$S_{\text{winner}} < S_{\text{loser}} / 1.01$` | `Swinner < Sloser / 1.01` | Yes | No |
| 101 | `$T$` | `T` | No | No |
| 102 | `$T = \text{relpages}$` | `T = relpages` | No | No |
| 103 | `$T = \text{relpages} \le b$` | `T = relpages ≤ b` | No | No |
| 104 | `$T_\tau(q) = \{c \in \mathcal{C}_N \mid \|d_{\text{FP32}}(c, q) - D(q)\| \le \tau\}$` | `Tτ(q) = {c ∈ CN  \|  \|dFP32(c, q) - D(q)\| ≤ τ}` | Yes | No |
| 105 | `$W$` | `W` | No | No |
| 106 | `$W = 0.0$` | `W = 0.0` | No | No |
| 107 | `$W = 28.0$` | `W = 28.0` | No | No |
| 108 | `$[N_{\text{Seq}}, N_{\text{HNSW}}]$` | `[NSeq, NHNSW]` | Yes | No |
| 109 | `$\Delta$` | `Δ` | No | No |
| 110 | `$\Delta = 0$` | `Δ = 0` | No | No |
| 111 | `$\Delta = 0.00$` | `Δ = 0.00` | No | No |
| 112 | `$\Delta = 607.3629 + 195.4543 = 802.8172$` | `Δ = 607.3629 + 195.4543 = 802.8172` | No | No |
| 113 | `$\Delta = 607.3632 + 195.4544 = 802.8176$` | `Δ = 607.3632 + 195.4544 = 802.8176` | No | No |
| 114 | `$\Delta = 802.8176$` | `Δ = 802.8176` | No | No |
| 115 | `$\Delta d = 0.0$` | `Δ d = 0.0` | No | No |
| 116 | `$\Delta d = 1.665 \times 10^{-6}$` | `Δ d = 1.665 × 10-6` | No | Yes |
| 117 | `$\Delta_{\text{Limit}} = (1 - K/N)\Delta$` | `ΔLimit = (1 - K/N)Δ` | Yes | No |
| 118 | `$\Delta_{\text{mean}, q} = \bar{L}_{P7}(q) - \bar{L}_{P4}(q)$` | `Δmean, q = L̄P7(q) - L̄P4(q)` | Yes | No |
| 119 | `$\Delta_{\text{med}, q} = \tilde{L}_{P7}(q) - \tilde{L}_{P4}(q)$` | `Δmed, q = L̃P7(q) - L̃P4(q)` | Yes | No |
| 120 | `$\alpha = 0.05$` | `α = 0.05` | No | No |
| 121 | `$\binom{28}{2} = 378$` | `C(28, 2) = 378` | No | No |
| 122 | `$\chi^2_8$` | `χ28` | Yes | Yes |
| 123 | `$\epsilon$` | `ϵ` | No | No |
| 124 | `$\in \{0.0025, 0.0100, 0.0500\}$` | `∈ {0.0025, 0.0100, 0.0500}` | No | No |
| 125 | `$\in \{1.0, 4.0, 8.0\}$` | `∈ {1.0, 4.0, 8.0}` | No | No |
| 126 | `$\le 0.01$` | `≤ 0.01` | No | No |
| 127 | `$\mathcal{C}_N$` | `CN` | Yes | No |
| 128 | `$\max(C_1, C_2) \le 1.01\min(C_1, C_2)$` | `max(C1, C2) ≤ 1.01min(C1, C2)` | Yes | No |
| 129 | `$\mid$` | ` \| ` | No | No |
| 130 | `$\pm$` | `±` | No | No |
| 131 | `$\sim\!500 < d < \sim\!1{,}000$` | `~500 < d < ~1,000` | No | No |
| 132 | `$\tau$` | `τ` | No | No |
| 133 | `$\tau = 10^{-5}$` | `τ = 10-5` | No | Yes |
| 134 | `$\tau = 10^{-6}$` | `τ = 10-6` | No | Yes |
| 135 | `$\tau = 10^{-6} \mid 10^{-5}$` | `τ = 10-6  \|  10-5` | No | Yes |
| 136 | `$\tau = 10^{-7}$` | `τ = 10-7` | No | Yes |
| 137 | `$\tau = 10^{-7}, 10^{-6}$` | `τ = 10-7, 10-6` | No | Yes |
| 138 | `$\tau = 10^{-7}, 10^{-6} \mid 10^{-5}$` | `τ = 10-7, 10-6  \|  10-5` | No | Yes |
| 139 | `$\tau \ge 0$` | `τ ≥ 0` | No | No |
| 140 | `$\tau \in \{10^{-7}, 10^{-6}, 10^{-5}\}$` | `τ ∈ {10-7, 10-6, 10-5}` | No | Yes |
| 141 | `$\tau \in \{10^{-7}, 10^{-6}\}$` | `τ ∈ {10-7, 10-6}` | No | Yes |
| 142 | `$\tau \le 10^{-6}$` | `τ ≤ 10-6` | No | Yes |
| 143 | `$\text{IndexScan}_{\text{run}}$` | `IndexScanrun` | Yes | No |
| 144 | `$\text{IndexScan}_{\text{startup}} = \text{*indexStartupCost}$` | `IndexScanstartup = *indexStartupCost` | Yes | No |
| 145 | `$\text{IndexScan}_{\text{total}} = \text{IndexScan}_{\text{startup}} + \text{IndexScan}_{\text{run}}$` | `IndexScantotal = IndexScanstartup + IndexScanrun` | Yes | No |
| 146 | `$\text{Initial} - \Delta$` | `Initial - Δ` | No | No |
| 147 | `$\text{MAXALIGN}(t_{\text{len}}(d)) = 32 + \text{VARSIZE}(d)$` | `MAXALIGN(tlen(d)) = 32 + VARSIZE(d)` | Yes | No |
| 148 | `$\text{MAXALIGN}(t_{\text{len}}) = 1{,}576\text{ B}$` | `MAXALIGN(tlen) = 1,576 B` | Yes | No |
| 149 | `$\text{MAXALIGN}(t_{\text{len}}) = 1{,}576\text{ B} \le 2{,}032\text{ B}$` | `MAXALIGN(tlen) = 1,576 B ≤ 2,032 B` | Yes | No |
| 150 | `$\text{MAXALIGN}(t_{\text{len}}) = 3{,}112\text{ B}$` | `MAXALIGN(tlen) = 3,112 B` | Yes | No |
| 151 | `$\text{Recall@10}_{\text{conv}}(S, q) = \|S \cap R_{\text{ref}}(q)\| / 10$` | `Recall@10conv(S, q) = \|S ∩ Rref(q)\| / 10` | Yes | No |
| 152 | `$\text{Recall@10}_{\text{tie}}(S, q; \tau) = (\|S \cap B_\tau(q)\| + \min(\|S \cap T_\tau(q)\|, r_\tau(q))) / 10$` | `Recall@10tie(S, q; τ) = (\|S ∩ Bτ(q)\| + min(\|S ∩ Tτ(q)\|, rτ(q))) / 10` | Yes | No |
| 153 | `$\text{VARSIZE} = 4d + 8 = 3{,}080\text{ B}$` | `VARSIZE = 4d + 8 = 3,080 B` | No | No |
| 154 | `$\text{VARSIZE}(d) = 8 + \text{bytes\_per\_elem}\cdot d$` | `VARSIZE(d) = 8 + bytes_per_elem· d` | No | No |
| 155 | `$\text{entryLevel}(50{,}000) = \lfloor \ln 50{,}000 / \ln 16 \rfloor = 3$` | `entryLevel(50,000) = ⌊ ln 50,000 / ln 16 ⌋ = 3` | No | No |
| 156 | `$\text{entryLevel}(N) = \lfloor \ln N / \ln m \rfloor$` | `entryLevel(N) = ⌊ ln N / ln m ⌋` | No | No |
| 157 | `$\text{indexTotalCost}_{\text{FP16}} = 1000.0 + 7.5075 = 1007.5075$` | `indexTotalCostFP16 = 1000.0 + 7.5075 = 1007.5075` | Yes | No |
| 158 | `$\text{indexTotalCost}_{\text{FP32}} = 1996.0 + 7.5075 = 2003.5075$` | `indexTotalCostFP32 = 1996.0 + 7.5075 = 2003.5075` | Yes | No |
| 159 | `$\text{numIndexPages} \approx 0.4985\,N = 24{,}925$` | `numIndexPages ≈ 0.4985 N = 24,925` | No | No |
| 160 | `$\text{pages\_fetched} = \lceil \min(T, 2TN/(2T+N)) \rceil$` | `pages_fetched = ⌈ min(T, 2TN/(2T+N)) ⌉` | No | No |
| 161 | `$\text{ratio} = 0.499493 < 0.50$` | `ratio = 0.499493 < 0.50` | No | No |
| 162 | `$\text{ratio} = 0.50$` | `ratio = 0.50` | No | No |
| 163 | `$\text{ratio} = 0.500041 \ge 0.50$` | `ratio = 0.500041 ≥ 0.50` | No | No |
| 164 | `$\text{ratio}(1{,}001) = 0.40572022$` | `ratio(1,001) = 0.40572022` | No | No |
| 165 | `$\text{ratio}(50{,}000) = 0.01267835$` | `ratio(50,000) = 0.01267835` | No | No |
| 166 | `$\text{ratio}(N)$` | `ratio(N)` | No | No |
| 167 | `$\text{ratio}(N) < 0.5$` | `ratio(N) < 0.5` | No | No |
| 168 | `$\text{ratio}(N) = (E_0 + 54.152441134 \ln N)/N$` | `ratio(N) = (E0 + 54.152441134 ln N)/N` | Yes | No |
| 169 | `$\text{ratio}(N) \ge 0.5$` | `ratio(N) ≥ 0.5` | No | No |
| 170 | `$\text{ratio}_{\text{cal}}$` | `ratiocal` | Yes | No |
| 171 | `$\text{ratio}_{\text{cal}} = 0.40572022$` | `ratiocal = 0.40572022` | Yes | No |
| 172 | `$\text{ratio}_{\text{cal}} = 0.40572022 < 0.5$` | `ratiocal = 0.40572022 < 0.5` | Yes | No |
| 173 | `$\text{relpages} \approx \lceil N/157 \rceil = 319 > \text{startupPages} = 316.01$` | `relpages ≈ ⌈ N/157 ⌉ = 319 > startupPages = 316.01` | No | No |
| 174 | `$\text{relpages} \cdot \text{seq\_page\_cost} + N(\text{cpu\_tuple\_cost} + \text{cpu\_operator\_cost})$` | `relpages · seq_page_cost + N(cpu_tuple_cost + cpu_operator_cost)` | No | No |
| 175 | `$\text{relpages}(N) \approx N / 157$` | `relpages(N) ≈ N / 157` | No | No |
| 176 | `$\text{startupPages} \cdot \text{random\_page\_cost}$` | `startupPages · random_page_cost` | No | No |
| 177 | `$\text{startupPages}(N) \approx 0.4985\,(48 + 54.152441\ln N)$` | `startupPages(N) ≈ 0.4985 (48 + 54.152441ln N)` | No | No |
| 178 | `$\text{startupPages}\cdot 4.0 - \text{relpages}\cdot 1.0$` | `startupPages· 4.0 - relpages· 1.0` | No | No |
| 179 | `$\text{toast\_index\_bytes} = 65{,}536\text{ B}$` | `toast_index_bytes = 65,536 B` | No | No |
| 180 | `$\text{toast\_table\_bytes} = 4{,}104{,}192\text{ B}$` | `toast_table_bytes = 4,104,192 B` | No | No |
| 181 | `$\text{toast\_total\_bytes} = 0 + 8{,}192 = 8{,}192\text{ B}$` | `toast_total_bytes = 0 + 8,192 = 8,192 B` | No | No |
| 182 | `$\text{toast\_total\_bytes} = \text{toast\_table\_bytes} + \text{toast\_index\_bytes} = 0 + 8{,}192 = 8{,}192\text{ B}$` | `toast_total_bytes = toast_table_bytes + toast_index_bytes = 0 + 8,192 = 8,192 B` | No | No |
| 183 | `$\text{toast\_total\_bytes} = \text{toast\_table\_bytes} + \text{toast\_index\_bytes} = 4{,}169{,}728\text{ B}$` | `toast_total_bytes = toast_table_bytes + toast_index_bytes = 4,169,728 B` | No | No |
| 184 | `$\to$` | `→` | No | No |
| 185 | `$d$` | `d` | No | No |
| 186 | `$d < \sim\!500$` | `d < ~500` | No | No |
| 187 | `$d = 1{,}024$` | `d = 1,024` | No | No |
| 188 | `$d = 1{,}536$` | `d = 1,536` | No | No |
| 189 | `$d = 384$` | `d = 384` | No | No |
| 190 | `$d = 512$` | `d = 512` | No | No |
| 191 | `$d = 768$` | `d = 768` | No | No |
| 192 | `$d > \sim\!1{,}000$` | `d > ~1,000` | No | No |
| 193 | `$d \approx 1{,}000$` | `d ≈ 1,000` | No | No |
| 194 | `$d \approx 500$` | `d ≈ 500` | No | No |
| 195 | `$d \ge 1{,}024$` | `d ≥ 1,024` | No | No |
| 196 | `$d \in \{384, 512, 768, 1{,}024, 1{,}536\}$` | `d ∈ {384, 512, 768, 1,024, 1,536}` | No | No |
| 197 | `$d_{\text{FP32}}(c, q)$` | `dFP32(c, q)` | Yes | No |
| 198 | `$df = 8$` | `df = 8` | No | No |
| 199 | `$ef_{\text{construction}} = 64$` | `efconstruction = 64` | Yes | No |
| 200 | `$ef_{\text{search}}$` | `efsearch` | Yes | No |
| 201 | `$ef_{\text{search}} = 40$` | `efsearch = 40` | Yes | No |
| 202 | `$m$` | `m` | No | No |
| 203 | `$m = 16$` | `m = 16` | No | No |
| 204 | `$m = 16, ef_{\text{construction}} = 64$` | `m = 16, efconstruction = 64` | Yes | No |
| 205 | `$m = 16, ef_{\text{construction}} = 64, ef_{\text{search}} = 40$` | `m = 16, efconstruction = 64, efsearch = 40` | Yes | No |
| 206 | `$m = 16, ef_{\text{search}} = 40$` | `m = 16, efsearch = 40` | Yes | No |
| 207 | `$n$` | `n` | No | No |
| 208 | `$n = 100$` | `n = 100` | No | No |
| 209 | `$n = 19$` | `n = 19` | No | No |
| 210 | `$n = 20$` | `n = 20` | No | No |
| 211 | `$n = 80$` | `n = 80` | No | No |
| 212 | `$n = 96$` | `n = 96` | No | No |
| 213 | `$n = 99$` | `n = 99` | No | No |
| 214 | `$p$` | `p` | No | No |
| 215 | `$p = 1.907 \times 10^{-6}$` | `p = 1.907 × 10-6` | No | Yes |
| 216 | `$p = 8.857 \times 10^{-5}, r = 0.8765$` | `p = 8.857 × 10-5, r = 0.8765` | No | Yes |
| 217 | `$p = 9.569 \times 10^{-5}$` | `p = 9.569 × 10-5` | No | Yes |
| 218 | `$p_{\text{adj}}$` | `padj` | Yes | No |
| 219 | `$p_{\text{adj}} = 0.0163$` | `padj = 0.0163` | Yes | No |
| 220 | `$p_{\text{adj}} = 0.2024$` | `padj = 0.2024` | Yes | No |
| 221 | `$p_{\text{adj}} = 2.45 \times 10^{-6}$` | `padj = 2.45 × 10-6` | Yes | Yes |
| 222 | `$q$` | `q` | No | No |
| 223 | `$r = 0.8723$` | `r = 0.8723` | No | No |
| 224 | `$r = 10 - 2 = 8$` | `r = 10 - 2 = 8` | No | No |
| 225 | `$r = \|z\|/\sqrt{20} = 0.8723$` | `r = \|z\|/√(20) = 0.8723` | No | No |
| 226 | `$r_\tau(q) = 10 - \|B_\tau(q)\|$` | `rτ(q) = 10 - \|Bτ(q)\|` | Yes | No |
| 227 | `$r_{\text{rb}}$` | `rrb` | Yes | No |
| 228 | `$r_{\text{rb}} = +1.0000$` | `rrb = +1.0000` | Yes | No |
| 229 | `$r_{\text{rb}} = -0.733$` | `rrb = -0.733` | Yes | No |
| 230 | `$t_{\text{len}}$` | `tlen` | Yes | No |
| 231 | `$t_{\text{len}} = 1{,}572\text{ B} \le 2{,}032\text{ B}$` | `tlen = 1,572 B ≤ 2,032 B` | Yes | No |
| 232 | `$t_{\text{len}} = 24 + 4 + 1{,}544 = 1{,}572\text{ B}$` | `tlen = 24 + 4 + 1,544 = 1,572 B` | Yes | No |
| 233 | `$t_{\text{len}} = 24 + 4 + 3{,}080 = 3{,}108\text{ B}$` | `tlen = 24 + 4 + 3,080 = 3,108 B` | Yes | No |
| 234 | `$t_{\text{len}} = 3{,}108\text{ B} > 2{,}032\text{ B}$` | `tlen = 3,108 B > 2,032 B` | Yes | No |
| 235 | `$t_{\text{len}}(d) = 28 + \text{VARSIZE}(d)$` | `tlen(d) = 28 + VARSIZE(d)` | Yes | No |
| 236 | `$z = (\|W - \mu_W\| - 0.5)/\sigma_W$` | `z = (\|W - μW\| - 0.5)/σW` | Yes | No |
| 237 | `$z = -3.9013$` | `z = -3.9013` | No | No |
| 238 | `$\|B\| = 2$` | `\|B\| = 2` | No | No |
| 239 | `$\|S\| = 10$` | `\|S\| = 10` | No | No |
| 240 | `$\|T\| = 28$` | `\|T\| = 28` | No | No |
| 241 | `$\|T\| > r$` | `\|T\| > r` | No | No |
