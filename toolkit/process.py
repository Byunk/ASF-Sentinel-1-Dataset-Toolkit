"""
Process Sentinel-1 data using HyP3

References:
- https://hyp3-docs.asf.alaska.edu/using/sdk/
"""

import logging
import os
from pathlib import Path
from hyp3_sdk import HyP3, Batch
import pandas as pd
from tqdm import tqdm


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
        self.logger = logging.getLogger(__name__)

    def submit_with_temporal_baselines(
        self,
        stack: pd.DataFrame,
        max_temporal_baseline: int = 24,
        project_name: str | None = None,
        output_dir: Path | str = ".",
        dry_run: bool = False,
        **kwargs,
    ) -> None:
        """
        Submit a batch of InSAR jobs with temporal baselines

        Args:
            stack: a pandas DataFrame of the stack
            max_temporal_baseline: the maximum temporal baseline
            project_name: the name of the project
            output_dir: the directory to save the results
            dry_run: whether to dry run the job submission
            **kwargs: additional arguments to pass to the hyp3.submit_insar_job method

        Returns:
            None
        """
        sbas_pairs = set()

        for reference, rt in stack.loc[
            ::-1, ["sceneName", "temporalBaseline"]
        ].itertuples(index=False):
            secondaries = stack.loc[
                (stack.sceneName != reference)
                & (stack.temporalBaseline - rt <= max_temporal_baseline)
                & (stack.temporalBaseline - rt > 0)
            ]
            for secondary in secondaries.sceneName:
                sbas_pairs.add((reference, secondary))

        self.logger.info("Submitting %d pairs", len(sbas_pairs))
        if dry_run:
            self.logger.info("Dry run, not submitting jobs")
            return

        # Check if there are enough credits to submit jobs
        cost_per_pair = 10 if kwargs.get("looks", "20x4") == "20x4" else 15
        total_cost = len(sbas_pairs) * cost_per_pair
        credits = self.hyp3.check_credits()
        if total_cost > credits:
            self.logger.error("Not enough credits to submit jobs")
            return

        jobs = Batch()

        try:
            for reference, secondary in tqdm(
                sbas_pairs,
                desc="Submitting InSAR jobs",
                unit="pair",
                disable=not self.logger.isEnabledFor(logging.INFO),
            ):
                jobs += self.hyp3.submit_insar_job(
                    reference,
                    secondary,
                    name=project_name,
                    # Compatibility with MintPy
                    include_dem=True,
                    include_look_vectors=True,
                    **kwargs,
                )
        except Exception as e:
            self.logger.error("Error submitting jobs: %s", e)

        self.logger.info("Watching job progress...")
        jobs = self.hyp3.watch(jobs)
        self.logger.info("Downloading files to %s", output_dir)
        jobs.download_files(output_dir)
