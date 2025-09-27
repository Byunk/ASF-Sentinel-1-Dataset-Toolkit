import argparse
import logging

from toolkit.process import InSARProcessor
from toolkit.search import baseline_search

logger = logging.getLogger(__name__)
asf_logger = logging.getLogger("asf_search")
asf_logger.setLevel(logging.WARNING)


def main(
    reference_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
    project_name: str | None = None,
    output_dir: str = "data",
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
        apply_water_mask=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "reference_id",
        type=str,
        help="Reference product ID (e.g. S1A_IW_SLC__1SSV_20141213T093112_20141213T093140_003699_004641_E1DC-SLC)",
    )
    parser.add_argument("--start", type=str)
    parser.add_argument("--end", type=str)
    parser.add_argument("--project_name", type=str, help="Optional project name")
    parser.add_argument(
        "--output_dir", type=str, help="Output directory", default="data"
    )
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    args = parse_args()
    main(
        reference_id=args.reference_id,
        start_date=getattr(args, "start", None),
        end_date=getattr(args, "end", None),
        project_name=getattr(args, "project_name", None),
        output_dir=getattr(args, "output_dir", "data"),
    )
