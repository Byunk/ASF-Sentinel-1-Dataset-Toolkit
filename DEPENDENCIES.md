# System Dependencies Documentation

This document lists all system-level dependencies required to run the ASF Sentinel-1 InSAR Toolkit, identified through Docker containerization testing.

## Purpose

This project requires several geospatial and scientific computing libraries that must be installed at the system level, beyond what pip/uv can provide. This document was created by building a Docker container from vanilla Ubuntu 24.04 and documenting all required dependencies.

## Summary

**Critical Finding**: This project requires **GDAL 3.11.4**, but Ubuntu 24.04 only provides GDAL 3.8.4. Therefore, GDAL must be compiled from source.

**Python Version Incompatibility**: The `pygrib` package (required by `mintpy -> pyaps3`) is incompatible with Python 3.13 due to deprecated `long` type usage. Consider using Python 3.11 or 3.12 instead.

## System Dependencies

### Build Tools
- `build-essential` - Essential compilation tools
- `gcc`, `g++`, `gfortran` - Compilers for C, C++, and Fortran
- `make`, `cmake` - Build automation tools
- `pkg-config` - Helper tool for compiling applications

### Geospatial Libraries

#### GDAL (Geospatial Data Abstraction Library) - **CRITICAL**
- **Required Version**: 3.11.4
- **Ubuntu 24.04 Version**: 3.8.4 (insufficient)
- **Solution**: Must compile from source
- **Source**: https://github.com/OSGeo/gdal/releases/download/v3.11.4/gdal-3.11.4.tar.gz
- **Purpose**: Reading and writing raster and vector geospatial data formats (GeoTIFF)

**GDAL Build Dependencies**:
- `libsqlite3-dev` - SQLite database library
- `libcurl4-openssl-dev` - HTTP client library
- `libexpat1-dev` - XML parsing library
- `zlib1g-dev` - Compression library
- `libbz2-dev` - Bzip2 compression
- `liblzma-dev` - LZMA compression
- `libzstd-dev` - Zstandard compression
- `libwebp-dev` - WebP image format
- `libjpeg-dev` - JPEG image format
- `libpng-dev` - PNG image format
- `libtiff-dev` - TIFF image format

#### PROJ (Cartographic Projections Library)
- **Package**: `libproj-dev`, `proj-bin`, `proj-data`
- **Purpose**: Coordinate system transformations
- **Required by**: GDAL, pyproj

#### GEOS (Geometry Engine - Open Source)
- **Package**: `libgeos-dev`
- **Purpose**: Geometry operations
- **Required by**: GDAL

#### Spatial Index
- **Package**: `libspatialindex-dev`
- **Purpose**: Spatial indexing and search

### Scientific Computing Libraries

#### HDF5 (Hierarchical Data Format)
- **Package**: `libhdf5-dev`, `hdf5-tools`
- **Purpose**: Storing and managing large scientific datasets
- **Required by**: h5py, mintpy (for InSAR time-series storage)

#### LAPACK/BLAS (Linear Algebra)
- **Package**: `liblapack-dev`, `libblas-dev`, `libopenblas-dev`
- **Purpose**: Optimized linear algebra operations
- **Required by**: numpy, scipy, scientific computations

### GRIB File Support

#### ECCODES
- **Package**: `libeccodes-dev`, `libeccodes-tools`
- **Purpose**: Encoding and decoding GRIB files (weather data format)
- **Required by**: pygrib (dependency of pyaps3, which is required by mintpy)
- **Critical**: Without this, pygrib compilation fails

### XML Libraries
- **Package**: `libxml2-dev`, `libxslt1-dev`
- **Purpose**: XML parsing and transformation
- **Required by**: lxml, mintpy

### Network Libraries
- **Package**: `curl`, `wget`, `git`
- **Purpose**: Downloading data and cloning repositories

### Other System Packages
- **Package**: `unzip`, `ca-certificates`
- **Purpose**: Archive extraction and SSL/TLS certificates

## Python Version Compatibility Issue

### Problem: pygrib + Python 3.13
The `pygrib` package (v2.1.6) fails to compile on Python 3.13 with the following error:

```
src/pygrib/_pygrib.pyx:420:46: undeclared name not builtin: long
```

**Root Cause**: Python 3 removed the `long` type (it's now just `int`), and `pygrib` 2.1.6 still uses legacy Python 2 syntax.

**Dependency Chain**:
```
asf-sentinel-1-dataset-toolkit
  └─ mintpy (v1.6.2)
      └─ pyaps3 (v0.3.7)
          └─ pygrib (v2.1.6) ❌ Incompatible with Python 3.13
```

### Solutions

1. **Recommended**: Use Python 3.12 instead of 3.13
   - Update `pyproject.toml`: `requires-python = ">=3.12,<3.13"`
   - Python 3.12 is well-supported and mature

2. **Alternative**: Wait for updated pygrib
   - Monitor https://github.com/jswhit/pygrib for Python 3.13 support

3. **Alternative**: Fork and patch pygrib
   - Replace `long` with `int` in the Cython source

## Docker Build Instructions

### Successful Build Command (Python 3.12)
```bash
# Modify Dockerfile to use Python 3.12 instead of 3.13
docker build -t asf-insar-toolkit .
```

### Environment Variables Required
```bash
GDAL_CONFIG=/usr/local/bin/gdal-config
GDAL_DATA=/usr/local/share/gdal
PROJ_LIB=/usr/share/proj
LD_LIBRARY_PATH=/usr/local/lib:/usr/lib
PATH=/usr/local/bin:$PATH
```

## Installation Time Estimates

- System packages installation: ~5 minutes
- GDAL compilation from source: ~15-20 minutes
- Python package installation: ~10-15 minutes
- **Total**: ~30-40 minutes (first build)

## Platform-Specific Notes

### macOS
- Use Homebrew to install system dependencies:
  ```bash
  brew install gdal hdf5 proj geos eccodes
  ```
- GDAL version from Homebrew should be sufficient (usually latest)

### Ubuntu/Debian
- Must compile GDAL from source (as shown in Dockerfile)
- All other dependencies available via apt

### CentOS/RHEL
- Use `yum` or `dnf` for package installation
- GDAL may need compilation from source

## Verification

After installation, verify critical dependencies:

```bash
# GDAL version
gdal-config --version  # Should show 3.11.4

# Python imports
python -c "from osgeo import gdal; print(gdal.__version__)"
python -c "import h5py; print(h5py.__version__)"
python -c "from pyproj import Transformer; print('pyproj OK')"
```

## Maintenance Notes

1. **GDAL Updates**: When updating GDAL, ensure Python bindings match system library version
2. **HDF5**: Ensure thread-safety is enabled if using multi-threaded applications
3. **PROJ Data**: Update `proj-data` package periodically for latest coordinate transformations

## Files Created

This investigation generated the following files:

1. `Dockerfile` - Multi-stage build for dependency identification
2. `.dockerignore` - Optimized Docker build context
3. `DEPENDENCIES.md` - This documentation
4. `uv.lock` - Python dependency lock file

## References

- GDAL Documentation: https://gdal.org/
- HDF5 Documentation: https://www.hdfgroup.org/
- MintPy Documentation: https://github.com/insarlab/MintPy
- ECCODES Documentation: https://confluence.ecmwf.int/display/ECC
- ASF HyP3: https://hyp3-docs.asf.alaska.edu/
