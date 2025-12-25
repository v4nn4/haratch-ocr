import shutil
from pathlib import Path

from .paths import get_issue_id, get_pdf_path, get_image_dir

def cleanup_issue_data(year: int, month: int):
    """
    Delete local generated images AND the source PDF for a specific issue.
    Keep only the JSONs in data/generated/ocr and data/output.
    """
    issue_id = get_issue_id(year, month)
    image_dir = get_image_dir(year, month)
    pdf_path = get_pdf_path(year, month)
    
    # 1. Cleanup images
    if image_dir.exists():
        print(f"[CLEANUP] Removing local images in {image_dir}...")
        try:
            shutil.rmtree(image_dir)
            print(f"[OK] Cleaned up {issue_id} images.")
        except Exception as e:
            print(f"[ERROR] Failed to cleanup {issue_id} images: {e}")
    
    # 2. Cleanup PDF
    if pdf_path.exists():
        print(f"[CLEANUP] Removing local PDF {pdf_path}...")
        try:
            pdf_path.unlink()
            print(f"[OK] Cleaned up {issue_id} PDF.")
        except Exception as e:
            print(f"[ERROR] Failed to cleanup {issue_id} PDF: {e}")

def cleanup_all_images():
    """Wipe out the entire data/generated/images folder to reclaim space."""
    image_root = Path("data") / "generated" / "images"
    if image_root.exists():
        print(f"[CLEANUP] Purging ALL legacy images in {image_root}...")
        try:
            shutil.rmtree(image_root)
            image_root.mkdir(parents=True, exist_ok=True)
            print("[OK] Global image cleanup complete.")
        except Exception as e:
            print(f"[ERROR] Global image cleanup failed: {e}")

def get_data_folder_size_mb():
    """Calculate the total size of the data/ folder in MB."""
    data_dir = Path("data")
    if not data_dir.exists():
        return 0
    total_size = sum(f.stat().st_size for f in data_dir.rglob('*') if f.is_file())
    return total_size / (1024 * 1024)

def enforce_disk_limit(limit_mb=1000):
    """
    Ensure the data/ folder is below the specified limit.
    If not, this logs a warning. Note: The actual deletion happens
    per issue in cleanup_issue_data to minimize peak usage.
    """
    size = get_data_folder_size_mb()
    if size > limit_mb:
        print(f"[WARNING] Data folder size ({size:.1f}MB) exceeds limit ({limit_mb}MB)!")
        return False
    return True
