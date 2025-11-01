# Atmospheric Metrology for Quantum Networks

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.xxxxxxx.svg)](https://doi.org/10.5281/zenodo.xxxxxxx)

This repository contains the complete dataset and analysis code for the research paper **"Atmospheric Metrology for Quantum Networks"**, which demonstrates precision environmental compensation for quantum networking applications using the 1762 nm transition of trapped barium ions.

## 📖 Abstract

Quantum networks utilizing atomic transitions face critical challenges in realistic environments where atmospheric phase noise rapidly degrades quantum coherence. This work establishes a wavelength-specific metrological framework demonstrating that environmental compensation is essential for practical quantum networking. Using quantum-referenced interferometry traceable to a single trapped ion, we analyze 89,106 measurements to determine the refractive index coefficients of air at 1762 nm with part-per-billion precision.

## 🚀 Key Features

- **Precision Refractometry**: Experimental determination of refractive index coefficients for air at 1762 nm
- **Environmental Compensation**: Physics-based phase noise suppression using environmental bookkeeping
- **Multi-Timescale Analysis**: Performance evaluation across quantum memory (15-day) and quantum gate (12-hour) timescales
- **Model Comparison**: Comprehensive comparison with established atmospheric models (Ciddor, Edlén, Mathar)
- **Open Data**: Complete synchronized dataset of environmental parameters and interferometric measurements

## 📊 Dataset

The dataset includes two main components:

### Training Dataset (89,106 measurements)
- Used for coefficient determination and model validation
- Covers temperature range: 15-35°C, humidity: 20-45%, pressure: 965-1000 hPa
- Includes synchronized measurements of temperature, humidity, pressure, and dual-wavelength interferometric data

### Validation Dataset (46,999 measurements)
- Independent dataset for performance evaluation
- 15-day continuous outdoor measurements
- Used to demonstrate noise suppression efficacy

### Data Format
Each CSV file contains:
- `time`: UTC timestamp
- `temperature`: Temperature in °C
- `humidity`: Relative humidity in %
- `pressure`: Atmospheric pressure in hPa  
- `n_1762`: Measured refractive index at 1762 nm
- `phase_measured`: Uncompensated phase in radians
- `phase_compensated`: Environmentally compensated phase

## 🛠️ Installation & Usage

### Prerequisites
```bash
pip install numpy pandas matplotlib scipy statsmodels seaborn
```

### Basic Usage
```python
import pandas as pd
import numpy as np
from analysis_functions import compare_refractive_index_models, plot_bootstrap_coefficient_distributions

# Load dataset
df = pd.read_csv('data/training_dataset.csv')

# Compare refractive index models
fig, stats = compare_refractive_index_models(wavelength=1762)

# Plot bootstrap coefficient distributions
fig, bootstrap_stats = plot_bootstrap_coefficient_distributions(results)
```

### Key Analysis Functions

#### 1. Refractive Index Model Comparison
```python
from model_comparison import compare_refractive_index_models

# Compare AcToMicS model with standard models
fig, statistics = compare_refractive_index_models(
    wavelength=1762,
    save_path='model_comparison.pdf'
)
```

#### 2. Phase Noise Compensation
```python
from phase_analysis import create_combined_figure

# Create comprehensive 2x4 analysis figure
fig, stats = create_combined_figure(
    df_long_term=df_15day,
    df_short_term=df_12hour,
    coefficients=coefficients,
    save_path='phase_analysis.pdf'
)
```

#### 3. Statistical Analysis
```python
from regression_analysis import perform_regression, plot_diagnostics

# Perform enhanced regression analysis
results = perform_regression(df, n_bootstrap=2000)

# Generate diagnostic plots
plot_diagnostics(results, df)
```

## 📈 Key Results

### Refractive Index Coefficients at 1762 nm
| Parameter | Coefficient | 95% CI |
|-----------|-------------|---------|
| Temperature (αₜ) | -8.940 × 10⁻⁷ | [-8.942, -8.938] × 10⁻⁷ |
| Humidity (αₕ) | -1.780 × 10⁻⁸ | [-1.796, -1.764] × 10⁻⁸ |
| Pressure (αₚ) | 2.569 × 10⁻⁷ | [2.557, 2.581] × 10⁻⁷ |

### Noise Suppression Performance
- **Long-term (15 days)**: 80.97% phase noise reduction (5.3× improvement)
- **Short-term (12 hours)**: 60.20% phase noise reduction (2.5× improvement)
- **Autocorrelation time**: Reduced from 5668s to 302s (long-term) and 560s to 1s (short-term)

## 📁 Repository Structure

```
├── data/
│   ├── training_dataset.csv          # 89,106 measurements for model training
│   ├── validation_dataset.csv        # 46,999 measurements for validation
│   └── decimated_1min_dataset.csv    # 1-minute cadence version
├── scripts/
│   ├── model_comparison.py           # Refractive index model comparison
│   ├── phase_analysis.py             # Phase noise compensation analysis
│   ├── regression_analysis.py        # Statistical regression functions
│   └── visualization.py              # Plotting utilities
├── figures/                          # Generated analysis figures
├── requirements.txt                  # Python dependencies
└── README.md                         # This file
```

## 🔬 Scientific Context

This work addresses the critical challenge of atmospheric phase noise in quantum networks, particularly for the 1762 nm transition of trapped barium ions. The research demonstrates:

1. **Wavelength-specific metrology** is essential near molecular resonances
2. **Environmental bookkeeping** provides deterministic phase noise suppression
3. **Multi-timescale optimization** enables both quantum memory and gate operations


## 📜 License

This project is dual-licensed under:

- **Code**: MIT License - See [LICENSE-CODE](LICENSE) for details
- **Data**: Creative Commons Attribution 4.0 International (CC BY 4.0) - See [LICENSE-DATA](LICENSE-CC-BY-4.0.txt) for details

## 🔗 Related Resources

- [Zenodo Data Repository](https://doi.org/10.5281/zenodo.xxxxxxx)
- [Qsim Group in Freiburg](https://www.qsim.uni-freiburg.de)
- [EU Quantum Flagship](https://qt.eu/)

---

*This research was supported by the European Research Council, Deutsche Forschungsgemeinschaft, QUSTEC Programme, and the Georg H. Endress Foundation.*
