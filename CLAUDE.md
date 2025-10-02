# ASF Sentinel-1 InSAR Toolkit

## Project Purpose

This toolkit processes Sentinel-1 Synthetic Aperture Radar (SAR) data to detect ground displacement using Interferometric SAR (InSAR) techniques.

## Workflow Overview

1. **Search & Discover**: Find Sentinel-1 granules from ASF catalog
2. **Process**: Submit InSAR processing jobs to ASF HyP3 service
3. **Download**: Retrieve processed InSAR products
4. **Clip**: Crop GeoTIFF files to common geographic overlap
5. **Analyze**: Generate displacement time-series and velocity maps
6. **Visualize**: View timeseries and velocity maps

Please refer to the [README.md](README.md) for more details.

## Project Structure

```
.
├── toolkit/          # Core processing modules
├── mintpy/          # MintPy configuration files
├── data/            # Downloaded InSAR products
└── main.py          # CLI entry point
```

## Python Development Guidelines

### Package Management
Always use `uv` for Python package management:
- `uv run python script.py` instead of `python script.py`
- `uv add <package>` instead of `pip install <package>`
- `uv remove <package>` instead of `pip uninstall <package>`
- `uv sync` to sync dependencies
