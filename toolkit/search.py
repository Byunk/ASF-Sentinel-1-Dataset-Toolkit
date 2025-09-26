"""
Perform a search for the ASF catalog

References:
- https://docs.asf.alaska.edu/asf_search/basics/
- https://github.com/asfadmin/Discovery-asf_search/blob/master/examples/0-Intro.md
"""

from datetime import datetime
from typing import Any

import asf_search as asf


def granule_search(
    granule_list: list[str],
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[Any]:
    """
    Baseline search for the given granule

    Args:
        granule_list: List of granules to search for
        start_date: Start date to filter the stack by
        end_date: End date to filter the stack by

    Returns:
        List of granules that match the given conditions
    """
    results = asf.granule_search(granule_list)
    reference = results[0]
    stack = reference.stack()

    # Filter stack by the given conditions
    filtered = []
    for item in stack:
        item_start_time = datetime.fromisoformat(
            item.properties["startTime"].replace("Z", "+00:00")
        )
        if start_date is not None and item_start_time < start_date:
            continue
        if end_date is not None and item_start_time > end_date:
            continue
        filtered.append(item)

    return filtered


if __name__ == "__main__":
    results = granule_search(
        ["S1A_IW_GRDH_1SDV_20250403T113936_20250403T114001_058592_074094_8683"]
    )

    # Save the results to a file
    with open("stack_data.txt", "w") as f:
        for item in results:
            file_id = item.properties["fileID"]
            start_time = item.properties["startTime"]
            f.write(f"{file_id},{start_time}\n")
