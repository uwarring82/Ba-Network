# Provenance Record — NS10657 v2.0 Analysis

**Date:** 2026-09-07
**Purpose:** Snapshot of data, code, environment, and selection rules behind all numbers reported in the revised manuscript and Zenodo v2.0 package.

---

## 1. Data snapshot

| File | Observations | Rows (incl. header) | Size | SHA-256 (first 16 hex) |
|---|---|---|---|---|
| `data/processed/full_data.csv` | **145,784** | 145,786 | 17.0 MB | `43cd465deda7f6dd` |
| `data/processed/training_data.csv` | 108,346 | 108,348 | 12.6 MB | `4d5efbbac5934b04` |
| `data/processed/validation_data.csv` | 40,897 | 40,899 | 4.8 MB | `9b26d3e65c9cc4c0` |

- **full_data = training (2025-01-01 → 2025-08-05) + validation (2025-08-05 → 2025-08-20)** built by `code/data_processing/preprocess_data.ipynb`.
- **The documented train/validation split is not disjoint (confirmed by an exact join).** An exact join on the `time` column of the two released files gives **3,459 shared timestamps, all on the boundary day 2025-08-05** (no other date), consistent with the arithmetic identity 108,346 + 40,897 − 3,459 = 145,784 = `full_data.csv`. The split is therefore not temporally disjoint. **No result reported in the manuscript is computed as a temporally held-out validation**, and no reported result uses the overlapping observations as a hold-out. The only out-of-sample check is the within-campaign blocked cross-validation of notebook 01, whose blocks span the whole campaign and are assigned to folds at random; the manuscript labels it as an internal consistency check. Recovered result: `audit/NS10657_train_validation_timestamp_join.json`. **Machine-checked (`p2_checks.py` C1, 2026-09-27, PASS):** n_training = 108,346, n_validation = 40,897, n_union = 145,784 = full; n_shared = 3,459, all on 2025-08-05; the arithmetic gap equals the shared-timestamp count. Record: `audit/NS10657_p2_checks_C1_C4.json`.
- **Packaging note (resolved).** `preprocess_data.ipynb` was present only in the v1.0 package; it has now been copied into `v2.0/code/data_processing/` (identical file). No v2.0 analysis notebook regenerates `full_data.csv`, so this notebook remains the only record of how the processed dataset is constructed.
- Actual first/last timestamps of `full_data.csv`: **2025-01-01 00:06:26 UTC → 2025-08-20 20:37:37 UTC** (231 calendar days). Rows before 2025-01-01 carry no valid synchronized data.
- Columns: `time, counts_ratio, humidity, temperature, pressure, n_1762`.

## 2. Retention / selection rules

- **Interferometer valid-range filter** (`preprocess_data.ipynb`):
  `counts_ratio ∈ [2.2584867, 3]` — outside this range rows are dropped (laser-unlock rejection). Note: the lower bound 2.2584867 is the minimum value present in the retained data (the full retained range is [2.2584867, 2.2584884]); it is a data-defined boundary, not an independently computed physical threshold. The upper bound 3 is a wide safety margin; no retained value approaches it.
- Environmental sensor data are merged to the interferometer timestamps; no additional row-level environmental filter is applied.
- "Retained observations" = the 145,784 synchronized rows of `full_data.csv`.
- **Quantitative items — status.** (i) Retention window, **resolved as a quantified limitation.** The rows below the window are removed by the acceptance step, but the raw data are released with the dataset, so their distribution can be characterised directly: `p2_checks.py` C2 found 11,147 of 156,931 counter rows (7.1%) dropped, all of them just below the lower bound (values in [2.2584858, 2.2584867)) and none above the upper bound; the dropped rows span the campaign (Jan 2001, Feb 11, Mar 1, Jun 256, Jul 2640, Aug 6238) and their environmental distributions resemble the retained set (median T 28.8 vs 29.4 °C, RH 31.2 vs 29.7 %, P 982.7 vs 987.3 hPa), with no dropped row above 80 % RH. The influence of the data-defined lower bound is additionally quantified by a trimming sensitivity on the retained rows: the ratio is essentially uncorrelated with the environmental state (|r| ≤ 0.033), and removing the lowest 0.5–10% of retained ratio values changes α_H by at most 4.2% (≈5.5×10⁻¹⁰), below its statistical standard error (1.16×10⁻⁹). This trimming test constrains only additional rejection within the retained sample; it does not exclude a bias from the original acceptance cut, and the original rationale for the lower bound is not documented. Details in the SM, Sec. S1b "Retention-window sensitivity". (ii) Counter–sensor time mismatch, **quantified.** The series are merged with `merge_asof(direction='nearest')`; the nearest-neighbour matching distance |Δt| has a median of 0.41 s, a 95th percentile of 4.3 s and a maximum of 458 s, with 1.5% of rows above 10 s and 1.3×10⁻⁴ above 60 s (`p2_checks.py` C3); the environmental change over the median window is below 0.03 °C (SM Sec. S1b). (iii) Constant-anchor-offset check, **completed.** With `n_1762 = (f_780/f_1762) * n_780 / R(t)` and a constant offset K applied to the 780 nm channel (i.e. `K / R(t)` in raw count space), the term contributes 5.9×10⁻¹⁰ to Δα_H and does not remove the discrepancy (notebook 10; `p2_checks.py` C3–C4). **`p2_checks.py` C4 (2026-09-27, PASS):** K = 5.2×10⁻⁶, peak-to-peak count-ratio-induced modulation δn = 3.9×10⁻¹² (std 1.0×10⁻¹²), i.e. 2.1×10⁻⁵ of the 1.84×10⁻⁷ residual scatter; the constant-anchor term is many orders of magnitude below the residual. Record: `audit/NS10657_p2_checks_C1_C4.json`.

