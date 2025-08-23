import requests
from pathlib import Path


def download_issue(year: int, month: int) -> Path:
    month_names = [
        "Janvier", "Fevrier", "Mars", "Avril", "Mai", "Juin",
        "Juillet", "Aout", "Septembre", "Octobre", "Novembre", "Decembre"
    ]
    
    month_name = month_names[month - 1]
    filename = f"HARATCH_{year}_{month:02d}-{month_name}.pdf"
    url = f"https://archives.webaram.com/presse/haratch/pdf/{filename}"
    
    output_dir = Path("data") / "pdfs"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    
    if output_path.exists():
        return output_path
    
    response = requests.get(url)
    response.raise_for_status()
    
    with output_path.open("wb") as f:
        f.write(response.content)
    
    return output_path
