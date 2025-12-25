import datetime
import signal
import sys
from .pipeline import simple_ocr_pipeline
from .sync_gcs import sync_all_jsons
from .gcs import get_gcs_client, update_runner_status, get_broken_issues
from .cleanup import cleanup_issue_data, enforce_disk_limit, get_data_folder_size_mb, cleanup_all_images
from .paths import get_issue_id
import psutil
import os
import time

def get_month_range(start_year, start_month, end_year, end_month):
    """Generate (year, month) tuples for the target range."""
    current_date = datetime.date(start_year, start_month, 1)
    end_date = datetime.date(end_year, end_month, 1)
    
    while current_date <= end_date:
        yield current_date.year, current_date.month
        # Move to next month
        if current_date.month == 12:
            current_date = datetime.date(current_date.year + 1, 1, 1)
        else:
            current_date = datetime.date(current_date.year, current_date.month + 1, 1)

def run_archive(
    start_year=1925, 
    start_month=8, 
    end_year=2009, 
    end_month=5,
    skip_sync=False
):
    """
    Process the entire Haratch archive month by month.
    Each month's result is synced to GCS to update the live dashboard.
    """
    client = get_gcs_client()
    
    def signal_handler(sig, frame):
        print("\n[STOP] Interrupt received, signaling IDLE status...")
        update_runner_status(client, "idle")
        sys.exit(0)

    def get_health_stats():
        """Get current RAM and Disk usage."""
        process = psutil.Process(os.getpid())
        ram_mb = process.memory_info().rss / (1024 * 1024)
        disk_mb = get_data_folder_size_mb()
        return ram_mb, disk_mb

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    start_time = time.time()
    completed_count = 0
    ram, disk = get_health_stats()

    # Global cleanup at startup to purge any legacy images
    cleanup_all_images()

    print(f"[START] Starting archive processing from {start_year}-{start_month} to {end_year}-{end_month}")
    update_runner_status(client, "active", pace=0, ram_mb=ram, disk_mb=disk)
    
    # GCS Scan: Find broken issues first
    broken_ids = get_broken_issues(client, start_year, end_year)
    
    # Generate the chronological list
    all_tasks = []
    for year, month in get_month_range(start_year, start_month, end_year, end_month):
        all_tasks.append(get_issue_id(year, month))
    
    # Prioritize: Broken first, then everything else if not complete
    tasks_to_run = []
    # 1. Broken first
    for b_id in broken_ids:
        tasks_to_run.append((b_id, True)) # (id, is_priority)
    
    # 2. Chronological (skip if already in broken or already complete)
    from .gcs import is_issue_complete_on_gcs
    for t_id in all_tasks:
        if t_id not in broken_ids:
            tasks_to_run.append((t_id, False))

    try:
        for issue_id, is_priority in tasks_to_run:
            year, month = map(int, issue_id.split("-"))
            
            # Skip if already complete on cloud (unless it was marked as broken)
            if not is_priority and is_issue_complete_on_gcs(client, issue_id):
                continue

            # Disk check
            if not enforce_disk_limit():
                print("[WAIT] Disk limit reached, waiting for next cycle or manual intervention...")
            
            print(f"\n[RUN] --- Processing {issue_id} {'(PRIORITY)' if is_priority else ''} ---")
            
            # Calculate pace
            elapsed = time.time() - start_time
            pace = (completed_count / (elapsed / 3600)) if elapsed > 0 else 0
            
            # Get current health stats
            ram, disk = get_health_stats()
            
            update_runner_status(
                client, 
                f"processing {issue_id}", 
                ram_mb=ram, 
                disk_mb=disk, 
                pace=round(pace, 2),
                completed_this_session=completed_count
            )
            
            try:
                # Run the OCR pipeline
                simple_ocr_pipeline(year, month)
                
                # Sync to GCS
                if not skip_sync:
                    print(f"[CLOUD] Syncing {issue_id} to GCS...")
                    sync_all_jsons()
                
                completed_count += 1
                print(f"[OK] Finished {issue_id}")
            except Exception as e:
                print(f"[ERROR] Error processing {issue_id}: {str(e)}")
                # We still cleanup even on error
            finally:
                # Cleanup local images AND PDFs
                cleanup_issue_data(year, month)
                
                # Report health after each issue
                ram, disk = get_health_stats()
                elapsed = time.time() - start_time
                pace = (completed_count / (elapsed / 3600)) if elapsed > 0 else 0
                
                update_runner_status(
                    client, 
                    "active", 
                    ram_mb=ram, 
                    disk_mb=disk, 
                    pace=round(pace, 2),
                    completed_this_session=completed_count
                )
                
    finally:
        print("\n[DONE] Archive processing finished or stopped.")
        update_runner_status(client, "idle")
