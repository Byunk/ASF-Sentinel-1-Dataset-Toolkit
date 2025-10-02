# Multi-stage Dockerfile to identify all system dependencies for ASF Sentinel-1 InSAR Toolkit
# This will help document all system-level dependencies required beyond pip packages

# =============================================================================
# Stage 1: Base system with all necessary system libraries
# =============================================================================
FROM ubuntu:24.04 AS base

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Update package list and install system dependencies
RUN apt-get update && apt-get install -y \
    # Build tools
    build-essential \
    gcc \
    g++ \
    gfortran \
    make \
    cmake \
    pkg-config \
    # Python 3.13 (from deadsnakes PPA)
    software-properties-common \
    # HDF5 libraries (required by h5py and mintpy)
    libhdf5-dev \
    hdf5-tools \
    # PROJ (geographic projection library) - need 9.x for GDAL 3.11
    libproj-dev \
    proj-bin \
    proj-data \
    # GEOS (geometry library)
    libgeos-dev \
    # Additional geospatial libraries
    libspatialindex-dev \
    # Image processing libraries - needed by GDAL
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libwebp-dev \
    libzstd-dev \
    liblzma-dev \
    # SQLite (required by GDAL)
    libsqlite3-dev \
    # CURL (required by GDAL)
    libcurl4-openssl-dev \
    # XML libraries (for mintpy and GDAL)
    libxml2-dev \
    libxslt1-dev \
    libexpat1-dev \
    # LAPACK/BLAS for numerical computations
    liblapack-dev \
    libblas-dev \
    libopenblas-dev \
    # Compression libraries
    zlib1g-dev \
    libbz2-dev \
    # ECCODES (required by pygrib for GRIB file support)
    libeccodes-dev \
    libeccodes-tools \
    # Curl and wget for downloads
    curl \
    wget \
    # Git for version control
    git \
    # Other utilities
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python 3.12 (compatible with pygrib)
# Note: Python 3.13 is incompatible with pygrib due to deprecated 'long' type
RUN apt-get update && \
    apt-get install -y \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.12 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1

# =============================================================================
# Install GDAL 3.11.4 from source
# =============================================================================
ENV GDAL_VERSION=3.11.4

# Download and compile GDAL
RUN wget https://github.com/OSGeo/gdal/releases/download/v${GDAL_VERSION}/gdal-${GDAL_VERSION}.tar.gz && \
    tar -xzf gdal-${GDAL_VERSION}.tar.gz && \
    cd gdal-${GDAL_VERSION} && \
    mkdir build && \
    cd build && \
    cmake .. \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/usr/local && \
    make -j$(nproc) && \
    make install && \
    ldconfig && \
    cd ../.. && \
    rm -rf gdal-${GDAL_VERSION} gdal-${GDAL_VERSION}.tar.gz

# Set environment variables for GDAL
ENV GDAL_CONFIG=/usr/local/bin/gdal-config
ENV GDAL_DATA=/usr/local/share/gdal
ENV PROJ_LIB=/usr/share/proj
ENV LD_LIBRARY_PATH=/usr/local/lib:/usr/lib
ENV PATH=/usr/local/bin:$PATH

# Verify GDAL installation
RUN gdal-config --version

# =============================================================================
# Stage 2: Install uv and Python dependencies
# =============================================================================
FROM base AS builder

WORKDIR /app

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Verify uv installation
RUN uv --version

# Copy project files
COPY pyproject.toml uv.lock ./
COPY toolkit/ ./toolkit/
COPY main.py ./
COPY mintpy/ ./mintpy/

# Install dependencies using uv
# This will reveal any missing system dependencies
RUN uv sync --frozen

# =============================================================================
# Stage 3: Runtime environment
# =============================================================================
FROM base AS runtime

WORKDIR /app

# Copy uv from builder
COPY --from=builder /root/.local/bin/uv /usr/local/bin/uv

# Copy the entire project and virtual environment
COPY --from=builder /app /app

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV UV_PROJECT_ENVIRONMENT=/app/.venv

# Test that all critical imports work
RUN python3 -c "from osgeo import gdal; print(f'GDAL version: {gdal.__version__}')" && \
    python3 -c "import h5py; print(f'h5py version: {h5py.__version__}')" && \
    python3 -c "from pyproj import Transformer; print('pyproj OK')" && \
    python3 -c "import numpy; print(f'numpy version: {numpy.__version__}')" && \
    python3 -c "import matplotlib; print(f'matplotlib version: {matplotlib.__version__}')" && \
    echo "All critical imports successful!"

# Create data and results directories
RUN mkdir -p data results

# Set working directory
WORKDIR /app

# Default command shows help
CMD ["python", "main.py", "--help"]
