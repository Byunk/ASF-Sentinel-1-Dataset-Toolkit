"""
Visualization tools for InSAR timeseries data with geographic coordinates.
"""

import h5py
import numpy as np
import matplotlib.pyplot as plt
from pyproj import Transformer


def read_timeseries_metadata(timeseries_file):
    """Read metadata from timeseries HDF5 file."""
    with h5py.File(timeseries_file, "r") as f:
        metadata = dict(f.attrs)
    return metadata


def get_coordinate_grids(metadata):
    """
    Generate coordinate grids from metadata.

    Returns:
        x_utm: 1D array of UTM X coordinates (easting)
        y_utm: 1D array of UTM Y coordinates (northing)
        lon: 2D array of longitude
        lat: 2D array of latitude
    """
    x_first = float(metadata["X_FIRST"])
    x_step = float(metadata["X_STEP"])
    y_first = float(metadata["Y_FIRST"])
    y_step = float(metadata["Y_STEP"])
    width = int(metadata["WIDTH"])
    length = int(metadata["LENGTH"])
    epsg = int(metadata["EPSG"])

    # Create UTM coordinate arrays
    x_utm = x_first + np.arange(width) * x_step
    y_utm = y_first + np.arange(length) * y_step

    # Create 2D meshgrids
    X_utm, Y_utm = np.meshgrid(x_utm, y_utm)

    # Transform UTM to lat/lon
    transformer = Transformer.from_crs(f"EPSG:{epsg}", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(X_utm, Y_utm)

    return x_utm, y_utm, lon, lat


def plot_timeseries_geographic(
    timeseries_file,
    date_idx=None,
    figsize=(12, 10),
    cmap="RdYlBu_r",
    vmin=None,
    vmax=None,
    show_colorbar=True,
    title=None,
    save_path=None,
):
    """
    Plot InSAR timeseries with geographic coordinates.

    Parameters:
        timeseries_file: Path to timeseries.h5 file
        date_idx: Index of date to plot (default: last date)
        figsize: Figure size (width, height)
        cmap: Colormap name
        vmin, vmax: Color scale limits in cm
        show_colorbar: Whether to show colorbar
        title: Custom title (auto-generated if None)
        save_path: Path to save figure (None to just display)
    """
    # Read metadata and data
    with h5py.File(timeseries_file, "r") as f:
        metadata = dict(f.attrs)
        dates = f["date"][:]
        if isinstance(dates[0], bytes):
            dates = [d.decode() for d in dates]

        # Get date index
        if date_idx is None:
            date_idx = len(dates) - 1

        # Read displacement data (in meters)
        displacement = f["timeseries"][date_idx, :, :]

    # Convert to cm
    displacement_cm = displacement * 100

    # Mask invalid data
    displacement_cm = np.ma.masked_where(displacement_cm == 0, displacement_cm)

    # Get coordinates
    x_utm, y_utm, lon, lat = get_coordinate_grids(metadata)

    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    # Plot with lon/lat coordinates
    if vmin is None:
        vmin = np.percentile(displacement_cm[~displacement_cm.mask], 2)
    if vmax is None:
        vmax = np.percentile(displacement_cm[~displacement_cm.mask], 98)

    im = ax.pcolormesh(
        lon, lat, displacement_cm, cmap=cmap, vmin=vmin, vmax=vmax, shading="auto"
    )

    # Add reference point
    ref_lon = lon[int(metadata["REF_Y"]), int(metadata["REF_X"])]
    ref_lat = lat[int(metadata["REF_Y"]), int(metadata["REF_X"])]
    ax.plot(
        ref_lon,
        ref_lat,
        "ks",
        markersize=10,
        markerfacecolor="black",
        markeredgecolor="white",
        markeredgewidth=2,
        label="Reference Point",
    )

    # Labels and formatting
    ax.set_xlabel("Longitude (°E)", fontsize=12)
    ax.set_ylabel("Latitude (°N)", fontsize=12)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.legend(loc="upper right")

    # Title
    if title is None:
        ref_date = (
            metadata.get("REF_DATE", dates[0]).decode()
            if isinstance(metadata.get("REF_DATE", dates[0]), bytes)
            else metadata.get("REF_DATE", dates[0])
        )
        title = f"N = {date_idx}, Time = {dates[date_idx]}\n"
        title += f"Reference: N = 0, Time = {ref_date}"
    ax.set_title(title, fontsize=14, weight="bold")

    # Colorbar
    if show_colorbar:
        cbar = plt.colorbar(im, ax=ax, orientation="vertical", pad=0.02, shrink=0.8)
        cbar.set_label("Displacement [cm]", fontsize=12)

    # Add coordinate info text
    lon_range = (lon.min(), lon.max())
    lat_range = (lat.min(), lat.max())
    info_text = "Geographic extent:\n"
    info_text += f"Lon: {lon_range[0]:.4f}°E to {lon_range[1]:.4f}°E\n"
    info_text += f"Lat: {lat_range[0]:.4f}°N to {lat_range[1]:.4f}°N\n"
    info_text += f"UTM Zone: {metadata.get('UTM_ZONE', '52N').decode() if isinstance(metadata.get('UTM_ZONE', '52N'), bytes) else metadata.get('UTM_ZONE', '52N')}"

    ax.text(
        0.02,
        0.02,
        info_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="bottom",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Figure saved to: {save_path}")

    plt.show()

    return fig, ax


def plot_velocity_geographic(
    velocity_file,
    figsize=(12, 10),
    cmap="RdYlBu_r",
    vmin=None,
    vmax=None,
    title="Mean LOS Velocity",
    save_path=None,
):
    """
    Plot velocity with geographic coordinates.

    Parameters:
        velocity_file: Path to velocity.h5 file
        figsize: Figure size (width, height)
        cmap: Colormap name
        vmin, vmax: Velocity limits in cm/year
        title: Plot title
        save_path: Path to save figure
    """
    # Read velocity data
    with h5py.File(velocity_file, "r") as f:
        metadata = dict(f.attrs)
        velocity = f["velocity"][:]

    # Convert m/year to cm/year
    velocity_cm = velocity * 100

    # Mask invalid data
    velocity_cm = np.ma.masked_where(velocity_cm == 0, velocity_cm)

    # Get coordinates
    x_utm, y_utm, lon, lat = get_coordinate_grids(metadata)

    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    # Auto-scale if not provided
    if vmin is None or vmax is None:
        vmax_abs = np.percentile(np.abs(velocity_cm[~velocity_cm.mask]), 98)
        vmin = -vmax_abs
        vmax = vmax_abs

    im = ax.pcolormesh(
        lon, lat, velocity_cm, cmap=cmap, vmin=vmin, vmax=vmax, shading="auto"
    )

    # Add reference point
    ref_lon = lon[int(metadata["REF_Y"]), int(metadata["REF_X"])]
    ref_lat = lat[int(metadata["REF_Y"]), int(metadata["REF_X"])]
    ax.plot(
        ref_lon,
        ref_lat,
        "ks",
        markersize=10,
        markerfacecolor="black",
        markeredgecolor="white",
        markeredgewidth=2,
        label="Reference Point",
    )

    # Labels and formatting
    ax.set_xlabel("Longitude (°E)", fontsize=12)
    ax.set_ylabel("Latitude (°N)", fontsize=12)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.legend(loc="upper right")
    ax.set_title(title, fontsize=14, weight="bold")

    # Colorbar
    cbar = plt.colorbar(im, ax=ax, orientation="vertical", pad=0.02, shrink=0.8)
    cbar.set_label("Velocity [cm/year]", fontsize=12)

    # Add coordinate info
    lon_range = (lon.min(), lon.max())
    lat_range = (lat.min(), lat.max())
    date_range = (
        f"{metadata.get('START_DATE', 'N/A')} - {metadata.get('END_DATE', 'N/A')}"
    )
    info_text = f"Time: {date_range}\n"
    info_text += f"Lon: {lon_range[0]:.4f}°E to {lon_range[1]:.4f}°E\n"
    info_text += f"Lat: {lat_range[0]:.4f}°N to {lat_range[1]:.4f}°N"

    ax.text(
        0.02,
        0.02,
        info_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="bottom",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Figure saved to: {save_path}")

    plt.show()

    return fig, ax


def interactive_timeseries_viewer(timeseries_file):
    """
    Interactive viewer for timeseries data with slider.

    Parameters:
        timeseries_file: Path to timeseries.h5 file
    """
    from matplotlib.widgets import Slider

    # Read data
    with h5py.File(timeseries_file, "r") as f:
        metadata = dict(f.attrs)
        dates = f["date"][:]
        if isinstance(dates[0], bytes):
            dates = [d.decode() for d in dates]
        timeseries_data = f["timeseries"][:]

    # Convert to cm and mask
    timeseries_cm = timeseries_data * 100
    timeseries_cm = np.ma.masked_where(timeseries_cm == 0, timeseries_cm)

    # Get coordinates
    x_utm, y_utm, lon, lat = get_coordinate_grids(metadata)

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 10))
    plt.subplots_adjust(bottom=0.15)

    # Initial plot
    vmin = np.percentile(timeseries_cm[~timeseries_cm.mask], 2)
    vmax = np.percentile(timeseries_cm[~timeseries_cm.mask], 98)

    im = ax.pcolormesh(
        lon,
        lat,
        timeseries_cm[0],
        cmap="RdYlBu_r",
        vmin=vmin,
        vmax=vmax,
        shading="auto",
    )

    # Reference point
    ref_lon = lon[int(metadata["REF_Y"]), int(metadata["REF_X"])]
    ref_lat = lat[int(metadata["REF_Y"]), int(metadata["REF_X"])]
    ax.plot(
        ref_lon,
        ref_lat,
        "ks",
        markersize=10,
        markerfacecolor="black",
        markeredgecolor="white",
        markeredgewidth=2,
        label="Reference Point",
    )[0]

    ax.set_xlabel("Longitude (°E)", fontsize=12)
    ax.set_ylabel("Latitude (°N)", fontsize=12)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.legend(loc="upper right")

    ref_date = metadata.get("REF_DATE", dates[0])
    if isinstance(ref_date, bytes):
        ref_date = ref_date.decode()
    title = ax.set_title(
        f"N = 0, Time = {dates[0]}\nReference: N = 0, Time = {ref_date}",
        fontsize=14,
        weight="bold",
    )

    cbar = plt.colorbar(im, ax=ax, orientation="vertical", pad=0.02, shrink=0.8)
    cbar.set_label("Displacement [cm]", fontsize=12)

    # Slider
    ax_slider = plt.axes([0.15, 0.05, 0.7, 0.03])
    slider = Slider(ax_slider, "Image", 0, len(dates) - 1, valinit=0, valstep=1)

    def update(val):
        idx = int(slider.val)
        im.set_array(timeseries_cm[idx].ravel())
        title.set_text(
            f"N = {idx}, Time = {dates[idx]}\nReference: N = 0, Time = {ref_date}"
        )
        fig.canvas.draw_idle()

    slider.on_changed(update)

    plt.show()


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Visualize InSAR timeseries and velocity data with geographic coordinates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Plot timeseries at specific date
  %(prog)s results/seoul-insar/timeseries.h5 --date-idx 44 --output displacement.png

  # Interactive timeseries viewer with slider
  %(prog)s results/seoul-insar/timeseries.h5 --interactive

  # Plot velocity map
  %(prog)s results/seoul-insar/velocity.h5 --output velocity.png

  # Custom color scale
  %(prog)s results/seoul-insar/velocity.h5 --vmin -5 --vmax 5 --cmap jet
        """,
    )

    parser.add_argument("input", help="Input HDF5 file (timeseries.h5 or velocity.h5)")
    parser.add_argument(
        "--date-idx",
        type=int,
        default=None,
        help="Date index to plot (default: last date). Only for timeseries files.",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Launch interactive viewer with slider. Only for timeseries files.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output file path to save the figure (e.g., output.png)",
    )
    parser.add_argument(
        "--cmap", type=str, default="RdYlBu_r", help="Colormap name (default: RdYlBu_r)"
    )
    parser.add_argument(
        "--vmin",
        type=float,
        default=None,
        help="Minimum value for color scale (cm for timeseries, cm/year for velocity)",
    )
    parser.add_argument(
        "--vmax",
        type=float,
        default=None,
        help="Maximum value for color scale (cm for timeseries, cm/year for velocity)",
    )
    parser.add_argument("--title", type=str, default=None, help="Custom plot title")

    args = parser.parse_args()

    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found.")
        exit(1)

    # Determine file type
    is_velocity = "velocity" in args.input.lower()

    if is_velocity:
        # Plot velocity
        if args.interactive:
            print(
                "Warning: --interactive mode is only supported for timeseries files. Ignoring."
            )

        plot_velocity_geographic(
            args.input,
            cmap=args.cmap,
            vmin=args.vmin,
            vmax=args.vmax,
            title=args.title or "Mean LOS Velocity",
            save_path=args.output,
        )
    else:
        # Plot timeseries
        if args.interactive:
            if args.output:
                print(
                    "Warning: --output is not supported in interactive mode. Ignoring."
                )
            interactive_timeseries_viewer(args.input)
        else:
            plot_timeseries_geographic(
                args.input,
                date_idx=args.date_idx,
                cmap=args.cmap,
                vmin=args.vmin,
                vmax=args.vmax,
                title=args.title,
                save_path=args.output,
            )
