from pathlib import Path

def get_issue_id(year: int, month: int) -> str:
    """Generate a standard issue ID."""
    return f"{year}-{month:02d}"

def get_pdf_path(year: int, month: int, data_dir: Path = Path("data")) -> Path:
    """Get the path to the PDF file for a specific issue."""
    month_names = [
        "Janvier", "Fevrier", "Mars", "Avril", "Mai", "Juin",
        "Juillet", "Aout", "Septembre", "Octobre", "Novembre", "Decembre"
    ]
    month_name = month_names[month - 1]
    filename = f"HARATCH_{year}_{month:02d}-{month_name}.pdf"
    return data_dir / "pdfs" / filename

def get_image_dir(year: int, month: int, data_dir: Path = Path("data")) -> Path:
    """Get the path to the directory containing extracted images for an issue."""
    issue_id = get_issue_id(year, month)
    return data_dir / "generated" / "images" / issue_id

def get_ocr_dir(year: int, month: int, data_dir: Path = Path("data")) -> Path:
    """Get the path to the directory containing OCR results for an issue."""
    issue_id = get_issue_id(year, month)
    return data_dir / "generated" / "ocr" / issue_id

def get_output_dir(year: int, month: int, data_dir: Path = Path("data")) -> Path:
    """Get the path to the directory containing final output for an issue."""
    issue_id = get_issue_id(year, month)
    return data_dir / "output" / issue_id
