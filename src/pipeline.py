from pathlib import Path
from typing import List, Dict, Any
import json
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import threading
from doclayout_yolo import YOLOv10

from .download import download_issue
from .pdf import convert_pdf_pages, get_pdf_page_count
from .extract import extract_paragraphs_and_lines, DEVICE
from .translate import translate_paragraph
import datetime
from .paths import get_issue_id, get_pdf_path, get_image_dir, get_ocr_dir, get_output_dir


def download_issue_task(year: int, month: int) -> Path:
    """Download the PDF issue from the archive."""
    return download_issue(year, month)


def convert_pdf_task(pdf_path: Path, image_dir: Path) -> List[Path]:
    """Convert PDF pages to images."""
    return convert_pdf_pages(pdf_path, image_dir)


from .gcs import get_gcs_client, BUCKET_NAME, blob_exists, update_runner_status

def _update_live_ocr_status(issue_id: str, page_name: str, json_data: Dict[str, Any]):
    """Helper to update the runner status with the full Armenian text from a page."""
    try:
        # Concatenate all Armenian text from paragraphs
        full_text = "\n".join([p["hye"].strip() for p in json_data.get("paragraphs", []) if p.get("hye")])
        
        # Limit total length slightly to avoid massive status JSON (e.g. 3000 chars)
        if len(full_text) > 3000:
            full_text = full_text[:3000] + "... (truncated)"

        if full_text:
            client = get_gcs_client()
            update_runner_status(
                client, 
                status=f"processing {issue_id}", 
                latest_ocr=full_text,
                current_page=page_name,
                phase="ocr"
            )
    except Exception as e:
        print(f"[STATUS] Failed to update OCR snippet: {e}")

def process_page_task(page_path: Path, output_dir: Path, model: YOLOv10 = None, issue_id: str = None, inference_lock: threading.Lock = None) -> Dict[str, Any]:
    """
    Process a single page for OCR extraction.
    Checks for existing JSON locally and on GCS to support resuming.
    """
    output_path = output_dir / f"{page_path.stem}.json"
    
    # 1. Local Cache Check
    if output_path.exists():
        print(f"[OK] Loading local cached OCR for {page_path.name}")
        with output_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if issue_id:
                _update_live_ocr_status(issue_id, page_path.stem, data)
            return data

    # 2. GCS Cache Check (Statelessness)
    if issue_id:
        client = get_gcs_client()
        bucket = client.get_bucket(BUCKET_NAME)
        blob_name = f"ocr/{issue_id}/{page_path.stem}.json"
        if blob_exists(bucket, blob_name):
            print(f"[CLOUD] Downloading cached OCR for {page_path.name} from GCS...")
            blob = bucket.blob(blob_name)
            content = blob.download_as_text()
            json_data = json.loads(content)
            # Save locally for future speed
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            _update_live_ocr_status(issue_id, page_path.stem, json_data)
            return json_data

    print(f"[INFO] Running OCR on {page_path.name}...")
    width, height = Image.open(str(page_path)).size

    # AI Layout Detection is GPU-bound. We only lock the specific inference part
    # inside extract_paragraphs_and_lines to be sequential.
    results = extract_paragraphs_and_lines(
        page_image_path=str(page_path),
        para_output=None,
        save_crops=False,
        return_bboxes=True,
        model=model,
        inference_lock=inference_lock
    )

    json_data = {"metadata": {"width": width, "height": height}, "paragraphs": []}

    for bbox, text in results:
        int_bbox = list(map(int, bbox))
        json_data["paragraphs"].append({"bbox": int_bbox, "hye": text.strip()})

    # Save individual page result
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    # Update status with latest OCR snippet (Armenian)
    if issue_id:
        _update_live_ocr_status(issue_id, page_path.stem, json_data)

    return json_data


