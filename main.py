import logging
from datetime import datetime, timezone
from toolkit.process import InSARProcessor
from toolkit.search import granule_search

logger = logging.getLogger(__name__)
asf_logger = logging.getLogger("asf_search")
asf_logger.setLevel(logging.WARNING)


def main():
    processor = InSARProcessor()

    # Sample granule for Myanmar earthquake
    base_granule = "S1A_IW_SLC__1SDV_20240315T113941_20240315T114008_052992_066A52_7EFF"
    start_date = datetime(2025, 1, 1).replace(tzinfo=timezone.utc)
    end_date = datetime(2025, 4, 1).replace(tzinfo=timezone.utc)
    granules = granule_search([base_granule], start_date=start_date, end_date=end_date)
    logger.info("Found %d granules", len(granules))

    # Convert the granules to a list of its file IDs
    granule_ids = [granule.properties["sceneName"] for granule in granules if granule.properties["sceneName"] != base_granule]

    # Submit the jobs
    processor.submit(
        base_granule,
        granule_ids,
        location="data",
        looks="10x2",  # Better resolution than 20x4
        include_wrapped_phase=True,
        include_los_displacement=True,
        include_displacement_maps=True,
        apply_water_mask=True,
        # Compatibility with MintPy
        include_dem=True,
        include_look_vectors=True,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    main()
