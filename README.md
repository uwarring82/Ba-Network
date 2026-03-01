# Precision Refractive Index Measurement at 1762 nm

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18800166.svg)](https://doi.org/10.5281/zenodo.18800166)

This repository contains the complete dataset and analysis code for the research paper **"Precision Refractive Index Measurement at 1762 nm"**, which demonstrates precision refractive index measurement using dual-wavelength interferometry traceable to quantum frequency standards.

## 📖 Abstract

This work establishes a wavelength-specific metrological framework for precision refractive index measurement at 1762 nm. Using quantum-referenced interferometry traceable to a single trapped barium ion, we analyze 149,243 measurements to determine the refractive index coefficients of air with part-per-billion precision. The study identifies a 17.2% enhanced humidity sensitivity at 1762 nm relative to standard atmospheric models, consistent with Kramers-Kronig predictions near water absorption lines.

## 🚀 Key Features

- **Precision Refractometry**: Experimental determination of refractive index coefficients for air at 1762 nm with part-per-billion (ppb) precision
- **Quantum-Traceable Metrology**: Direct linkage to atomic frequency standards enables SI-traceable environmental monitoring
- **Enhanced Humidity Sensitivity**: Identification of 17.2% enhanced humidity sensitivity at 1762 nm
- **Model Validation**: Comprehensive comparison with established atmospheric models (Ciddor, Edlén, Mathar)
- **Open Data**: Complete synchronized dataset of environmental parameters and interferometric measurements

## 📊 Dataset

The dataset includes 145784 synchronized measurements from January to August 2025, which includes synchronized measurements of temperature, humidity, pressure, and dual-wavelength interferometric data.

### Data Format
Each processed CSV file contains:
- `time`: UTC timestamp
- `temperature`: Temperature in °C
- `humidity`: Relative humidity in %
- `pressure`: Atmospheric pressure in hPa  
- `counts_ratio`: Interference pattern counts ratio
- `n_1762`: Measured refractive index at 1762 nm

## 📈 Key Results

### Refractive Index Coefficients at 1762 nm
| Parameter | Coefficient | HAC Standard Error | Precision |
|-----------|-------------|-------------------|-----------|
| Temperature (αₜ) | -8.8474 × 10⁻⁷ °C⁻¹ | 2.7967 × 10⁻¹⁰ | 0.28 ppb/°C |
| Humidity (αₕ) | -1.3152 × 10⁻⁸ %⁻¹ | 2.2435 × 10⁻¹⁰ | 0.22 ppb/% |
| Pressure (αₚ) | +2.5949 × 10⁻⁷ hPa⁻¹ | 1.8632 × 10⁻¹⁰ | 0.19 ppb/hPa |

### Model Performance
- **Model Fit**: R² = 0.996
- **Residual Precision**: σₙ = 1.837 × 10⁻⁷
- **Enhanced Humidity Sensitivity**: 17.2% relative to standard models (v.s. Mathar@1762nm: -1.122 × 10⁻⁸ %⁻¹)
- **Kramers-Kronig Prediction**: -1.4361 × 10⁻⁸ %⁻¹ (v.s. experimental -1.3152 × 10⁻⁸ %⁻¹)

### Bootstrap Confidence Intervals (95%)
- Temperature: [-8.8513, -8.8437] × 10⁻⁷ °C⁻¹
- Humidity: [-1.3464, -1.2859] × 10⁻⁸ %⁻¹
- Pressure: [2.5925, 2.5973] × 10⁻⁷ hPa⁻¹

## 📁 Repository Structure

```
zenodo/
├── README.md                  
├── LICENSE.txt                
├── CITATION.cff              
├── data/
│   ├── raw/
│   │   ├── interferometer/
│   │   │   └── counts_ratio_data_{date}.csv
│   │   └── environmental/
│   │       ├── humidity_data_{date}.csv
│   │       ├── temperature_data_{date}.csv
│   │       └── pressure_data_{date}.csv
│   ├── processed/
│   │   ├── training_data.csv
│   │   └── validation_data.csv
│   └── derived/
│       ├── figures/
│       │   ├── data_preview.pdf
│       │   ├── deviation_validation.pdf
│       │   └── kramers_kronig.pdf
│       └── models/
│           └── hitran
│               ├── H2O.data
│               └── H2O.header
├── code/
│   ├── data_processing/
│   │   └── preprocess_data.ipynb
│   ├── analysis/              
│   │   ├── refractive_index_model.ipynb
│   │   ├── model_validation.ipynb
│   │   ├── regression_results.json
│   │   └── kramers_kronig.ipynb
│   └── models/              
│       ├── hitran
│       │   └── hapi.py
│       ├── mathar
│       │   └── Mathar2007.py
│       └── nist
│           └── refractive_index.py
└── manuscript/
    ├── manuscript.tex                  
    └── manuscript.pdf   
```

## 🔬 Scientific Context

This work addresses the critical need for wavelength-specific refractive index measurements, particularly at 1762 nm where standard atmospheric models show limitations. The research demonstrates:

1. **Part-per-billion precision** in environmental coefficient determination
2. **Enhanced humidity sensitivity** near water absorption lines at 1762 nm
3. **Quantum-traceable metrology** enabling SI-traceable atmospheric monitoring
4. **Comprehensive validation** against independent datasets and theoretical predictions

## 📜 License

This project is dual-licensed under:

- **Code**: MIT License - See [LICENSE](LICENSE) for details
- **Data**: Creative Commons Attribution 4.0 International (CC BY 4.0) - See [LICENSE-CC-BY-4.0.txt](LICENSE-CC-BY-4.0.txt) for details

## 🔗 Related Resources

- [Zenodo Data Repository](https://doi.org/10.5281/zenodo.xxxxxxx)
- [Qsim Group in Freiburg](https://www.qsim.uni-freiburg.de)
- [EU Quantum Flagship](https://qt.eu/)

## 📧 Contact

- Wei Wu: wei.wu@physik.uni-freiburg.de
- Ulrich Warring: ulrich.warring@physik.uni-freiburg.de

---

*This research was supported by the European Research Council, Deutsche Forschungsgemeinschaft, QUSTEC Programme, and the Georg H. Endress Foundation.*
