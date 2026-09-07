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

- **full_data = training (2024-12-30 → 2025-08-05) + validation (2025-08-05 → 2025-08-21)** built by `code/data_processing/preprocess_data.ipynb`.
- Actual first/last timestamps of `full_data.csv`: **2025-01-01 00:06:26 UTC → 2025-08-20 20:37:37 UTC** (231 calendar days). Rows before 2025-01-01 carry no valid synchronized data.
- Columns: `time, counts_ratio, humidity, temperature, pressure, n_1762`.

## 2. Retention / selection rules

- **Interferometer valid-range filter** (`preprocess_data.ipynb`):
  `counts_ratio ∈ [2.2584867, 3]` — outside this range rows are dropped (laser-unlock rejection). Note: the lower bound 2.2584867 is the minimum value present in the retained data (the full retained range is [2.2584867, 2.2584884]); it is a data-defined boundary, not an independently computed physical threshold. The upper bound 3 is a wide safety margin; no retained value approaches it.
- Environmental sensor data are merged to the interferometer timestamps; no additional row-level environmental filter is applied.
- "Retained observations" = the 145,784 synchronized rows of `full_data.csv`.

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

Bootstrap settings across notebooks: moving-block bootstrap, **block length L=156 samples** (row-lag 1/e ≈ 78–100; see §5), **B=5000**, RNG seed 42. KK quadrature: **limit=2000, epsrel=1e-9**.

## 5. Block-length note (open item)

- Segment-internal row-lag ACF gives a 1/e crossing at lag ≈ 100 → L = 200.
- Residual autocorrelation contains a diurnal lobe (ρ ≈ 0.14 at 20–22 h); block-bootstrap SEs grow 4–7× from L=156 (0.6 h) to L≈1–2 days.
- The adopted block length for reported statistical uncertainties is **pending decision** (Ulrich); see `06_statistical_robustness.ipynb`. Current SM S1b values use L=156 and are marked for revision once the choice is made.

## 6. Environment

To be filled by the author (run once in the analysis environment):

```
python --version
pip list | grep -Ei 'pandas|numpy|statsmodels|scipy|matplotlib'
```

Notes:
- SciPy `quad` default subinterval limit (50) does **not** converge for the KK integral; all KK values require `limit=2000` (identical for epsrel 1e-6 and 1e-9).
- hapi (HITRAN API) version affects the line list; the fetched H2O partition is stored in `data/derived/models/hitran/`.

## 7. Manuscript ↔ code cross-references

| Manuscript/SM item | Producing notebook |
|---|---|
| Table I (coefficients, u_stat) | 01, 03 |
| SM Table S1a/S1b | 03 |
| SM Table S2 (same-condition Δα) | 01 |
| SM Table S5 (KK) | 04 |
| SM S0 (temporal coverage) | 05 |
| Results statistics (mean conditions) | 00, 05 |
| Statistical robustness text (SM S1) | 06 (pending block-length decision) |
