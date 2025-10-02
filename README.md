# ASF Sentinel-1 Dataset Toolkit

A toolkit for the ASF Sentinel-1 dataset.

## Features

- Search for Sentinel-1 granules in the ASF catalog
- Submit InSAR jobs
- Download the results
- Process and analyze InSAR timeseries data
- Visualize displacement and velocity with geographic coordinates

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/)
- Docker (for MintPy processing)
- [`gdal`](https://gdal.org/en/stable/download.html)

Sign up for `earthdata.nasa.gov` and get your credentials.

```bash
cp .env.example .env
UV_ENV_FILE=.env
```

## Complete InSAR Processing Pipeline

This is the complete workflow from raw data to visualization:

> If you already have a processed dataset, you can skip to Step 2.

### Step 1: Process InSAR Dataset

Strongly recommend using [ASF Search](https://search.asf.alaska.edu/) to search for desired SAR products. They offer geographic, baseline, and SBAS search tools to find the desired products.

After finding the desired products, you can use hyp3 on-demand processing on website. Once you have the products, go to Step 2 and download the products to your data directory.

> By above recommendation, `search.py` and `process.py` will be deprecated.

### Step 2: Download InSAR Products

Download the products to your data directory:

```bash
uv run main.py download --project-name your-project-name --output-dir data
```

### Step 3: Crop to Common Overlap

After downloading InSAR products, crop all GeoTIFF files to their common geographic overlap:

```bash
uv run main.py clip --data-dir data
```

This creates `*_clipped.tif` files that cover the same geographic extent, which is required for MintPy.

### Step 4: Run MintPy Analysis

Process the InSAR stack with MintPy to generate timeseries and velocity:

> **NOTE**: You need to enable CDS Access to download ERA5 data. See this notebook for details: [CDS Access](https://github.com/ASFOpenSARlab/opensarlab_MintPy_Recipe_Book/blob/main/2_CDS_Access.ipynb)

```bash
# Timeseries analysis
docker run --rm --platform linux/amd64 \
  -v $PWD:/home/mambauser \
  -v $HOME/.cdsapirc:/home/mambauser/.cdsapirc \
  ghcr.io/insarlab/mintpy:latest \
  smallbaselineApp.py mintpy/default.txt \
  --dir data

# Velocity analysis
docker run --rm --platform linux/amd64 \
  -v $PWD:/home/mambauser \
  ghcr.io/insarlab/mintpy:latest \
  timeseries2velocity.py data/timeseries.h5 \
  -o data/velocity.h5
```

**Configuration**: Edit `mintpy/default.txt` before running:
- Set `mintpy.troposphericDelay.method = no` to skip tropospheric correction (faster)
- Configure input file paths to point to your clipped GeoTIFF files
- Adjust processing parameters as needed

**Output files** (in `data/` directory):
- `timeseries.h5` - Displacement timeseries for each date
- `velocity.h5` - Mean velocity map (cm/year)
- `temporalCoherence.h5` - Quality metrics
- `pic/` - Generated plots and figures
- Other intermediate products

### Step 5: Visualize Results

Visualize displacement and velocity with geographic coordinates:

```bash
# Interactive timeseries viewer (default)
uv run main.py visualize data/timeseries.h5

# Plot velocity map
uv run main.py visualize data/velocity.h5

# Save velocity plot to file
uv run main.py visualize data/velocity.h5 --output velocity.png

# Custom title
uv run main.py visualize data/velocity.h5 --title "My Custom Title"
```

## Documentation

- [Useful References](docs/REFERENCE.md)
