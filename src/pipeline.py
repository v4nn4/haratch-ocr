from pathlib import Path
from .download import download_issue
from .pdf import convert_pdf_pages
from .extract import extract_paragraphs_and_lines
import json
from PIL import Image


def process_page(page_path: Path, output_dir: Path) -> dict:
    width, height = Image.open(str(page_path)).size

    results = extract_paragraphs_and_lines(
        page_image_path=str(page_path),
        para_output=None,
        save_crops=False,
        return_bboxes=True,
    )

    json_data = {"metadata": {"width": width, "height": height}, "paragraphs": []}

    for bbox, text in results:
        int_bbox = list(map(int, bbox))
        json_data["paragraphs"].append({"bbox": int_bbox, "hye": text.strip()})

    output_path = output_dir / f"{page_path.stem}.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    return json_data


def run_issue(year: int, month: int) -> dict:
    issue_id = f"{year}-{month:02d}"

    pdf_path = download_issue(year, month)
    image_dir = Path("data") / "generated" / "images" / issue_id
    output_dir = Path("data") / "generated" / "ocr" / issue_id

    image_paths = convert_pdf_pages(pdf_path, image_dir)

    results = []
    for page_path in image_paths:
        result = process_page(page_path, output_dir)
        results.append(result)

    return {"issue": issue_id, "pages": len(results)}
