"""
Airport Infrastructure - Subsidence Risk Analysis

Generic tool for analyzing subsidence risk from MintPy InSAR data using
scientifically validated methods.

Methodology:
- Angular distortion: Fernández-Torres et al. (2020), Cabral-Cano et al. (2011)
- Damage thresholds: Skempton & MacDonald (1956)
- Gradient calculation: Sobel operator (standard GIS method)

Usage:
    python airport_risk_analysis.py \\
        --data-dir results/airport-name \\
        --wkt "POLYGON((lon1 lat1, lon2 lat2, ...))" \\
        --name "Airport Name" \\
        --facility-year 2000
"""

import numpy as np
import h5py
from shapely.geometry import Point, Polygon
from shapely import wkt
import pyproj
from scipy.ndimage import sobel
import json
from datetime import datetime
import argparse
import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib import cm


def get_polygon_bounds_with_buffer(polygon, buffer_percent=10):
    """
    Calculate bounding box of polygon with buffer for visualization.

    Args:
        polygon: Shapely polygon object
        buffer_percent: Percentage buffer to add around bounds (default: 10%)

    Returns:
        tuple: (lon_min, lon_max, lat_min, lat_max)
    """
    bounds = polygon.bounds  # (minx, miny, maxx, maxy)
    lon_min, lat_min, lon_max, lat_max = bounds

    # Calculate buffer
    lon_range = lon_max - lon_min
    lat_range = lat_max - lat_min

    lon_buffer = lon_range * (buffer_percent / 100)
    lat_buffer = lat_range * (buffer_percent / 100)

    # Apply buffer
    lon_min -= lon_buffer
    lon_max += lon_buffer
    lat_min -= lat_buffer
    lat_max += lat_buffer

    return lon_min, lon_max, lat_min, lat_max


