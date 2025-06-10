from pathlib import Path
import fire

from src.pdf import convert_pdf_pages
from src.extract import extract_all
from src.translate import translate_folder

issue = "1925-08"
# issue = "1933-02"


class Paths:
    DATA = Path("data")
    GENERATED = DATA / "generated"
    IMAGES = GENERATED / "images"
    OCR = GENERATED / "ocr"
    OUTPUT = Path("output")
    TRANSLATIONS = OUTPUT / "translations"


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

    def translate(
        self,
        input_dir=Paths.IMAGES / issue,
        output_dir=Paths.TRANSLATIONS / issue,
        min_length=200,
    ):
        translate_folder(input_dir, output_dir, min_length)


if __name__ == "__main__":
    fire.Fire(Cli)
