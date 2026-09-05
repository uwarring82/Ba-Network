# Quantum-Referenced Refractive-Index Measurement of Air at 1762 nm

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18800166.svg)](https://doi.org/10.5281/zenodo.18800166)

This repository contains the synchronized dataset and analysis code for the research paper **"Quantum-referenced refractive-index calibration of air at 1762 nm for environmental phase compensation in quantum optical interfaces"**. The refractive index of air at 1762 nm — the clock transition wavelength of ¹³⁸Ba⁺ — is measured with a dual-wavelength Michelson interferometer whose 1762 nm probe laser is referenced to a single trapped barium ion.

## 📖 Abstract

We report an atom-frequency-referenced measurement of the refractive index of air at 1762 nm over a campaign spanning eight months. A dual-wavelength Michelson interferometer referenced to a single trapped ¹³⁸Ba⁺ ion recorded differential phase accumulation together
with co-located environmental sensors, yielding 145,784 synchronized measurements. The data provide the environmental coefficients ∂n/∂X for temperature, relative humidity, and pressure. Evaluated against the Mathar model on the identical observed conditions, the measured temperature and pressure coefficients agree to within 0.35 % and 0.93 %, respectively; the measured humidity coefficient is smaller in magnitude than the same-condition Mathar surrogate by 24.8 %. This humidity difference is statistically significant in the full dataset but not within the model validity range, and its magnitude is spanned by the gain uncertainty of the humidity sensor; it is reported as an unresolved systematic. The raw Mathar residual is dominated by a static offset (1.166 × 10⁻⁶ in refractive index); after this offset is subtracted, the residuals of the empirical model and the Mathar model agree within about 5 %. The dataset is made openly available.

## 🚀 Key Features

- **Atom-referenced refractometry**: refractive-index coefficients of air at 1762 nm measured with a probe laser referenced to a single trapped ¹³⁸Ba⁺ ion
- **Long-duration campaign dataset**: 145,784 synchronized measurements spanning eight months (January – August 2025)
- **Same-condition model comparison**: reproducible protocol comparing measured coefficients with the Mathar model on identical (T, H, P) rows
- **Open Data**: full synchronized dataset of environmental parameters and interferometric measurements

## 📊 Dataset

The synchronized dataset contains 145,784 measurements collected from January to August 2025 at a site in Freiburg, Germany (observed ranges: temperature 17.5–34.6 °C, relative humidity 18.9–45.3 %, pressure 964.6–1006.8 hPa). The sample is not continuous: gaps arise from ion reloading and interferometer realignment, and the retained observations are weighted toward the warmer months of the campaign.

### Data Format
Each processed CSV file contains:
- `time`: UTC timestamp
- `temperature`: Temperature in °C
- `humidity`: Relative humidity in %
- `pressure`: Atmospheric pressure in hPa
- `counts_ratio`: Dual-wavelength interference fringe-count ratio
- `n_1762`: Refractive index at 1762 nm derived from the differential phase measurement

### Files
- `data/processed/full_data.csv`: complete synchronized dataset (145,784 rows, Jan 1 – Aug 20, 2025)
- `data/processed/training_data.csv`: Jan 1 – Aug 5, 2025 (108,346 rows)
- `data/processed/validation_data.csv`: Aug 5 – Aug 20, 2025 (40,897 rows)

## 📈 Key Results

### Environmental coefficients at 1762 nm
| Parameter | Coefficient | Bootstrap SE (L=156, B=5000) |
|-----------|-------------|------------------------------|
| Temperature (α_T) | −8.8474 × 10⁻⁷ K⁻¹ | 1.41 × 10⁻⁹ |
| Humidity (α_H) | −1.3152 × 10⁻⁸ %⁻¹ | 1.15 × 10⁻⁹ |
| Pressure (α_P) | +2.5949 × 10⁻⁷ hPa⁻¹ | 9.85 × 10⁻¹⁰ |

The bootstrap standard errors are cross-checked against HAC standard errors (lag 156); the two agree within 3 %. Systematic contributions from the BME280 sensor gain bounds are documented in the Supplemental Material.

### Same-condition comparison with the Mathar model
The Mathar formulation is evaluated at the identical observed (T, H, P) rows and fitted with the same linear surrogate model, so that both fits share the same design matrix:

| Parameter | This work | Mathar surrogate | Difference |
|-----------|-----------|------------------|------------|
| α_T | −8.8474 × 10⁻⁷ K⁻¹ | −8.8164 × 10⁻⁷ K⁻¹ | −0.35 % |
| α_H | −1.3152 × 10⁻⁸ %⁻¹ | −1.7486 × 10⁻⁸ %⁻¹ | +24.8 % (measured smaller) |
| α_P | +2.5949 × 10⁻⁷ hPa⁻¹ | +2.5710 × 10⁻⁷ hPa⁻¹ | +0.93 % |

The humidity difference is statistically significant in the full campaign but not within the Mathar validity domain (10–25 °C). Its direction is opposite to the sign expected from water-vapor dispersion, and its magnitude is spanned by the BME280 humidity-sensor gain uncertainty; it is reported as an unresolved systematic pending an independently calibrated humidity measurement. A Kramers-Kronig evaluation of the HITRAN2020 water-vapor spectrum at the mean campaign conditions yields a coefficient of order 10⁻⁸ %⁻¹ without enhancement over the broadband model.

### Residual analysis
- Empirical model residual standard deviation: σ_n = 1.84 × 10⁻⁷ (R² = 0.996)
- Mathar root-mean-square residual: 1.18 × 10⁻⁶, dominated by a static offset of 1.166 × 10⁻⁶ (17.46 rad over the 4.2 m round-trip path)
- After subtracting the offset: residual standard deviation 1.93 × 10⁻⁷; the empirical model improves on the offset-subtracted model by 4.9 % in amplitude and 9.5 % in variance

## 📁 Repository Structure

```
├── README.md
├── LICENSE.txt                  # CC BY 4.0 (data)
├── metadata.json
├── data/
│   ├── raw/
│   │   ├── interferometer/      # counts_ratio_data_{date}.csv
│   │   └── environmental/       # temperature/humidity/pressure data
│   ├── processed/
│   │   ├── full_data.csv
│   │   ├── training_data.csv
│   │   └── validation_data.csv
│   └── derived/
│       ├── figures/
│       └── models/hitran/
├── code/
│   ├── data_processing/
│   │   └── preprocess_data.ipynb
│   ├── analysis/
│   │   ├── 00_descriptive_statistics.ipynb
│   │   ├── 01_same_condition_mathar_comparison.ipynb
│   │   ├── 02_offset_fair_improvement.ipynb
│   │   ├── 03_uncertainty_budget_audit.ipynb
│   │   └── 04_kramers_kronig_mean_conditions.ipynb
│   └── models/                  # Mathar2007, NIST Ciddor, HITRAN HAPI
└── manuscript/
    ├── main.tex
    ├── supplemental_material.tex
    └── reference.bib
```

The analysis notebooks reproduce every number reported in the manuscript and its Supplemental Material: block length L = 156 samples (twice the residual ACF 1/e lag), B = 5000 bootstrap replications, random seed 42.

## 🔬 Reproducibility Notes

- All analysis notebooks read `data/processed/full_data.csv` and import the model modules under `code/models/`.
- A revised analysis of the submitted results (same-condition Mathar comparison, offset-fair improvement, uncertainty-budget audit, and Kramers-Kronig evaluation at the true campaign mean conditions) is provided in the current release; see the manuscript revision history.
- The earlier public description of this dataset (v1) contained claims — a 17.2 % humidity enhancement, agreement with a Kramers-Kronig prediction, and SI traceability — that are retracted in the current version. The raw data are unchanged.

## 📜 License

- **Data**: Creative Commons Attribution 4.0 International (CC BY 4.0) — see `LICENSE.txt`
- **Code**: MIT License — see the code header for details

## 🔗 Related Resources

- [Zenodo record v1 (DOI 10.5281/zenodo.18800166)](https://doi.org/10.5281/zenodo.18800166)
- [Qsim Group in Freiburg](https://www.qsim.uni-freiburg.de)
- [EU Quantum Flagship](https://qt.eu/)

## 📧 Contact

- Wei Wu: wei.wu@physik.uni-freiburg.de
- Ulrich Warring: ulrich.warring@physik.uni-freiburg.de

---

*This research was supported by the European Research Council, Deutsche Forschungsgemeinschaft, QUSTEC Programme, and the Georg H. Endress Foundation.*