def translate_page_task(
    page_data: Dict[str, Any], min_length: int = 200
) -> Dict[str, Any]:
    """Translate Armenian text to French for a single page."""
    translated = {"metadata": page_data["metadata"], "paragraphs": []}

    for para in page_data["paragraphs"]:
        if len(para["hye"]) >= min_length:
            try:
                fr_text = translate_paragraph(para["hye"])
                # Skip placeholder translation results
                if fr_text and not fr_text.startswith("["):
                    translated["paragraphs"].append(
                        {
                            "bbox": para["bbox"],
                            "original": para["hye"],
                            "translated": fr_text,
                        }
                    )
                else:
                    # Translation not available (no API key, etc)
                    translated["paragraphs"].append(
                        {
                            "bbox": para["bbox"],
                            "original": para["hye"],
                            "translated": None,
                        }
                    )
            except Exception as e:
                # If translation fails, keep original text without translation
                translated["paragraphs"].append(
                    {
                        "bbox": para["bbox"],
                        "original": para["hye"],
                        "translated": None,
                    }
                )
        else:
            # Keep short paragraphs without translation
            translated["paragraphs"].append(
                {
                    "bbox": para["bbox"],
                    "original": para["hye"],
                    "translated": None,
                }
            )

    return translated


def process_single_page_task(
    page_path: Path,
    ocr_dir: Path,
    model: YOLOv10,
    include_translation: bool = False,
    min_translation_length: int = 200,
    issue_id: str = None,
    inference_lock: threading.Lock = None,
) -> Dict[str, Any]:
    """Process a single page for OCR and optionally translation."""
    # Process page for OCR (passing issue_id for GCS check)
    page_data = process_page_task(page_path, ocr_dir, model=model, issue_id=issue_id, inference_lock=inference_lock)

    # Translate if requested
    if include_translation:
        return translate_page_task(page_data, min_translation_length)
    else:
        return page_data


def save_final_results_task(
    issue_id: str, pages_data: List[Dict[str, Any]], output_dir: Path
) -> Dict[str, Any]:
    """Save the final results for the entire issue."""
    final_results = {
        "issue": issue_id,
        "pages": pages_data,
        "total_pages": len(pages_data),
    }

    output_path = output_dir / f"{issue_id}_complete.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(final_results, f, ensure_ascii=False, indent=2)

    return final_results


def save_metadata_task(issue_id: str, page_count: int, output_dir: Path):
    """Save metadata about the issue (e.g. total pages)."""
    metadata = {
        "issue": issue_id,
        "total_pages": page_count,
        "processed_at": datetime.datetime.now().isoformat()
    }
    output_path = output_dir / "metadata.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    return metadata


