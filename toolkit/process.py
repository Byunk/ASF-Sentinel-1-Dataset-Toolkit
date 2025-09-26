"""
Process Sentinel-1 data using HyP3

References:
- https://hyp3-docs.asf.alaska.edu/using/sdk/
"""

import os
from pathlib import Path
from hyp3_sdk import HyP3, Batch


class InSARProcessor:
    """
    Sentinel-1 InSAR data processor using HyP3
    """

    def __init__(self, username: str | None = None, password: str | None = None):
        if not username:
            username = os.getenv("HYP3_USERNAME")
        if not password:
            password = os.getenv("HYP3_PASSWORD")
        if not username or not password:
            raise ValueError("Username and password are required")

        self.hyp3 = HyP3(username=username, password=password)

    def submit(
        self,
        reference_granule_id: str,
        granule_list: list[str],
        location: Path | str = ".",
        **kwargs,
    ) -> None:
        """
        Submit a batch of InSAR jobs

        Args:
            reference_granule_id: The ID of the reference granule
            granule_list: The list of secondary granules to process
            location: The location to download the files to
            **kwargs: Additional arguments to pass to the `HyP3.submit_insar_job` method

        Returns:
            None
        """
        jobs = Batch()
        for granule in granule_list:
            jobs += self.hyp3.submit_insar_job(reference_granule_id, granule, **kwargs)
        jobs = self.hyp3.watch(jobs)
        jobs.download_files(location)
