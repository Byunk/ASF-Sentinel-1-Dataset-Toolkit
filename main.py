import logging
from datetime import datetime, timezone
from toolkit.process import InSARProcessor
from toolkit.search import granule_search

logger = logging.getLogger(__name__)
asf_logger = logging.getLogger("asf_search")
asf_logger.setLevel(logging.WARNING)


def main():
    processor = InSARProcessor()

    # Sample granule for Myanmar earthquake 2025.03.28
    base_granule = "S1A_IW_GRDH_1SDV_20250403T113936_20250403T114001_058592_074094_8683"
    start_date = datetime(2024, 1, 1).replace(tzinfo=timezone.utc)
    granules = granule_search([base_granule], start_date=start_date)
    logger.info("Found %d granules", len(granules))

    # Convert the granules to a list of its file IDs
    granule_ids = [granule.properties["sceneName"] for granule in granules]

    # Submit the jobs
    processor.submit(
        granule_ids[0],
        granule_ids[1:],
        location="data",
        looks="10x2",  # Better resolution than 20x4
        include_wrapped_phase=True,
        # apply_water_mask=True,
        # Compatibility with MintPy
        include_dem=True,
        include_look_vectors=True,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    main()