def ocr_pipeline(
    year: int,
    month: int,
    include_translation: bool = False,
    min_translation_length: int = 200,
) -> Dict[str, Any]:
    """
    Optimized OCR pipeline that overlaps PDF conversion and AI processing.
    """
    issue_id = get_issue_id(year, month)

    # Define paths
    image_dir = get_image_dir(year, month)
    ocr_dir = get_ocr_dir(year, month)
    output_dir = get_output_dir(year, month)
    
    final_output_path = output_dir / f"{issue_id}_complete.json"
    if final_output_path.exists():
        print(f"[OK] Issue {issue_id} is already complete. Loading results...")
        with final_output_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    # Step 1: Download PDF
    pdf_path = download_issue_task(year, month)

    try:
        # Step 2: Get total pages and save metadata
        page_count = get_pdf_page_count(pdf_path)
        save_metadata_task(issue_id, page_count, ocr_dir)
        save_metadata_task(issue_id, page_count, output_dir)

        print("[INIT] Initializing Layout Detection Model on DEVICE...")
        import torch
        # Global disable gradients for the entire session
        torch.set_grad_enabled(False)

        model = YOLOv10(
            "models/DocLayout-YOLO-DocStructBench/doclayout_yolo_docstructbench_imgsz1024.pt"
        ).to(DEVICE)
        
        BATCH_SIZE = 8  # Process 8 pages per YOLO batch
        max_workers = 8  # For parallel Tesseract across pages
        
        print(f"[PROCESS] Starting batched YOLO pipeline for {issue_id} (batch_size={BATCH_SIZE})...")
        
        image_queue = Queue(maxsize=20)  # Buffer 20 images in memory
        
        def producer():
            """Producer: Convert PDF pages to PNGs and put paths in the queue."""
            try:
                image_stream = convert_pdf_pages(pdf_path, image_dir)
                for img_path in image_stream:
                    image_queue.put(img_path)
                # Signal end of stream
                image_queue.put(None)
                print("[PRODUCER] PDF conversion finished.")
            except Exception as e:
                print(f"[ERROR] Producer failed: {e}")
                image_queue.put(None)

        # Start producer thread
        threading.Thread(target=producer, daemon=True).start()
        
        # Import batch functions
        from .extract import batch_yolo_detect, process_single_detection
        
        def process_batch_ocr(page_img, boxes, classes, page_path, ocr_dir, issue_id):
            """Process a single page's OCR after YOLO detection."""
            output_path = ocr_dir / f"{page_path.stem}.json"
            
            # Check local cache
            if output_path.exists():
                print(f"[OK] Loading local cached OCR for {page_path.name}")
                with output_path.open("r", encoding="utf-8") as f:
                    return json.load(f)
            
            # Check GCS cache
            if issue_id:
                client = get_gcs_client()
                bucket = client.get_bucket(BUCKET_NAME)
                blob_name = f"ocr/{issue_id}/{page_path.stem}.json"
                if blob_exists(bucket, blob_name):
                    print(f"[CLOUD] Downloading cached OCR for {page_path.name} from GCS...")
                    blob = bucket.blob(blob_name)
                    content = blob.download_as_text()
                    json_data = json.loads(content)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with output_path.open("w", encoding="utf-8") as f:
                        json.dump(json_data, f, ensure_ascii=False, indent=2)
                    return json_data
            
            print(f"[INFO] Running OCR on {page_path.name}...")
            width, height = page_img.size
            
            # Run Tesseract on paragraphs (already parallelized inside)
            results = process_single_detection(page_img, boxes, classes)
            
            json_data = {"metadata": {"width": width, "height": height}, "paragraphs": []}
            for bbox, text in results:
                int_bbox = list(map(int, bbox))
                json_data["paragraphs"].append({"bbox": int_bbox, "hye": text.strip()})
            
            # Save individual page result
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            # Update status
            if issue_id:
                _update_live_ocr_status(issue_id, page_path.stem, json_data)
            
            return json_data
        
        # Step 3b: Batched Consumer - Collect images, batch YOLO, parallel OCR
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            batch = []
            done = False
            
            while not done:
                # Collect a batch of images
                while len(batch) < BATCH_SIZE:
                    img_path = image_queue.get()
                    if img_path is None:
                        done = True
                        break
                    batch.append(img_path)
                
                if not batch:
                    break
                
                # Run batched YOLO detection
                print(f"[YOLO] Batch detecting {len(batch)} pages...")
                detections = batch_yolo_detect(batch, model)
                
                # Submit OCR tasks in parallel for all detections
                futures = []
                for (page_path, page_img, boxes, classes) in detections:
                    future = executor.submit(
                        process_batch_ocr,
                        page_img, boxes, classes, Path(page_path), ocr_dir, issue_id
                    )
                    futures.append(future)
                
                # Wait for this batch to complete before next
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        print(f"[ERROR] Page processing failed: {e}")
                
                # Clear batch for next iteration
                batch = []

    finally:
        # Step 4: Cleanup PDF now that we have all PNGs (or if conversion failed)
        if pdf_path.exists():
            print(f"[CLEANUP] Deleting source PDF: {pdf_path.name}")
            pdf_path.unlink()

    # Re-list images to maintain consistent order in the final JSON
    # This ensures page_0.json, page_1.json sequence
    final_image_paths = sorted(list(image_dir.glob("page_*.png")))
    pages_data = []
    for p in final_image_paths:
        page_json = ocr_dir / f"{p.stem}.json"
        if page_json.exists():
            with page_json.open("r", encoding="utf-8") as f:
                pages_data.append(json.load(f))
        else:
            print(f"[WARNING] Missing OCR result for {p.name}")

    # Step 5: Save final results
    final_results = save_final_results_task(issue_id, pages_data, output_dir)

    return final_results


def simple_ocr_pipeline(year: int, month: int) -> Dict[str, Any]:
    """
    Simple OCR pipeline without translation for faster processing.
    """
    return ocr_pipeline(year, month, include_translation=False)


def full_ocr_pipeline(year: int, month: int) -> Dict[str, Any]:
    """
    Full OCR pipeline with translation for complete processing.
    """
    return ocr_pipeline(year, month, include_translation=True)
