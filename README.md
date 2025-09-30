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

## Complete InSAR Processing Pipeline

This is the complete workflow from raw data to visualization:

> If you already have a processed dataset, you can skip to Step 2.

### Step 1: Process and Download InSAR Dataset

[ASF](https://search.asf.alaska.edu/)

```bash
# Setup environment
cp .env.example .env

# Search for granules with known base granule
uv run toolkit/search.py

# Submit InSAR processing jobs
uv run --env-file .env main.py S1A_IW_SLC__1SSV_20141213T093112_20141213T093140_003699_004641_E1DC-SLC --start 2025-01-01 --project-name seoul-insar

# Process InSAR data using HyP3
uv run toolkit/process.py --project-name seoul-insar
```

This will submit InSAR jobs to HyP3 and download the results to your data directory.

### Step 2: Crop to Common Overlap

After downloading InSAR products, crop all GeoTIFF files to their common geographic overlap:

```bash
# Run analysis to find and crop to common overlap
uv run toolkit/analysis.py
```

This creates `*_clipped.tif` files that cover the same geographic extent, which is required for MintPy.

### Step 3: Run MintPy Analysis

Process the InSAR stack with MintPy to generate timeseries and velocity:

> **NOTE**: You need to enable CDS Access to download ERA5 data. See this notebook for details: [CDS Access](https://github.com/ASFOpenSARlab/opensarlab_MintPy_Recipe_Book/blob/main/2_CDS_Access.ipynb)

```bash
# Run MintPy smallbaselineApp
docker run --rm --platform linux/amd64 \
  -v $PWD:/home/mambauser \
  ghcr.io/insarlab/mintpy:latest \
  smallbaselineApp.py mintpy/seoul-insar.txt
```

**Configuration**: Edit `smallbaselineApp.cfg` before running:
- Set `mintpy.troposphericDelay.method = no` to skip tropospheric correction (faster)
- Configure input file paths to point to your clipped GeoTIFF files
- Adjust processing parameters as needed

**Output files**:
- `timeseries.h5` - Displacement timeseries for each date
- `velocity.h5` - Mean velocity map (cm/year)
- `temporalCoherence.h5` - Quality metrics
- Other intermediate products

### Step 4: Visualize Results

Visualize displacement and velocity with geographic coordinates:

```bash
# Interactive timeseries viewer
uv run toolkit/visualization.py timeseries.h5 --interactive

# Plot specific date
uv run toolkit/visualization.py timeseries.h5 --date-idx 44 --output displacement.png

# Plot velocity map
uv run toolkit/visualization.py velocity.h5 --output velocity.png
```

See [InSAR Visualization](#insar-visualization) section below for more options.

## InSAR Visualization

Visualize InSAR timeseries and velocity data with geographic coordinates (lat/lon).

### Quick Start

```bash
# View help
uv run toolkit/visualization.py --help

# Plot timeseries at specific date
uv run toolkit/visualization.py timeseries.h5 --date-idx 44

# Interactive timeseries viewer with slider
uv run toolkit/visualization.py timeseries.h5 --interactive

# Plot velocity map
uv run toolkit/visualization.py velocity.h5

# Save to file
uv run toolkit/visualization.py timeseries.h5 --output displacement.png
```


### Examples

```bash
# Plot displacement at date index 44 and save
uv run toolkit/visualization.py timeseries.h5 --date-idx 44 --output displacement_44.png

# Interactive viewer for exploring timeseries
uv run toolkit/visualization.py timeseries.h5 -i

# Plot velocity with custom color scale
uv run toolkit/visualization.py velocity.h5 --vmin -5 --vmax 5 --cmap jet -o velocity_map.png

# Custom title
uv run toolkit/visualization.py timeseries.h5 --title "Seoul Displacement Analysis"
```

### Features

- **Geographic Coordinates**: Automatic conversion from UTM to lat/lon
- **Units**: Displacement in cm, velocity in cm/year
- **Reference Point**: Displayed as black square on maps
- **Interactive Mode**: Slider to browse through timeseries dates
- **Customization**: Flexible colormap and scale options

## Documentation

- [Useful References](docs/REFERENCE.md)
