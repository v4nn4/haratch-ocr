from pathlib import Path
from pdf2image import convert_from_path
from PyPDF2 import PdfReader


def convert_pdf_pages(pdf_path: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    total_pages = len(PdfReader(str(pdf_path)).pages)
    image_paths = []

    for i in range(total_pages):
        pages = convert_from_path(
            str(pdf_path), dpi=300, first_page=i + 1, last_page=i + 1
        )
        image_path = output_dir / f"page_{i}.png"
        pages[0].save(image_path, "PNG")
        image_paths.append(image_path)

    return image_paths
