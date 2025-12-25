import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


def get_pdf_page_count(pdf_path: Path) -> int:
    """Get the total number of pages in a PDF using pdfinfo."""
    try:
        result = subprocess.run(
            ["pdfinfo", str(pdf_path)],
            capture_output=True,
            text=True,
            check=True
        )
        for line in result.stdout.splitlines():
            if line.startswith("Pages:"):
                return int(line.split(":")[1].strip())
    except Exception as e:
        print(f"[ERROR] Failed to get page count for {pdf_path.name}: {e}")
    return 0


def convert_single_page(pdf_path: Path, output_path: Path, page_num: int):
    """Convert a single page of a PDF to a PNG image."""
    try:
        subprocess.run(
            [
                "pdftoppm", 
                "-png", 
                "-r", "300", 
                "-f", str(page_num), 
                "-l", str(page_num), 
                "-singlefile", 
                str(pdf_path), 
                str(output_path.with_suffix(""))
            ],
            check=True,
            capture_output=True
        )
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error converting page {page_num}: {e.stderr.decode()}")
        return None


def convert_pdf_pages(pdf_path: Path, output_dir: Path):
    """
    Convert all PDF pages to images in parallel and yield them as they finish.
    (Yielding allows for a producer-consumer overlap with OCR).
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    page_count = get_pdf_page_count(pdf_path)
    if page_count == 0:
        print(f"[WARNING] PDF {pdf_path.name} seems empty or unreadable.")
        return

    # Check for existing images to support resume
    existing_images = sorted(list(output_dir.glob("page_*.png")))
    if len(existing_images) == page_count:
        print(f"[OK] All {page_count} images already exist in {output_dir}, streaming existing files.")
        for img in existing_images:
            yield img
        return

    print(f"[INFO] Streaming conversion of {pdf_path.name} ({page_count} pages) using parallel workers...")
    
    image_paths = [output_dir / f"page_{i}.png" for i in range(page_count)]
    
    # We use ThreadPoolExecutor to run multiple pdftoppm processes in parallel.
    max_workers = 10
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(convert_single_page, pdf_path, image_paths[i], i + 1): i
            for i in range(page_count)
        }
        
        for future in as_completed(futures):
            res = future.result()
            if res:
                yield res
