# Precision Refractive Index Measurement at 1762 nm

## Dataset Description

- **Title**: Refractive index measurements at 1762 nm with dual-wavelength interferometry
- **Authors**: Wei Wu, Tobias Schaetz, Ulrich Warring
- **DOI**: 10.5281/zenodo.xxxxx
- **Publication Date**: 2026
- **License**: CC BY 4.0

## Contents

1. Raw interferometric and environmental sensor data
2. Processed refractive index calculations
3. Statistical analysis scripts
4. Model parameters and uncertainty analysis
5. Figure generation code

## Data Collection Methods

- Dual-wavelength Michelson interferometer (780 nm reference, 1762 nm probe)
- BME280 environmental sensors (T, H, P)
- GPS-disciplined timing synchronization
- Measurement period: [Start Date] to [End Date]

## File Structure

```html
refractive_index_1762nm_v1.0/
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
└── paper/                     
    ├── manuscript.pdf         
    └── bulletpoint_list.pdf   
```

## Citation

Please cite: [Your Paper Reference] and this dataset: [Zenodo DOI]

## Contact

wei.wu@physik.uni-freiburg.de
ulrich.warring@physik.uni-freiburg.de
