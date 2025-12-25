import fire
from src.pipeline import simple_ocr_pipeline, full_ocr_pipeline
from src.runner import run_archive


class Cli:
    def simple(self, year: int, month: int):
        return simple_ocr_pipeline(year, month)

    def full(self, year: int, month: int):
        return full_ocr_pipeline(year, month)

    def archive(
        self,
        start_year: int = 1925,
        start_month: int = 8,
        end_year: int = 2009,
        end_month: int = 5,
        skip_sync: bool = False,
    ):
        """Process the entire archive month by month."""
        return run_archive(start_year, start_month, end_year, end_month, skip_sync)

    def reset(self):
        """Delete all files in GCS and local data to start fresh."""
        from src.gcs import get_gcs_client, reset_bucket
        client = get_gcs_client()
        reset_bucket(client)
        print("[OK] Reset complete.")


if __name__ == "__main__":
    fire.Fire(Cli)
