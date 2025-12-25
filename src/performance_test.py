import time
import torch
import json
from pathlib import Path
from PIL import Image
from doclayout_yolo import YOLOv10
from torchvision.ops import nms
from src.extract import DEVICE, id_to_names, enhance_and_binarize
from src.ocr import run_tesseract

def run_performance_test(image_dir: Path):
    print(f"Loading model on {DEVICE}...")
    torch.set_grad_enabled(False)
    model = YOLOv10("models/DocLayout-YOLO-DocStructBench/doclayout_yolo_docstructbench_imgsz1024.pt").to(DEVICE)
    # model.eval() and model.fuse() removed as they cause unexpected dataset loading in this environment

    image_paths = sorted(list(image_dir.glob("*.png")))[:5]
    if not image_paths:
        print(f"No images found in {image_dir}")
        return

    stats = {
        "total_time": 0.0,
        "total_paragraphs": 0,
        "pages_processed": 0
    }

    print(f"Starting performance test on {len(image_paths)} images...")

    try:
        for img_path in image_paths:
            print(f"Processing {img_path.name}...")
            start_page = time.perf_counter()
            
            from src.extract import extract_paragraphs_and_lines
            results = extract_paragraphs_and_lines(
                page_image_path=str(img_path),
                para_output=None,
                save_crops=False,
                return_bboxes=True,
                model=model
            )
            
            duration = time.perf_counter() - start_page
            stats["total_time"] += duration
            stats["total_paragraphs"] += len(results)
            stats["pages_processed"] += 1
            print(f"  Done in {duration:.2f}s ({len(results)} paragraphs)")

    except KeyboardInterrupt:
        print("\nInterrupted. Printing partial results...")

    if stats["pages_processed"] > 0:
        print("\n--- Performance Results (Optimized) ---")
        print(f"Pages processed: {stats['pages_processed']}")
        print(f"Total paragraphs: {stats['total_paragraphs']}")
        print(f"Total time spent: {stats['total_time']:.2f}s")
        print(f"Average per page: {stats['total_time']/stats['pages_processed']:.2f}s")
    else:
        print("No pages processed.")

if __name__ == "__main__":
    test_dir = Path("data/generated/images/1926-08")
    run_performance_test(test_dir)
