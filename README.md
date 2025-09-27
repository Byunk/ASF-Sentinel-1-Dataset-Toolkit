# ASF Sentinel-1 Dataset Toolkit

A toolkit for the ASF Sentinel-1 dataset.

## Features

- Search for Sentinel-1 granules in the ASF catalog
- Submit InSAR jobs
- Download the results

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/)

## Usage

```bash
cp .env.example .env
```

1. Search for granules with known base granule. It will save the results to `stack_data.txt`

```bash
uv run toolkit/search.py
```

2. Select the base granule and the start and end dates to search for granules. You need to modify `main.py` to do this.

```bash
uv run --env-file .env main.py
```

## Documentation

- [Useful References](docs/REFERENCE.md)
