# ASF Sentinel-1 InSAR Toolkit

## Project Purpose

This toolkit processes Sentinel-1 Synthetic Aperture Radar (SAR) data to detect ground displacement using Interferometric SAR (InSAR) techniques. It automates the complete workflow from data discovery to visualization:

1. **Search & Discover**: Find Sentinel-1 granules from the ASF catalog (recommended: use [ASF Search](https://search.asf.alaska.edu/))
2. **Process**: Submit InSAR processing jobs to ASF HyP3 service (optional: use web interface)
3. **Download**: Retrieve processed InSAR products with concurrent downloads
4. **Clip**: Crop GeoTIFF files to common geographic overlap
5. **MintPy**: Generate displacement time-series and velocity maps (Docker-based)
6. **Visualize**: Interactive timeseries viewer and velocity maps with geographic coordinates

> **Note**: `search.py` and `process.py` will be deprecated in favor of using ASF Search web interface for better SBAS and baseline search tools.

## Project Structure

```
.
├── toolkit/               # Core toolkit modules
│   ├── search.py         # ASF catalog search for Sentinel-1 granules
│   ├── process.py        # InSAR job submission (HyP3)
│   ├── hyp3.py           # HyP3 client for job management and downloads
│   └── insar.py          # GeoTIFF clipping and visualization tools
├── main.py               # CLI entry point (process, download, clip, visualize)
├── mintpy/               # MintPy configuration files
│   └── default.txt       # smallbaselineApp.py config template
├── data/                 # Downloaded InSAR products (GeoTIFF)
├── .env.example          # Environment variables template (ASF credentials)
├── Makefile              # Developer convenience commands
└── pyproject.toml        # Python dependencies (uv)
```

## CLI Commands

The toolkit provides 4 main commands via `main.py`:

### 1. Process (Search + Submit InSAR Jobs)
```bash
uv run main.py process <reference_id> \
  [--start START_DATE] \
  [--end END_DATE] \
  [--project-name NAME] \
  [--output-dir DIR] \
  [--no-download] \
  [--dry-run] \
  [--water-mask]
```

### 2. Download (Retrieve HyP3 Products)
```bash
uv run main.py download \
  --project-name <name> \
  [--output-dir data] \
  [--max-workers 10]
```

### 3. Clip (Crop to Common Overlap)
```bash
uv run main.py clip [--data-dir data]
```

### 4. Visualize (Timeseries/Velocity)
```bash
# Interactive timeseries viewer
uv run main.py visualize data/timeseries.h5

# Velocity map
uv run main.py visualize data/velocity.h5 [--output velocity.png] [--title "Custom Title"]
```

## Development Commands

```bash
# Format code
make format  # or: uv run ruff format

# Install/manage dependencies
uv add <package>
uv remove <package>
uv sync
```

## Key Features

### HyP3 Client (`toolkit/hyp3.py`)
- Concurrent downloads with configurable max workers (default: 10)
- Progress tracking with tqdm
- Error handling and retry logic
- Job discovery by project name

### InSAR Processing (`toolkit/insar.py`)
- **Clipping**: Crop GeoTIFFs to common geographic overlap for MintPy
- **Visualization**:
  - Interactive timeseries viewer with slider
  - Velocity map plotting with geographic coordinates
  - UTM to lat/lon coordinate transformation
  - Reference point marking and coordinate grid display

### Processing Options (`toolkit/process.py`)
- Water mask support (`--water-mask` flag)
- Configurable looks (default: 10x2 for better resolution)
- Wrapped phase, LOS displacement, and displacement maps
- Dry-run mode for testing

## Python Development Guidelines

### Package Management
Always use `uv` for Python package management:
- `uv run python script.py` instead of `python script.py`
- `uv add <package>` instead of `pip install <package>`
- `uv remove <package>` instead of `pip uninstall <package>`
- `uv sync` to sync dependencies

### Prerequisites
- `uv` - Python package manager
- `gdal` - Geospatial data processing
- Docker - For MintPy processing
- ASF Earthdata credentials (set in `.env`)
