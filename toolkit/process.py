"""
Process Sentinel-1 data using HyP3

References:
- https://hyp3-docs.asf.alaska.edu/using/sdk/
"""

import logging
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from hyp3_sdk import HyP3, Batch, Job
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
        batch_size: int = 50,
        project_name: str | None = None,
        output_dir: Path | str = ".",
        download: bool = True,
        dry_run: bool = False,
        **kwargs,
    ) -> None:
        """
        Submit a batch of InSAR jobs with temporal baselines

        Args:
            stack: a pandas DataFrame of the stack
            max_temporal_baseline: the maximum temporal baseline
            batch_size: the number of jobs to submit at a time
            project_name: the name of the project
            output_dir: the directory to save the results
            download: whether to download the results
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

        sbas_pairs_list = list(sbas_pairs)
        for i in range(0, len(sbas_pairs_list), batch_size):
            batch_pairs = sbas_pairs_list[i : i + batch_size]
            batch_jobs = Batch()
            for reference, secondary in tqdm(
                batch_pairs,
                desc=f"Submitting InSAR jobs [{i + 1}-{min(i + batch_size, len(sbas_pairs_list))}]",
                unit="pair",
                disable=not self.logger.isEnabledFor(logging.INFO),
            ):
                try:
                    batch_jobs += self.hyp3.submit_insar_job(
                        reference,
                        secondary,
                        name=project_name,
                        # Compatibility with MintPy
                        include_dem=True,
                        include_look_vectors=True,
                        **kwargs,
                    )
                except Exception as e:
                    self.logger.error(
                        "Error submitting job for pair (%s, %s): %s",
                        reference,
                        secondary,
                        e,
                    )
                    continue

            if len(batch_jobs) == 0:
                self.logger.warning("No jobs were submitted in this batch.")
                continue

            try:
                self.logger.info("Submitting %d jobs", len(batch_jobs))
                self.logger.info("Watching job progress...")
                jobs = self.hyp3.watch(batch_jobs)
                if download:
                    self.logger.info("Downloading files to %s", output_dir)
                    jobs.download_files(output_dir)
            except Exception as e:
                self.logger.error(
                    "Error processing batch [%d-%d]: %s",
                    i + 1,
                    min(i + batch_size, len(sbas_pairs_list)),
                    e,
                )
                continue

    def find_jobs(self, project_name: str) -> Batch:
        """
        Find jobs by project name
        """
        return self.hyp3.find_jobs(name=project_name)

    def download_jobs(
        self,
        jobs: Batch | list[Job],
        output_dir: Path | str = ".",
        max_workers: int = 10,
    ) -> None:
        """
        Download jobs to the output directory using multi-threading

        Args:
            jobs: Batch of jobs to download
            output_dir: Directory to save the downloaded files
            max_workers: Maximum number of concurrent download threads (default: 10)
        """

        def download_single_job(job) -> tuple[Job, Exception | None]:
            try:
                job.download_files(output_dir)
                return job, None
            except Exception as e:
                self.logger.error(f"Failed to download job {job.job_id}: {e}")
                return job, e

        job_list = list(jobs) if not isinstance(jobs, list) else jobs

        if not job_list:
            self.logger.warning("No jobs to download")
            return

        failed_downloads = []
        successful_downloads = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_job = {
                executor.submit(download_single_job, job): job for job in job_list
            }

            with tqdm(total=len(job_list), desc="Downloading jobs", unit="job") as pbar:
                for future in as_completed(future_to_job):
                    job, error = future.result()

                    if error:
                        failed_downloads.append((job, error))
                    else:
                        successful_downloads += 1

                    pbar.update(1)
                    pbar.set_postfix(
                        {
                            "Success": successful_downloads,
                            "Failed": len(failed_downloads),
                        }
                    )

        self.logger.info(
            f"Download complete: {successful_downloads} successful, {len(failed_downloads)} failed"
        )


def download(
    project_name: str,
    output_dir: Path | str = ".",
    max_workers: int = 10,
    start_index: int = 0,
    end_index: int = None,
) -> None:
    """
    Download jobs from the project
    """
    processor = InSARProcessor()
    jobs = processor.find_jobs(project_name)
    jobs = sorted(list(jobs), key=lambda x: x.files[0]["filename"])
    jobs = jobs[start_index:end_index]
    processor.download_jobs(jobs, output_dir, max_workers)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--project-name", type=str, required=True)
    parser.add_argument("--output-dir", type=str, default=".")
    parser.add_argument("--max-workers", type=int, default=10)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--end-index", type=int, default=None)
    args = parser.parse_args()
    download(
        args.project_name,
        args.output_dir,
        args.max_workers,
        args.start_index,
        args.end_index,
    )
