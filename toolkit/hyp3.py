"""
Comprehensive InSAR processing toolkit
"""

import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Literal
from hyp3_sdk import HyP3, Batch, Job
import hyp3_sdk
from tqdm import tqdm


class HyP3Client:
    """
    HyP3 client
    """

    def __init__(self, username: str, password: str):
        self.hyp3 = HyP3(username=username, password=password)
        self.logger = logging.getLogger(__name__)

    def submit_insar_job(
        self,
        pairs: list[tuple[str, str]],
        project_name: str | None = None,
        output_dir: Path | str = ".",
        download: bool = True,
        looks: Literal["10x2", "20x4"] = "10x2",
        water_mask: bool = False,
        wait: bool = True,
    ) -> None:
        """
        Submit an InSAR job
        """
        if not pairs:
            self.logger.warning("No pairs to submit")
            return

        # Check if there are enough credits to submit jobs
        cost_per_pair = 15 if looks == "10x2" else 10
        total_cost = len(pairs) * cost_per_pair
        credits = self.hyp3.check_credits()
        if total_cost > credits:
            self.logger.error("Not enough credits to submit jobs")
            return

        batch = Batch()
        for reference, secondary in pairs:
            batch += self.hyp3.submit_insar_job(
                reference,
                secondary,
                name=project_name,
                include_inc_map=True,
                looks=looks,
                apply_water_mask=water_mask,
                include_wrapped_phase=True,
                include_displacement_maps=True,
                # Compatibility with MintPy
                include_dem=True,
                include_look_vectors=True,
            )

        if wait:
            batch = self.hyp3.watch(batch)
            if download:
                self.logger.info("Downloading files to %s", output_dir)
                batch.download_files(output_dir)
        else:
            self.logger.info("Jobs submitted. Not waiting for completion.")
            if download:
                self.logger.warning(
                    "Download skipped because --no-wait was specified. "
                    "Use 'download' command later to retrieve results."
                )

    def submit_insar_burst_job(
        self,
        pairs: list[tuple[str, str]],
        project_name: str | None = None,
        output_dir: Path | str = ".",
        download: bool = True,
        looks: Literal["20x4", "10x2", "5x1"] = "5x1",
        water_mask: bool = False,
        wait: bool = True,
    ) -> None:
        """
        Submit an InSAR burst job
        """
        if not pairs:
            self.logger.warning("No pairs to submit")
            return

        # Check if there are enough credits to submit jobs
        cost_per_pair = 1
        total_cost = len(pairs) * cost_per_pair
        credits = self.hyp3.check_credits()
        if total_cost > credits:
            self.logger.error("Not enough credits to submit jobs")
            return

        batch = Batch()
        for reference, secondary in pairs:
            batch += self.hyp3.submit_insar_isce_burst_job(
                reference,
                secondary,
                name=project_name,
                looks=looks,
                apply_water_mask=water_mask,
            )

        if wait:
            batch = self.hyp3.watch(batch)
            if download:
                self.logger.info("Downloading files to %s", output_dir)
                batch.download_files(output_dir)
        else:
            self.logger.info("Jobs submitted. Not waiting for completion.")
            if download:
                self.logger.warning(
                    "Download skipped because --no-wait was specified. "
                    "Use 'download' command later to retrieve results."
                )

    def find_jobs(self, project_name: str) -> Batch:
        """
        Find jobs by project name
        """
        return self.hyp3.find_jobs(name=project_name)

    def download(
        self,
        jobs: Batch | list[Job],
        output_dir: Path | str = "data",
        max_workers: int = 10,
    ) -> None:
        """
        Download jobs to the output directory using multi-threading

        Args:
            jobs: Batch of jobs to download
            output_dir: Directory to save the downloaded files
            max_workers: Maximum number of concurrent download threads (default: 10)
        """

        def download_single_job(job: Job) -> bool:
            try:
                p = job.download_files(output_dir)
                p = [hyp3_sdk.util.extract_zipped_product(pp) for pp in p]
                return True
            except Exception as e:
                self.logger.error(f"Failed to download job {job.job_id}: {e}")
                return False

        job_list = list(jobs) if not isinstance(jobs, list) else jobs
        if not job_list:
            self.logger.warning("No jobs to download")
            return

        failed_downloads = 0
        successful_downloads = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_success = {
                executor.submit(download_single_job, job): job for job in job_list
            }

            with tqdm(total=len(job_list), desc="Downloading jobs", unit="job") as pbar:
                for future in as_completed(future_to_success):
                    success = future.result()

                    if not success:
                        failed_downloads += 1
                    else:
                        successful_downloads += 1

                    pbar.update(1)
                    pbar.set_postfix(
                        {
                            "Success": successful_downloads,
                            "Failed": failed_downloads,
                        }
                    )

        self.logger.info(
            f"Download complete: {successful_downloads} successful, {failed_downloads} failed"
        )
