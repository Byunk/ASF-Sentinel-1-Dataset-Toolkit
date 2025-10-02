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
from toolkit.search import read_ids_from_file, sbas_pairs, stack_from_ids

logger = logging.getLogger(__name__)
asf_logger = logging.getLogger("asf_search")
asf_logger.setLevel(logging.WARNING)


def process_insar_command(
    input_file: str,
    project_name: str | None = None,
    output_dir: str = "data",
    download: bool = True,
    water_mask: bool = False,
    looks: str = "10x2",
    min_temporal_baseline: int = 0,
    max_temporal_baseline: int = 24,
    dry_run: bool = False,
):
    username = os.getenv("HYP3_USERNAME")
    password = os.getenv("HYP3_PASSWORD")

    if not username or not password:
        logger.error("HYP3_USERNAME and HYP3_PASSWORD environment variables required")
        return

    ids = read_ids_from_file(input_file)
    if not ids:
        logger.error("No IDs found in input file")
        return

    logger.info(f"Generating stack from {len(ids)} IDs")
    stack = stack_from_ids(ids)

    logger.info(
        f"Generating SBAS pairs (temporal baseline: {min_temporal_baseline}-{max_temporal_baseline} days)"
    )
    pairs = sbas_pairs(stack, min_temporal_baseline, max_temporal_baseline)
    logger.info(f"Generated {len(pairs)} pairs")

    if not pairs:
        logger.error("No pairs generated")
        return

    if dry_run:
        logger.info(f"DRY RUN: Would process {len(pairs)} pairs:")
        for reference, secondary in pairs:
            print(f"{reference},{secondary}")
        return

    client = HyP3Client(username=username, password=password)
    client.submit_insar_job(
        pairs=pairs,
        project_name=project_name,
        output_dir=output_dir,
        download=download,
        looks=looks,
        water_mask=water_mask,
    )


def process_insar_burst_command(
    input_file: str,
    project_name: str | None = None,
    output_dir: str = "data",
    download: bool = True,
    water_mask: bool = False,
    looks: str = "5x1",
    min_temporal_baseline: int = 0,
    max_temporal_baseline: int = 24,
    dry_run: bool = False,
):
    username = os.getenv("HYP3_USERNAME")
    password = os.getenv("HYP3_PASSWORD")

    if not username or not password:
        logger.error("HYP3_USERNAME and HYP3_PASSWORD environment variables required")
        return

    ids = read_ids_from_file(input_file)
    if not ids:
        logger.error("No IDs found in input file")
        return

    logger.info(f"Generating stack from {len(ids)} IDs")
    stack = stack_from_ids(ids)

    logger.info(
        f"Generating SBAS pairs (temporal baseline: {min_temporal_baseline}-{max_temporal_baseline} days)"
    )
    pairs = sbas_pairs(stack, min_temporal_baseline, max_temporal_baseline)
    logger.info(f"Generated {len(pairs)} pairs")

    if not pairs:
        logger.error("No pairs generated")
        return

    if dry_run:
        logger.info(f"DRY RUN: Would process {len(pairs)} pairs:")
        for reference, secondary in pairs:
            print(f"{reference},{secondary}")
        return

    client = HyP3Client(username=username, password=password)
    client.submit_insar_burst_job(
        pairs=pairs,
        project_name=project_name,
        output_dir=output_dir,
        download=download,
        looks=looks,
        water_mask=water_mask,
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

    # Process subcommand with nested subcommands
    process_parser = subparsers.add_parser("process", help="Process InSAR jobs")
    process_subparsers = process_parser.add_subparsers(
        dest="process_type", help="Processing type"
    )

    # Process InSAR subcommand
    insar_parser = process_subparsers.add_parser("insar", help="Process InSAR pairs")
    insar_parser.add_argument(
        "input_file",
        type=str,
        help="Text file containing product IDs (one per line)",
    )
    insar_parser.add_argument("--project-name", type=str, help="HyP3 project name")
    insar_parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Output directory (default: data)",
    )
    insar_parser.add_argument(
        "--no-download",
        action="store_true",
        default=False,
        help="Skip downloading processed results",
    )
    insar_parser.add_argument(
        "--water-mask",
        action="store_true",
        default=False,
        help="Apply water mask (default: False)",
    )
    insar_parser.add_argument(
        "--looks",
        type=str,
        default="10x2",
        choices=["10x2", "20x4"],
        help="Resolution setting (default: 10x2)",
    )
    insar_parser.add_argument(
        "--min-temporal-baseline",
        type=int,
        default=0,
        help="Minimum temporal baseline in days (default: 0)",
    )
    insar_parser.add_argument(
        "--max-temporal-baseline",
        type=int,
        default=24,
        help="Maximum temporal baseline in days (default: 24)",
    )
    insar_parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Show pairs that would be processed without submitting jobs",
    )

    # Process InSAR Burst subcommand
    insar_burst_parser = process_subparsers.add_parser(
        "insar-burst", help="Process InSAR burst pairs"
    )
    insar_burst_parser.add_argument(
        "input_file",
        type=str,
        help="Text file containing product IDs (one per line)",
    )
    insar_burst_parser.add_argument(
        "--project-name", type=str, help="HyP3 project name"
    )
    insar_burst_parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Output directory (default: data)",
    )
    insar_burst_parser.add_argument(
        "--no-download",
        action="store_true",
        default=False,
        help="Skip downloading processed results",
    )
    insar_burst_parser.add_argument(
        "--water-mask",
        action="store_true",
        default=False,
        help="Apply water mask (default: False)",
    )
    insar_burst_parser.add_argument(
        "--looks",
        type=str,
        default="5x1",
        choices=["20x4", "10x2", "5x1"],
        help="Resolution setting (default: 5x1)",
    )
    insar_burst_parser.add_argument(
        "--min-temporal-baseline",
        type=int,
        default=0,
        help="Minimum temporal baseline in days (default: 0)",
    )
    insar_burst_parser.add_argument(
        "--max-temporal-baseline",
        type=int,
        default=24,
        help="Maximum temporal baseline in days (default: 24)",
    )
    insar_burst_parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Show pairs that would be processed without submitting jobs",
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
        if args.process_type == "insar":
            process_insar_command(
                input_file=args.input_file,
                project_name=getattr(args, "project_name", None),
                output_dir=getattr(args, "output_dir", "data"),
                download=not getattr(args, "no_download", False),
                water_mask=getattr(args, "water_mask", False),
                looks=getattr(args, "looks", "10x2"),
                min_temporal_baseline=getattr(args, "min_temporal_baseline", 0),
                max_temporal_baseline=getattr(args, "max_temporal_baseline", 24),
                dry_run=getattr(args, "dry_run", False),
            )
        elif args.process_type == "insar-burst":
            process_insar_burst_command(
                input_file=args.input_file,
                project_name=getattr(args, "project_name", None),
                output_dir=getattr(args, "output_dir", "data"),
                download=not getattr(args, "no_download", False),
                water_mask=getattr(args, "water_mask", False),
                looks=getattr(args, "looks", "5x1"),
                min_temporal_baseline=getattr(args, "min_temporal_baseline", 0),
                max_temporal_baseline=getattr(args, "max_temporal_baseline", 24),
                dry_run=getattr(args, "dry_run", False),
            )
        else:
            logger.error(
                "No process type specified. Use 'process insar' or 'process insar-burst'."
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
