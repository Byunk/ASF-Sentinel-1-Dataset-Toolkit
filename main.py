import argparse
import logging
import os
from pathlib import Path

from toolkit.hyp3 import HyP3Client
from toolkit.insar import (
    clip_hyp3_products_to_common_overlap,
    get_common_overlap,
    interactive_timeseries_viewer,
    plot_velocity_geographic,
)
from toolkit.process import InSARProcessor
from toolkit.search import baseline_search

logger = logging.getLogger(__name__)
asf_logger = logging.getLogger("asf_search")
asf_logger.setLevel(logging.WARNING)


def process_command(
    reference_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
    project_name: str | None = None,
    output_dir: str = "data",
    download: bool = True,
    dry_run: bool = False,
    water_mask: bool = False,
):
    stack = baseline_search(reference_id, start_date=start_date, end_date=end_date)

    processor = InSARProcessor()
    processor.submit_with_temporal_baselines(
        stack,
        project_name=project_name,
        output_dir=output_dir,
        looks="10x2",  # Better resolution than 20x4
        include_wrapped_phase=True,
        include_los_displacement=True,
        include_displacement_maps=True,
        apply_water_mask=water_mask,
        download=download,
        dry_run=dry_run,
    )


def download_command(
    project_name: str,
    output_dir: str = "data",
    max_workers: int = 10,
):
    username = os.getenv("HYP3_USERNAME")
    password = os.getenv("HYP3_PASSWORD")

    if not username or not password:
        logger.error("HYP3_USERNAME and HYP3_PASSWORD environment variables required")
        return

    client = HyP3Client(username=username, password=password)
    logger.info(f"Finding jobs for project: {project_name}")
    jobs = client.find_jobs(project_name)

    if not jobs:
        logger.warning(f"No jobs found for project: {project_name}")
        return

    logger.info(f"Found {len(jobs)} jobs")
    client.download(jobs, output_dir=output_dir, max_workers=max_workers)


def clip_command(data_dir: str = "data"):
    data_path = Path(data_dir)
    logger.info(f"Finding DEM files in {data_path}")
    files = list(data_path.glob("*/*_dem.tif"))

    if not files:
        logger.warning(f"No DEM files found in {data_path}")
        return

    logger.info(f"Found {len(files)} DEM files")
    logger.info("Calculating common overlap")
    overlap = get_common_overlap(files)
    logger.info(f"Common overlap: {overlap}")
    logger.info("Clipping GeoTIFF files to common overlap")
    clip_hyp3_products_to_common_overlap(data_path, overlap)
    logger.info("Clipping complete")


def visualize_command(
    input_file: str, output: str | None = None, title: str | None = None
):
    if not os.path.exists(input_file):
        logger.error(f"Input file '{input_file}' not found.")
        return

    # Determine file type
    is_velocity = "velocity" in input_file.lower()

    if is_velocity:
        # Plot velocity (static plot)
        logger.info(f"Visualizing velocity from {input_file}")
        plot_velocity_geographic(
            input_file,
            title=title or "Mean LOS Velocity",
            save_path=output,
        )
    else:
        # Plot timeseries (interactive by default)
        if output:
            logger.warning("--output is not supported in interactive mode. Ignoring.")
        logger.info(f"Launching interactive timeseries viewer for {input_file}")
        interactive_timeseries_viewer(input_file)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ASF Sentinel-1 InSAR Toolkit")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Process subcommand
    process_parser = subparsers.add_parser(
        "process", help="Search and process InSAR pairs"
    )
    process_parser.add_argument(
        "reference_id",
        type=str,
        help="Reference product ID (e.g. S1A_IW_SLC__1SSV_20141213T093112_20141213T093140_003699_004641_E1DC-SLC)",
    )
    process_parser.add_argument("--start", type=str, help="Start date")
    process_parser.add_argument("--end", type=str, help="End date")
    process_parser.add_argument(
        "--project-name", type=str, help="Optional project name"
    )
    process_parser.add_argument(
        "--output-dir", type=str, help="Output directory", default="data"
    )
    process_parser.add_argument(
        "--no-download",
        action="store_true",
        default=False,
        help="Skip downloading processed results",
    )
    process_parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Dry run without submitting jobs",
    )
    process_parser.add_argument(
        "--water-mask",
        action="store_true",
        default=False,
        help="Apply water mask to the processing (default: False)",
    )

    # Download subcommand
    download_parser = subparsers.add_parser(
        "download", help="Download jobs from a project"
    )
    download_parser.add_argument(
        "--project-name", type=str, required=True, help="Project name to download from"
    )
    download_parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Output directory (default: data)",
    )
    download_parser.add_argument(
        "--max-workers",
        type=int,
        default=10,
        help="Number of concurrent downloads (default: 10)",
    )

    # Clip subcommand
    clip_parser = subparsers.add_parser(
        "clip", help="Clip GeoTIFF files to common overlap"
    )
    clip_parser.add_argument(
        "--data-dir", type=str, default="data", help="Data directory (default: data)"
    )

    # Visualize subcommand
    visualize_parser = subparsers.add_parser(
        "visualize", help="Visualize InSAR timeseries or velocity data"
    )
    visualize_parser.add_argument(
        "input", type=str, help="Input HDF5 file (timeseries.h5 or velocity.h5)"
    )
    visualize_parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output file path to save the figure (e.g., output.png)",
    )
    visualize_parser.add_argument(
        "--title", type=str, default=None, help="Custom plot title"
    )

    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    args = parse_args()

    if args.command == "process":
        process_command(
            reference_id=args.reference_id,
            start_date=getattr(args, "start", None),
            end_date=getattr(args, "end", None),
            project_name=getattr(args, "project_name", None),
            output_dir=getattr(args, "output_dir", "data"),
            download=not getattr(args, "no_download", False),
            dry_run=getattr(args, "dry_run", False),
            water_mask=getattr(args, "water_mask", False),
        )
    elif args.command == "download":
        download_command(
            project_name=args.project_name,
            output_dir=args.output_dir,
            max_workers=args.max_workers,
        )
    elif args.command == "clip":
        clip_command(data_dir=args.data_dir)
    elif args.command == "visualize":
        visualize_command(
            input_file=args.input,
            output=getattr(args, "output", None),
            title=getattr(args, "title", None),
        )
    else:
        logger.error(
            "No command specified. Use 'process', 'download', 'clip', or 'visualize'."
        )
