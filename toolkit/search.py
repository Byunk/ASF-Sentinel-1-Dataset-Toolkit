"""
Perform a search for the ASF catalog

References:
- https://docs.asf.alaska.edu/asf_search/basics/
- https://github.com/asfadmin/Discovery-asf_search/blob/master/examples/0-Intro.md
"""

from datetime import datetime, timezone
import logging

import asf_search as asf
import pandas as pd
from dateutil.parser import parse as parse_date

logger = logging.getLogger(__name__)


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

    columns = list(baseline_results[0].properties.keys()) + [
        "geometry",
    ]
    data = [
        list(scene.properties.values())
        + [
            scene.geometry,
        ]
        for scene in baseline_results
    ]

    stack = pd.DataFrame(data, columns=columns)
    stack["startTime"] = stack.startTime.apply(parse_date)

    reference = stack.loc[stack.fileID == reference_id].iloc[0]

    # Filter stack by frame number and path number
    stack = stack.loc[
        (reference.frameNumber == stack.frameNumber)
        & (reference.pathNumber == stack.pathNumber)
    ]

    if start_date is not None:
        stack = stack.loc[stack.startTime >= start_date]
    if end_date is not None:
        stack = stack.loc[stack.startTime <= end_date]

    logger.info("Found %d results", len(stack))
    return stack


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    reference_id = (
        "S1A_IW_SLC__1SSV_20141213T093112_20141213T093140_003699_004641_E1DC-SLC"
    )
    results = baseline_search(reference_id)

    # Save the results to a file
    with open("stack_data.txt", "w") as f:
        for item in results.itertuples():
            scene_name = item.sceneName
            start_time = item.startTime
            f.write(f"{scene_name},{start_time}\n")

    logger.info("%d items saved to stack_data.txt", len(results))
