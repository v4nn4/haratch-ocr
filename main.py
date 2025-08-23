from pathlib import Path
import fire

from src.pdf import convert_pdf_pages
from src.extract import extract_all
from src.pipeline import run_issue

issue = "1925-08"
# issue = "1933-02"


class Paths:
    DATA = Path("data")
    GENERATED = DATA / "generated"
    IMAGES = GENERATED / "images"
    OCR = GENERATED / "ocr"
    OUTPUT = Path("output")


class Cli:
    def extract(
        self,
        image_dir=Paths.IMAGES / issue,
        output_dir=Paths.OCR / issue,
        pdf_path=None,
    ):
        if pdf_path:
            print("Converting PDF to images...")
            convert_pdf_pages(pdf_path, image_dir)
        extract_all(image_dir, output_dir)

    def run(self, year: int, month: int):
        return run_issue(year, month)


if __name__ == "__main__":
    fire.Fire(Cli)
