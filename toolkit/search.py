"""
Perform a search for the ASF catalog

References:
- https://docs.asf.alaska.edu/asf_search/basics/
- https://github.com/asfadmin/Discovery-asf_search/blob/master/examples/0-Intro.md
"""

from datetime import datetime, timezone
import logging
from pathlib import Path

import asf_search as asf
import pandas as pd
from dateutil.parser import parse as parse_date

logger = logging.getLogger(__name__)


def read_ids_from_file(file_path: str) -> list[str]:
    """
    Read product IDs from a text file

    Args:
        file_path: Path to text file containing product IDs (one per line)

    Returns:
        List of product IDs
    """
    ids = []
    path = Path(file_path)

    if not path.exists():
        logger.error(f"File not found: {file_path}")
        return ids

    with open(path) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            ids.append(line)

    logger.info(f"Read {len(ids)} IDs from {file_path}")
    return ids


def search_result_to_df(
    search_results: asf.ASFSearchResults,
) -> pd.DataFrame:
    """
    Convert a list of search results to a pandas DataFrame
    """
    columns = list(search_results[0].properties.keys()) + [
        "geometry",
    ]
    data = [
        list(scene.properties.values())
        + [
            scene.geometry,
        ]
        for scene in search_results
    ]
    df = pd.DataFrame(data, columns=columns)
    df["startTime"] = df.startTime.apply(parse_date)
    return df


def baseline_search(
    reference_id: str,
    start_date: datetime | str | None = None,
    end_date: datetime | str | None = None,
) -> pd.DataFrame:
    """
    Search for baselines with a reference ID

    Args:
        reference_id: The ID of the reference granule
        start_date: The start date of the search
        end_date: The end date of the search
    Returns:
        A pandas DataFrame of the search results
    """
    if isinstance(start_date, str):
        start_date = parse_date(start_date).replace(tzinfo=timezone.utc)
    if isinstance(end_date, str):
        end_date = parse_date(end_date).replace(tzinfo=timezone.utc)

    logger.info("Searching for baselines with reference ID: %s", reference_id)
    logger.info("  Start date: %s", start_date)
    logger.info("  End date: %s", end_date)

    baseline_results = asf.stack_from_id(reference_id)

    stack = search_result_to_df(baseline_results)

    if start_date is not None:
        stack = stack.loc[stack.startTime >= start_date]
    if end_date is not None:
        stack = stack.loc[stack.startTime <= end_date]

    logger.info("Found %d results", len(stack))
    return stack


def stack_from_ids(
    ids: list[str],
) -> pd.DataFrame:
    """
    Search for stacks from a list of IDs, and compute temporalBaseline column based on startTime.
    """
    baseline_results = asf.product_search(product_list=ids)

    # Convert to DataFrame
    stack = search_result_to_df(baseline_results)

    # Ensure startTime is datetime, but only parse if not already datetime
    stack["startTime"] = pd.to_datetime(stack["startTime"], utc=True)

    # Compute temporalBaseline in days relative to the earliest startTime
    min_time = stack["startTime"].min()
    stack["temporalBaseline"] = (stack["startTime"] - min_time).dt.total_seconds() / (
        24 * 3600
    )

    logger.info("Found %d results", len(stack))
    return stack


def sbas_pairs(
    stack: pd.DataFrame,
    min_temporal_baseline: int = 0,
    max_temporal_baseline: int = 24,
) -> list[tuple[str, str]]:
    """
    Generate SBAS pairs from a stack based on temporal baseline

    Args:
        stack: A pandas DataFrame of the stack
        min_temporal_baseline: The minimum temporal baseline
        max_temporal_baseline: The maximum temporal baseline

    Returns:
        A set of tuples of the SBAS pairs

    Raises:
        ValueError: If min_temporal_baseline or max_temporal_baseline is not a positive integer
    """
    if not isinstance(min_temporal_baseline, int) or min_temporal_baseline < 0:
        raise ValueError("min_temporal_baseline must be a positive integer")
    if not isinstance(max_temporal_baseline, int) or max_temporal_baseline < 0:
        raise ValueError("max_temporal_baseline must be a positive integer")

    sbas_pairs = set()

    for reference, rt in stack.loc[::-1, ["sceneName", "temporalBaseline"]].itertuples(
        index=False
    ):
        secondaries = stack.loc[
            (stack.sceneName != reference)
            & (stack.temporalBaseline - rt <= max_temporal_baseline)
            & (stack.temporalBaseline - rt > min_temporal_baseline)
        ]
        for secondary in secondaries.sceneName:
            sbas_pairs.add((reference, secondary))

    pairs = list(sbas_pairs)
    pairs.sort(key=lambda x: x[0])
    return pairs


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    with open("input.txt", "r") as f:
        ids = f.readlines()
    ids = [id.strip() for id in ids]

    results = stack_from_ids(ids)
    pairs = sbas_pairs(results, min_temporal_baseline=81, max_temporal_baseline=99)

    # Save the results to a file
    with open("stack_data.txt", "w") as f:
        for item in results.itertuples():
            scene_name = item.sceneName
            start_time = item.startTime
            f.write(f"{scene_name},{start_time}\n")

    with open("sbas_pairs.txt", "w") as f:
        for pair in pairs:
            f.write(f"{pair[0]},{pair[1]}\n")

    logger.info("%d items saved to stack_data.txt", len(results))
    logger.info("%d pairs saved to sbas_pairs.txt", len(pairs))