def create_risk_dashboard(
    area_velocity,
    area_angular_dist,
    lon_grid,
    lat_grid,
    grad_x,
    grad_y,
    area_mask,
    area_polygon,
    critical_locations,
    hazard_counts,
    facility_name,
    projection_years,
    output_file,
):
    """Create multi-panel dashboard visualization of risk assessment."""

    # Define Skempton & MacDonald risk thresholds
    thresholds = [1 / 5000, 1 / 3000, 1 / 1500, 1 / 500]

    # Create colormap for risk classes
    colors = [
        "#2ecc71",
        "#f1c40f",
        "#e67e22",
        "#e74c3c",
        "#c0392b",
    ]  # Green -> Yellow -> Orange -> Red -> Dark Red
    cmap = ListedColormap(colors)
    bounds = [0] + thresholds + [1]  # Add min and max bounds
    norm = BoundaryNorm(bounds, cmap.N)

    # Calculate airport bounds for cropping visualization (if polygon provided)
    if area_polygon is not None:
        lon_min, lon_max, lat_min, lat_max = get_polygon_bounds_with_buffer(
            area_polygon, buffer_percent=10
        )
    else:
        # Use full grid extent if no polygon
        lon_min, lon_max = np.nanmin(lon_grid), np.nanmax(lon_grid)
        lat_min, lat_max = np.nanmin(lat_grid), np.nanmax(lat_grid)

    # Create figure with 4 subplots
    fig = plt.figure(figsize=(20, 14))

    # Panel 1: Angular Distortion Heatmap with Risk Thresholds
    ax1 = plt.subplot(2, 2, 1)
    im1 = ax1.pcolormesh(
        # lon_grid, lat_grid, area_angular_dist, cmap=cmap, norm=norm, shading="auto"
        lon_grid,
        lat_grid,
        area_angular_dist,
        cmap=cmap,
        norm=norm,
        shading="auto",
    )

    # Add facility boundary (if polygon provided)
    if area_polygon is not None and hasattr(area_polygon, "exterior"):
        boundary_coords = list(area_polygon.exterior.coords)
        boundary_lons = [coord[0] for coord in boundary_coords]
        boundary_lats = [coord[1] for coord in boundary_coords]
        ax1.plot(
            boundary_lons, boundary_lats, "k--", linewidth=2, label="Facility Boundary"
        )

    # Add critical location markers
    for loc in critical_locations:
        ax1.plot(
            loc["lon"],
            loc["lat"],
            "w*",
            markersize=12,
            markeredgecolor="black",
            markeredgewidth=1,
        )

    ax1.set_xlabel("Longitude (°E)", fontsize=11)
    ax1.set_ylabel("Latitude (°N)", fontsize=11)
    ax1.set_title(
        f"Angular Distortion Risk Map\n({projection_years}-year projection)",
        fontsize=12,
        fontweight="bold",
    )
    ax1.set_aspect("equal", adjustable="box")
    ax1.set_xlim(lon_min, lon_max)
    ax1.set_ylim(lat_min, lat_max)
    ax1.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
    ax1.tick_params(axis="both", labelsize=9)

    # Colorbar with risk labels
    cbar1 = plt.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04)
    cbar1.set_label("Angular Distortion (radians)", fontsize=10)
    cbar1.set_ticks(thresholds + [np.nanmax(area_angular_dist)])
    cbar1.set_ticklabels(
        [
            f"Very Low (< 1/{int(1/thresholds[0])})",
            f"Low (< 1/{int(1/thresholds[1])})",
            f"Medium (< 1/{int(1/thresholds[2])})",
            f"High (< 1/{int(1/thresholds[3])})",
            f"Very High (>= 1/{int(1/thresholds[3])})",
        ]
    )

    # # Panel 4: Hazard Class Distribution (Pie Chart)
    # ax4 = plt.subplot(2, 2, 4)

    # hazard_labels = list(hazard_counts.keys())
    # hazard_values = list(hazard_counts.values())
    # explode = [
    #     0.05 if val > 0 else 0 for val in hazard_values
    # ]  # Explode non-zero slices

    # wedges, texts, autotexts = ax4.pie(
    #     hazard_values,
    #     labels=hazard_labels,
    #     autopct=lambda pct: f"{pct:.1f}%" if pct > 0 else "",
    #     colors=colors,
    #     explode=explode,
    #     startangle=90,
    #     textprops={"fontsize": 9},
    # )

    # ax4.set_title("Hazard Class Distribution", fontsize=12, fontweight="bold")

    # Main title
    fig.suptitle(
        f"{facility_name} - Subsidence Risk Assessment Dashboard",
        fontsize=16,
        fontweight="bold",
        y=0.98,
    )

    plt.tight_layout(rect=[0, 0, 1, 0.96], pad=2.0)
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"  {output_file} - Risk assessment dashboard")


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Airport subsidence risk analysis using InSAR data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Input data
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--data-dir",
        type=str,
        help="Directory containing velocity.h5 and timeseries.h5 (e.g., results/airport-name)",
    )
    input_group.add_argument(
        "--velocity-file", type=str, help="Path to velocity.h5 file"
    )

    parser.add_argument(
        "--timeseries-file",
        type=str,
        help="Path to timeseries.h5 file (required if using --velocity-file)",
    )

    # Area of interest
    parser.add_argument(
        "--wkt",
        type=str,
        required=False,
        help="WKT polygon defining area of interest (optional - if not provided, analyzes entire dataset)",
    )

    # Facility information
    parser.add_argument(
        "--name",
        type=str,
        default="Infrastructure",
        help="Name of facility/area being analyzed (default: Infrastructure)",
    )

    parser.add_argument(
        "--facility-year",
        type=int,
        default=2000,
        help="Year facility was constructed (for vulnerability assessment, default: 2000)",
    )

    # Analysis parameters
    parser.add_argument(
        "--projection-years",
        type=float,
        default=10.0,
        help="Projection period for angular distortion in years (default: 10.0)",
    )

    # Output
    parser.add_argument(
        "--output-prefix",
        type=str,
        help="Prefix for output files (default: derived from --name)",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=".",
        help="Output directory (default: current directory)",
    )

    parser.add_argument(
        "--plot",
        action="store_true",
        help="Generate visualization plots of angular distortion and risk assessment",
    )

    args = parser.parse_args()

    # Validate and set file paths
    if args.data_dir:
        args.velocity_file = os.path.join(args.data_dir, "velocity.h5")
        args.timeseries_file = os.path.join(args.data_dir, "timeseries.h5")
    elif args.velocity_file and not args.timeseries_file:
        parser.error("--timeseries-file is required when using --velocity-file")

    # Check files exist
    if not os.path.exists(args.velocity_file):
        parser.error(f"Velocity file not found: {args.velocity_file}")
    if not os.path.exists(args.timeseries_file):
        parser.error(f"Timeseries file not found: {args.timeseries_file}")

    # Set output prefix
    if not args.output_prefix:
        args.output_prefix = args.name.lower().replace(" ", "_")

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    return args