## 3. Statistics provenance (mean conditions)

| Quoted statistic | Value | Origin | Status |
|---|---|---|---|
| Mean T (retained obs) | 28.87 °C | `full_data.csv`, mean over 145,784 rows | Reported in manuscript |
| Mean RH (retained obs) | 30.23 % | same | Reported |
| Mean P (retained obs) | 986.40 hPa | same | Reported |
| Mean T (time-weighted) | 25.64 °C | notebook 05, time-weighted over segments | Reported |
| Mean T (full raw record) | 23.68 °C | all raw environmental temperature data | For provenance only |
| **Old 24.7 °C** | 24.6896 °C | mean of raw environmental T from **2025-02-21 onward**, computed while acquisition ongoing | **Retracted** (stale subset) |
| Old 31.2 % / 982.3 hPa | — | same early raw subset | **Retracted** |

## 4. Code snapshot (SHA-256 first 16 hex)

`code/analysis/` (v2.0):

| Notebook | SHA-256 | Role |
|---|---|---|
| `00_descriptive_statistics.ipynb` | `da804a3f9fea0705` | campaign statistics, mean conditions |
| `01_same_condition_mathar_comparison.ipynb` | `3538411e04b2aa89` | Task 1: same-condition Mathar surrogate comparison |
| `02_offset_fair_improvement.ipynb` | `1699f2ab4e0ff6e8` | Task 2: offset-fair improvement |
| `03_uncertainty_budget_audit.ipynb` | `222a9dfa11f48240` | Task 4: uncertainty budget (SM S1a/S1b) |
| `04_kramers_kronig_mean_conditions.ipynb` | `a1282c4987ecaac2` | KK at mean conditions, converged quadrature (limit=2000) |
| `05_time_coverage.ipynb` | `0c443ebf9cea7bc9` | temporal coverage, monthly table, time-weighted means |
| `06_statistical_robustness.ipynb` | `478e04c7f3deab98` | physical-time ACF, diurnal lobe, block-length sensitivity |

`code/models/` (v2.0):

| File | SHA-256 |
|---|---|
| `mathar/Mathar2007.py` | `426fa58d26270919` |
| `nist/refractive_index.py` | `e21246a32fe60256` |
| `hitran/hapi.py` | `e12665086c38f80d` |

Bootstrap settings across notebooks: moving-block bootstrap over **physical-time blocks** (durations 0.56 / 7.17 / 24 / 48 h, built inside continuous segments; shared implementation in `code/analysis/physical_blocks.py`), **B=5000**, RNG seed 42. No nominal block length is adopted (see §5). KK quadrature: **limit=2000, epsrel=1e-9**.

## 5. Block duration for the uncertainties (resolved: no nominal value)

- The residual ACF decays to 1/e at a row lag of about 78–100 samples, but it retains a positive diurnal lobe (ρ ≈ 0.14 at 20–22 h). No single decorrelation scale therefore describes the full dependence, and a block length derived from the 1/e crossing (twice the lag) is **not** adopted as a decision rule.
- The previously reported **row-block length L = 156 samples is withdrawn.** Row blocks of 156 samples could straddle the 111-day gap in the campaign, and the earlier conversion of 156 rows into a duration used a global 12.9 s cadence whereas the mean within-segment interval is 21.1 s (median interval 12.9 s). Row counts and durations are no longer inter-converted.
- Reported instead: moving-block bootstrap SEs over physical-time blocks, duration swept 0.56–48 h, with the coverage fraction of the block pool given for each duration (SM Table S1c). The L = 156 row-block SEs are a *lower* bound on that sweep (1.41, 1.15 and 0.99 ×10⁻⁹ for α_T, α_H, α_P).
- For the record: the campaign is split into continuous segments by gaps longer than 2 h; the largest gap is 111 days and no block crosses a gap.

## 5b. Combined uncertainty for the coefficients (retracted)

- The earlier `u_syst`, `u_tot` and `U(k=2)` columns of SM Table S1b are **retracted**. They merged the sensitivity of the paired coefficient *difference* (notebook 09) with the statistical uncertainty of the measured *coefficient*, which requires a specified and propagated joint probability model over the three sensor channels that is not available.
- Deterministic gain–offset envelopes and statistical uncertainties are reported separately. The earlier unsupported combined numbers are not restored in any form.

