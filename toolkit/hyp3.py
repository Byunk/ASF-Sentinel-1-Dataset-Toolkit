"""
Comprehensive InSAR processing toolkit
"""

import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from hyp3_sdk import HyP3, Batch, Job
from tqdm import tqdm


class HyP3Client:
    """
    HyP3 client
    """

    def __init__(self, username: str, password: str):
        self.hyp3 = HyP3(username=username, password=password)
        self.logger = logging.getLogger(__name__)

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
