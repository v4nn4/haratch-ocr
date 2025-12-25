from google.cloud import storage
from pathlib import Path
import os
from datetime import datetime
import json

PROJECT_ID = "haratch-ocr"
BUCKET_NAME = "haratch-ocr"

def get_gcs_client():
    """Initialize GCS client."""
    return storage.Client(project=PROJECT_ID)

def ensure_bucket_exists(client, bucket_name=BUCKET_NAME):
    """Ensure the bucket exists, create it if not."""
    try:
        bucket = client.get_bucket(bucket_name)
        return bucket
    except Exception:
        print(f"[INIT] Creating bucket: {bucket_name}...")
        return client.create_bucket(bucket_name)

def blob_exists(bucket, blob_name):
    """Check if a blob exists in the bucket."""
    blob = bucket.blob(blob_name)
    return blob.exists()

def upload_file(bucket, local_path, blob_name):
    """Upload a file to GCS if it hasn't changed (or doesn't exist)."""
    if blob_exists(bucket, blob_name):
        return False
    
    print(f"[UPLOAD] Uploading {local_path} to gs://{bucket.name}/{blob_name}...")
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(str(local_path))
    return True
def update_runner_status(client, status="idle", bucket_name=BUCKET_NAME, **kwargs):
    """Write current runner status and health metrics to GCS as JSON."""
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob("status/runner.json")
    
    # Auto-fetch stats if not provided to avoid 0MB logs
    ram_mb = kwargs.get("ram_mb")
    disk_mb = kwargs.get("disk_mb")
    
    if ram_mb is None or disk_mb is None:
        try:
            import psutil
            import os
            from .cleanup import get_data_folder_size_mb
            process = psutil.Process(os.getpid())
            if ram_mb is None:
                ram_mb = process.memory_info().rss / (1024 * 1024)
            if disk_mb is None:
                disk_mb = get_data_folder_size_mb()
        except Exception:
            ram_mb = ram_mb or 0
            disk_mb = disk_mb or 0

    status_data = {
        "status": status,
        "last_updated": datetime.now().isoformat(),
        "ram_mb": ram_mb,
        "disk_mb": disk_mb
    }
    status_data.update(kwargs)
    
    blob.upload_from_string(json.dumps(status_data))
    print(f"[STATUS] Runner is {status.upper()} (RAM: {ram_mb:.1f}MB, Disk: {disk_mb:.1f}MB)")
def reset_bucket(client, bucket_name=BUCKET_NAME):
    """Delete all blobs in the bucket to start fresh."""
    bucket = client.get_bucket(bucket_name)
    blobs = bucket.list_blobs()
    print(f"[CLEANUP] Deleting all files in gs://{bucket_name}...")
    # Using batches for large buckets is safer but direct deletion works for now
    count = 0
    for blob in blobs:
        blob.delete()
        count += 1
    print(f"[OK] Deleted {count} files.")
def is_issue_complete_on_gcs(client, issue_id, bucket_name=BUCKET_NAME):
    """
    Check if an issue is truly complete on GCS by comparing 
    ocr/page_*.json count with total_pages in metadata.json.
    """
    bucket = client.get_bucket(bucket_name)
    
    # 1. Check metadata.json
    metadata_blob = bucket.blob(f"ocr/{issue_id}/metadata.json")
    if not metadata_blob.exists():
        return False
        
    try:
        content = metadata_blob.download_as_text()
        metadata = json.loads(content)
        total_pages = metadata.get("total_pages", 0)
        if total_pages == 0:
            return False
            
        # 2. Count page JSONs
        prefix = f"ocr/{issue_id}/page_"
        blobs = list(bucket.list_blobs(prefix=prefix))
        # Filter for .json to be sure (in case there are other files)
        page_blobs = [b for b in blobs if b.name.endswith(".json")]
        
        return len(page_blobs) >= total_pages
    except Exception as e:
        print(f"[ERROR] Error checking coherence for {issue_id}: {e}")
        return False

def get_broken_issues(client, start_year, end_year, bucket_name=BUCKET_NAME):
    """
    Scan the bucket for issues that are incomplete according to their metadata.
    Returns a list of issue_id strings.
    """
    bucket = client.get_bucket(bucket_name)
    broken = []
    
    print(f"[SCAN] Scanning for broken issues from {start_year} to {end_year}...")
    
    # List all metadata files to find candidate issues
    blobs = bucket.list_blobs(prefix="ocr/")
    for blob in blobs:
        if blob.name.endswith("metadata.json"):
            # Path format: ocr/YYYY-MM/metadata.json
            parts = blob.name.split("/")
            if len(parts) == 3:
                issue_id = parts[1]
                try:
                    year = int(issue_id.split("-")[0])
                    if start_year <= year <= end_year:
                        if not is_issue_complete_on_gcs(client, issue_id, bucket_name):
                            broken.append(issue_id)
                except (ValueError, IndexError):
                    continue
    
    if broken:
        print(f"[SCAN] Found {len(broken)} broken issues: {', '.join(broken)}")
    else:
        print("[SCAN] No broken issues found.")
        
    return broken