## 5c. Frequency constants and the documented-value difference (K provenance)

- The measurement equation uses the two optical frequencies fixed by atomic references: **f_1762 = 170.126432 THz** and **f_Rb = 384.2281145 THz**. Their ratio, the constant actually used in processing, is **2.2584857**.
- The documented ratio obtained from the rounded wavelengths (1762.17 / 780.24 nm) is 2.2584974. The difference from the constant used is **−5.17 ppm**.
- This is a reporting-convention difference, **not a processing discrepancy**: the rounded wavelengths never enter the computation, which uses the frequency constants above, and the recovered ratio equals 2.2584857 exactly. Rounding in the documentation is therefore not evidence that such an error entered the calculation.
- No numerical action remains. The only outstanding item is an optional cross-check of the two frequency constants against the laboratory frequency records; it is not needed to reconcile the numbers.
- **780 nm lock provenance (added 2026-09-27):** the 780 nm laser is locked to the ⁸⁷Rb D₂ **F = 2 → F′ = 1,3 crossover** line at **384.2279034069709 THz**; a double-pass acousto-optic modulator then shifts the light used for the measurement to **384.2281145 THz** (AOM shift +211.093 MHz). The `f_Rb = 384.2281145 THz` used in processing is the post-AOM frequency.
- **Correction of the 384 kHz figure:** earlier drafts quoted a 384 kHz frequency uncertainty for the 780 nm reference. This was a **copy error** and is withdrawn. The lock linewidth is ≈100 kHz and the long-term frequency uncertainty is <1 MHz. Propagated as a fractional wavelength uncertainty (δn ≈ n·δν/ν), this bounds the refractive-index contribution at **δn < 2.6×10⁻⁹** (a bound, not a standard uncertainty).
- **Cross-check of the lock point (added 2026-10-03):** the crossover frequency agrees with the hyperfine-level calculation for the ⁸⁷Rb D₂ F = 2 → F′ = 1,3 crossover. Adding the AOM shift (211.1 MHz) places the frequency used for the measurement approximately **0.70 MHz below the F = 2 → F′ = 3 transition**; this is recorded as a consistency check on the lock point.
- **Laboratory records:** the lock point is the ⁸⁷Rb D₂ **F = 2 → F′ = 1,3 crossover**; the double-pass acousto-optic modulator is driven at **105.5 MHz** (211.1 MHz round trip); and the **< 1 MHz** long-term bound was obtained from a **HighFinesse wavemeter recording of the locked laser over three hours**. The **1762 nm** reference is the ¹³⁸Ba⁺ **6S₁/₂ (m_J = 1/2) → 5D₅/₂ (m_J = 3/2)** transition. (Logbook entries to be cited in the manuscript.)
- **Rounded wavelengths:** the documented rounded wavelengths are taken from the literature rather than from this work: 780.24 nm from the ⁸⁷Rb D₂ line data (Steck, *Rubidium 87 D Line Data*, \texttt{http://steck.us/alkalidata}) and 1762.17 nm from arXiv:1906.09150.

## 6. Environment

To be filled by the author (run once in the analysis environment):

```
/opt/homebrew/bin/python3.11 --version
/opt/homebrew/bin/python3.11 -m pip list | grep -Ei 'pandas|numpy|statsmodels|scipy|matplotlib'
```

Notes:
- The notebooks require **Python 3.11** with numpy/pandas/scipy/statsmodels/matplotlib. The system `python3` on this machine is 3.9.6 and does not have those packages.
- Plot-producing notebooks need `MPLCONFIGDIR=/tmp/mplcfg` to be writable in the analysis environment.
- SciPy `quad` default subinterval limit (50) does **not** converge for the KK integral; all KK values require `limit=2000` (identical for epsrel 1e-6 and 1e-9).
- hapi (HITRAN API) version affects the line list; the fetched H2O partition is stored in `data/derived/models/hitran/`.
- `code/analysis/physical_blocks.py` is the single shared implementation of the physical-time block construction used by notebooks 01, 02, 03, 06 and 07.

## 7. Manuscript ↔ code cross-references

| Manuscript/SM item | Producing notebook |
|---|---|
| Table I (coefficients; statistical column = HAC lag 156) | 01, 03 |
| SM Table S1a (absolute n) | 03 |
| SM Table S1b (coefficients; deterministic envelopes only) | 03, 09 |
| SM Table S1c (block-duration sensitivity with coverage) | 06 |
| SM Table S2 (same-condition Δα) | 01 |
| SM Table S4a–S4c / S5 (evidence grading) | 11 |
| SM Table S5 (KK) | 04 |
| SM S0 (temporal coverage) | 05 |
| Results statistics (mean conditions) | 00, 05 |
| Statistical robustness text (SM S1) | 06 (block-duration sweep; no nominal duration) |