def main():
    # Parse arguments
    args = parse_args()

    VELOCITY_FILE = args.velocity_file
    TIMESERIES_FILE = args.timeseries_file
    PROJECTION_YEARS = args.projection_years
    FACILITY_NAME = args.name
    FACILITY_YEAR = args.facility_year

    # Parse WKT polygon (optional)
    if args.wkt:
        AREA_WKT = args.wkt
        try:
            AREA_POLYGON = wkt.loads(AREA_WKT)
        except Exception as e:
            print(f"ERROR: Invalid WKT polygon: {e}")
            exit(1)
    else:
        AREA_WKT = None
        AREA_POLYGON = None

    # ========================================================================
    # LOAD DATA AND EXTRACT AREA
    # ========================================================================

    print("=" * 80)
    print(f"{FACILITY_NAME.upper()} SUBSIDENCE RISK ANALYSIS")
    print("=" * 80)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Velocity Data: {VELOCITY_FILE}")
    print(f"Projection Period: {PROJECTION_YEARS} years")
    print()

    # Load velocity data
    with h5py.File(VELOCITY_FILE, "r") as f:
        velocity = f["velocity"][:]  # m/year
        attrs = dict(f.attrs)

    print(f"Velocity Data Shape: {velocity.shape}")
    print(
        f"Velocity Range: {np.nanmin(velocity)*1000:.2f} to {np.nanmax(velocity)*1000:.2f} mm/year"
    )
    print(f"Velocity Mean: {np.nanmean(velocity)*1000:.2f} mm/year")
    print()

    # Load timeseries metadata
    with h5py.File(TIMESERIES_FILE, "r") as f:
        dates = f["date"][:]
        if isinstance(dates[0], bytes):
            dates = [d.decode() for d in dates]
        ts_attrs = dict(f.attrs)

    start_date = dates[0]
    end_date = dates[-1]
    n_acquisitions = len(dates)

    print(f"Time Series Period: {start_date} to {end_date}")
    print(f"Number of Acquisitions: {n_acquisitions}")
    print(f"Duration: {(int(end_date[:4]) - int(start_date[:4]))} years")
    print()

    # ========================================================================
    # CONVERT UTM TO LAT/LON
    # ========================================================================

    print("Converting coordinates...")

    # Get UTM parameters from metadata
    x_first = float(ts_attrs["X_FIRST"])
    y_first = float(ts_attrs["Y_FIRST"])
    x_step = float(ts_attrs["X_STEP"])
    y_step = float(ts_attrs["Y_STEP"])
    utm_zone = (
        ts_attrs["UTM_ZONE"].decode()
        if isinstance(ts_attrs["UTM_ZONE"], bytes)
        else ts_attrs["UTM_ZONE"]
    )

    # Create coordinate arrays
    height, width = velocity.shape
    x_coords = x_first + np.arange(width) * x_step
    y_coords = y_first + np.arange(height) * y_step

    # Create 2D grids
    x_grid, y_grid = np.meshgrid(x_coords, y_coords)

    # Convert UTM to Lat/Lon
    transformer = pyproj.Transformer.from_crs(
        f"EPSG:326{utm_zone[:2]}",  # UTM Zone -> EPSG code
        "EPSG:4326",  # WGS84
        always_xy=True,
    )

    lon_grid, lat_grid = transformer.transform(x_grid, y_grid)

    print(f"Latitude Range: {np.nanmin(lat_grid):.6f} to {np.nanmax(lat_grid):.6f}")
    print(f"Longitude Range: {np.nanmin(lon_grid):.6f} to {np.nanmax(lon_grid):.6f}")
    print()

    # ========================================================================
    # FILTER TO AREA BOUNDARY (if WKT provided)
    # ========================================================================

    if AREA_POLYGON:
        print(f"Filtering pixels within {FACILITY_NAME} boundary...")

        # Create mask for area pixels
        area_mask = np.zeros_like(velocity, dtype=bool)

        for i in range(height):
            for j in range(width):
                point = Point(lon_grid[i, j], lat_grid[i, j])
                if AREA_POLYGON.contains(point):
                    area_mask[i, j] = True

        n_area_pixels = np.sum(area_mask)
        print(f"Pixels within boundary: {n_area_pixels}")

        if n_area_pixels == 0:
            print("WARNING: No pixels found within boundary!")
            print(f"Polygon: {AREA_WKT}")
            print("Check coordinate system and polygon definition.")
            exit(1)

        # Extract area-only velocity
        area_velocity = np.where(area_mask, velocity, np.nan)
    else:
        print("No WKT masking - analyzing entire dataset")
        area_mask = np.ones_like(velocity, dtype=bool)
        area_velocity = velocity
        n_area_pixels = np.sum(~np.isnan(velocity))

    # Statistics for area
    area_vel_values = area_velocity[~np.isnan(area_velocity)]
    print()
    print("=" * 80)
    print(f"{FACILITY_NAME.upper()} AREA VELOCITY STATISTICS")
    print("=" * 80)
    print(f"Mean Velocity: {np.mean(area_vel_values)*1000:.2f} mm/year")
    print(f"Median Velocity: {np.median(area_vel_values)*1000:.2f} mm/year")
    print(f"Std Dev: {np.std(area_vel_values)*1000:.2f} mm/year")
    print(f"Min Velocity: {np.min(area_vel_values)*1000:.2f} mm/year (max uplift)")
    print(f"Max Velocity: {np.max(area_vel_values)*1000:.2f} mm/year (max subsidence)")
    print()

    # ========================================================================
    # CALCULATE ANGULAR DISTORTION USING PUBLISHED METHOD
    # ========================================================================

    print("Calculating angular distortion using Sobel operator...")
    print("Method: Fernández-Torres et al. (2020), Cabral-Cano et al. (2011)")
    print()

    # Calculate gradient using Sobel operator
    x_spacing_m = abs(x_step)  # Already in meters (UTM)
    y_spacing_m = abs(y_step)  # Already in meters (UTM)

    # Calculate gradients using Sobel operator (standard GIS method)
    grad_x = sobel(velocity, axis=1) / (8 * x_spacing_m)  # m/year per meter
    grad_y = sobel(velocity, axis=0) / (8 * y_spacing_m)  # m/year per meter

    # Calculate magnitude of gradient
    gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)

    # Convert to radians
    gradient_map = gradient_magnitude  # m/m per year = radians per year

    # Angular distortion over projection period
    angular_dist_map = gradient_map * PROJECTION_YEARS  # radians

    # Create edge mask to remove Sobel boundary artifacts (2 pixels on each side)
    edge_buffer = 2
    edge_mask = np.ones_like(angular_dist_map, dtype=bool)
    edge_mask[:edge_buffer, :] = False  # Top edge
    edge_mask[-edge_buffer:, :] = False  # Bottom edge
    edge_mask[:, :edge_buffer] = False  # Left edge
    edge_mask[:, -edge_buffer:] = False  # Right edge

    # Apply area mask AND edge mask to angular distortion
    area_angular_dist = np.where(area_mask & edge_mask, angular_dist_map, np.nan)
    area_angular_values = area_angular_dist[~np.isnan(area_angular_dist)]

    print("=" * 80)
    print(f"ANGULAR DISTORTION STATISTICS ({PROJECTION_YEARS}-YEAR PROJECTION)")
    print("=" * 80)
    print(f"Mean: {np.mean(area_angular_values):.6f} radians")
    print(f"Median: {np.median(area_angular_values):.6f} radians")
    print(f"Max: {np.max(area_angular_values):.6f} radians")
    print(
        f"Max Ratio: 1/{int(1/np.max(area_angular_values)) if np.max(area_angular_values) > 0 else 'inf'}"
    )
    print()

    # ========================================================================
    # IDENTIFY CRITICAL LOCATIONS
    # ========================================================================

    print("=" * 80)
    print("CRITICAL LOCATIONS IDENTIFIED")
    print("=" * 80)

    # Find most critical pixels
    max_subsidence_idx = np.unravel_index(
        np.nanargmax(area_velocity), area_velocity.shape
    )
    max_uplift_idx = np.unravel_index(np.nanargmin(area_velocity), area_velocity.shape)
    max_angular_idx = np.unravel_index(
        np.nanargmax(area_angular_dist), area_angular_dist.shape
    )

    critical_locations = [
        {
            "name": "Maximum Subsidence Zone",
            "lat": float(lat_grid[max_subsidence_idx]),
            "lon": float(lon_grid[max_subsidence_idx]),
            "velocity": float(velocity[max_subsidence_idx] * 1000),  # mm/year
            "angular_distortion": float(angular_dist_map[max_subsidence_idx]),
            "idx": max_subsidence_idx,
        },
        {
            "name": "Maximum Uplift Zone",
            "lat": float(lat_grid[max_uplift_idx]),
            "lon": float(lon_grid[max_uplift_idx]),
            "velocity": float(velocity[max_uplift_idx] * 1000),  # mm/year
            "angular_distortion": float(angular_dist_map[max_uplift_idx]),
            "idx": max_uplift_idx,
        },
        {
            "name": "Maximum Angular Distortion Zone",
            "lat": float(lat_grid[max_angular_idx]),
            "lon": float(lon_grid[max_angular_idx]),
            "velocity": float(velocity[max_angular_idx] * 1000),  # mm/year
            "angular_distortion": float(angular_dist_map[max_angular_idx]),
            "idx": max_angular_idx,
        },
    ]

    for loc in critical_locations:
        print(f"\n{loc['name']}:")
        print(f"  Location: {loc['lat']:.6f}°N, {loc['lon']:.6f}°E")
        print(f"  Velocity: {loc['velocity']:.2f} mm/year")
        print(
            f"  Angular Distortion ({PROJECTION_YEARS}yr): {loc['angular_distortion']:.6f} rad"
        )
        print(
            f"  Distortion Ratio: 1/{int(1/loc['angular_distortion']) if loc['angular_distortion'] > 0 else 'inf'}"
        )

    print()

    # ========================================================================
    # CALCULATE RISK SCORES
    # ========================================================================

    print("=" * 80)
    print("RISK ASSESSMENT (using Skempton & MacDonald 1956 thresholds)")
    print("=" * 80)
    print()

    # Calculate facility age
    current_year = datetime.now().year
    facility_age = current_year - FACILITY_YEAR

    # Determine age vulnerability score
    if facility_age > 50:
        age_score = 4.5
    elif facility_age > 30:
        age_score = 3.5
    elif facility_age > 15:
        age_score = 2.5
    elif facility_age > 5:
        age_score = 1.5
    else:
        age_score = 1.0

    risk_results = []

    for loc in critical_locations:
        print(f"{loc['name']}:")

        # Classify hazard using Skempton & MacDonald (1956) thresholds
        angular_dist = loc["angular_distortion"]

        if angular_dist > 1 / 500:  # 0.002 radians
            hazard_score = 5
            hazard_class = "Very High - Structural damage expected"
        elif angular_dist > 1 / 1500:  # 0.000667 radians
            hazard_score = 4
            hazard_class = "High - Severe damage possible"
        elif angular_dist > 1 / 3000:  # 0.000333 radians
            hazard_score = 3
            hazard_class = "Medium - Moderate damage possible"
        elif angular_dist > 1 / 5000:  # 0.0002 radians
            hazard_score = 2
            hazard_class = "Low - Minor damage possible"
        else:
            hazard_score = 1
            hazard_class = "Very Low - Negligible damage expected"

        # Calculate vulnerability (generic infrastructure)
        vuln_scores = {
            "foundation": 2.0,  # Pile foundation (typical for critical infrastructure)
            "age": age_score,  # Based on actual facility age
            "structure": 2.5,  # Reinforced concrete (typical)
            "height": 1.5,  # Low-rise (generic)
            "criticality": 4.5,  # Critical infrastructure
        }
        weights = {
            "foundation": 0.30,
            "age": 0.20,
            "structure": 0.25,
            "height": 0.15,
            "criticality": 0.10,
        }
        vuln_overall = sum(vuln_scores[k] * weights[k] for k in weights.keys())

        result = {
            "hazard": {
                "subsidence_velocity": float(round(loc["velocity"], 2)),
                "velocity_unit": "mm/year",
                "angular_distortion_projected": float(round(angular_dist, 6)),
                "projection_period": float(PROJECTION_YEARS),
                "distortion_ratio": f"1/{int(1/angular_dist) if angular_dist > 0 else 'inf'}",
                "hazard_score": int(hazard_score),
                "hazard_class": hazard_class,
            },
            "vulnerability": {
                "overall": float(round(vuln_overall, 2)),
                "components": {k: float(v) for k, v in vuln_scores.items()},
            },
        }

        # Store result
        loc["risk_result"] = result
        risk_results.append(
            {
                "location": loc["name"],
                "coordinates": {"lat": loc["lat"], "lon": loc["lon"]},
                "hazard": result["hazard"],
                "vulnerability": result["vulnerability"],
            }
        )

        print(f"  Hazard Class: {result['hazard']['hazard_class']}")
        print(f"  Hazard Score: {result['hazard']['hazard_score']}/5")
        print(
            f"  Subsidence Velocity: {result['hazard']['subsidence_velocity']} mm/year"
        )
        print(
            f"  Angular Distortion ({PROJECTION_YEARS}yr): {result['hazard']['distortion_ratio']}"
        )
        print(f"  Vulnerability Score: {result['vulnerability']['overall']:.2f}/5")
        print()

    # ========================================================================
    # GENERATE SUMMARY STATISTICS
    # ========================================================================

    # Count pixels in each hazard class
    hazard_counts = {
        "Very Low": np.sum(area_angular_values < 1 / 5000),
        "Low": np.sum(
            (area_angular_values >= 1 / 5000) & (area_angular_values < 1 / 3000)
        ),
        "Medium": np.sum(
            (area_angular_values >= 1 / 3000) & (area_angular_values < 1 / 1500)
        ),
        "High": np.sum(
            (area_angular_values >= 1 / 1500) & (area_angular_values < 1 / 500)
        ),
        "Very High": np.sum(area_angular_values >= 1 / 500),
    }

    print("=" * 80)
    print(f"{FACILITY_NAME.upper()} AREA HAZARD DISTRIBUTION")
    print("=" * 80)
    for hazard_class, count in hazard_counts.items():
        pct = 100 * count / len(area_angular_values)
        print(f"{hazard_class:15s}: {count:6d} pixels ({pct:5.2f}%)")
    print()

    # ========================================================================
    # SAVE RESULTS
    # ========================================================================

    output_data = {
        "analysis_info": {
            "facility_name": FACILITY_NAME,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "velocity_file": VELOCITY_FILE,
            "timeseries_file": TIMESERIES_FILE,
            "projection_period_years": PROJECTION_YEARS,
            "facility_construction_year": FACILITY_YEAR,
            "methodology": "Fernández-Torres et al. (2020), Cabral-Cano et al. (2011)",
            "damage_thresholds": "Skempton & MacDonald (1956)",
        },
        "time_series": {
            "start_date": start_date,
            "end_date": end_date,
            "n_acquisitions": n_acquisitions,
            "duration_years": int(end_date[:4]) - int(start_date[:4]),
        },
        "area_of_interest": {
            "polygon_wkt": AREA_WKT if AREA_WKT else "None (entire dataset)",
            "n_pixels": int(n_area_pixels),
            "velocity_statistics_mm_per_year": {
                "mean": float(np.mean(area_vel_values) * 1000),
                "median": float(np.median(area_vel_values) * 1000),
                "std": float(np.std(area_vel_values) * 1000),
                "min": float(np.min(area_vel_values) * 1000),
                "max": float(np.max(area_vel_values) * 1000),
            },
            "angular_distortion_statistics_radians": {
                "mean": float(np.mean(area_angular_values)),
                "median": float(np.median(area_angular_values)),
                "max": float(np.max(area_angular_values)),
                "max_ratio": f"1/{int(1/np.max(area_angular_values)) if np.max(area_angular_values) > 0 else 'inf'}",
            },
            "hazard_distribution": {k: int(v) for k, v in hazard_counts.items()},
        },
        "critical_locations": risk_results,
    }

    output_json = os.path.join(
        args.output_dir, f"{args.output_prefix}_risk_assessment.json"
    )
    with open(output_json, "w") as f:
        json.dump(output_data, f, indent=2)

    print("=" * 80)
    print("OUTPUT FILES GENERATED")
    print("=" * 80)
    print(f"  {output_json} - Detailed risk assessment data")

    # ========================================================================
    # GENERATE VISUALIZATIONS (if requested)
    # ========================================================================

    if args.plot:
        print()
        print("Generating visualizations...")

        # Dashboard visualization
        dashboard_file = os.path.join(
            args.output_dir, f"{args.output_prefix}_risk_dashboard.png"
        )
        create_risk_dashboard(
            area_velocity=area_velocity,
            area_angular_dist=area_angular_dist,
            lon_grid=lon_grid,
            lat_grid=lat_grid,
            grad_x=grad_x,
            grad_y=grad_y,
            area_mask=area_mask,
            area_polygon=AREA_POLYGON,
            critical_locations=critical_locations,
            hazard_counts=hazard_counts,
            facility_name=FACILITY_NAME,
            projection_years=PROJECTION_YEARS,
            output_file=dashboard_file,
        )

    print()
    print("Analysis complete!")


if __name__ == "__main__":
    main()
