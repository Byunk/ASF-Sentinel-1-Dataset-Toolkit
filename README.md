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

There is a `main.py` script that demonstrates the usage of the toolkit.

```bash
uv run --env-file .env main.py
```

## Documentation

- [Useful References](docs/REFERENCE.md)
