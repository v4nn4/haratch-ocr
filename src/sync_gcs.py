from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from .gcs import get_gcs_client, ensure_bucket_exists, upload_file

def sync_all_jsons():
    """Sync all OCR and Output JSON files to GCS in parallel."""
    client = get_gcs_client()
    bucket = ensure_bucket_exists(client)
    
    data_dir = Path("data")
    
    files_to_sync = []
    
    # 1. Collect OCR files
    ocr_root = data_dir / "generated" / "ocr"
    if ocr_root.exists():
        for json_file in ocr_root.rglob("*.json"):
            rel_path = json_file.relative_to(ocr_root)
            blob_name = f"ocr/{rel_path}"
            files_to_sync.append((json_file, blob_name))
    
    # 2. Collect Output files
    output_root = data_dir / "output"
    if output_root.exists():
        for json_file in output_root.rglob("*.json"):
            rel_path = json_file.relative_to(output_root)
            blob_name = f"output/{rel_path}"
            files_to_sync.append((json_file, blob_name))

    if not files_to_sync:
        print("[SYNC] No files found to sync.")
        return

    print(f"[SYNC] Syncing {len(files_to_sync)} files to GCS using parallel workers...")
    
    # Use a ThreadPoolExecutor for parallel uploads
    # GCS Client is thread-safe for diverse operations
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {executor.submit(upload_file, bucket, f, b): b for f, b in files_to_sync}
        
        count = 0
        for future in as_completed(futures):
            try:
                if future.result():
                    count += 1
            except Exception as e:
                print(f"[ERROR] Failed to upload {futures[future]}: {e}")

    print(f"[DONE] Sync complete. Uploaded {count} new files.")

if __name__ == "__main__":
    sync_all_jsons()
