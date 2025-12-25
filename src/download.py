import requests
from pathlib import Path


from .paths import get_pdf_path


def download_issue(year: int, month: int) -> Path:
    output_path = get_pdf_path(year, month)
    
    if output_path.exists():
        return output_path

    filename = output_path.name
    url = f"https://archives.webaram.com/presse/haratch/pdf/{filename}"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    response = requests.get(url)
    response.raise_for_status()
    
    with output_path.open("wb") as f:
        f.write(response.content)
    
    return output_path
