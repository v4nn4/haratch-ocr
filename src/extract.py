import json
import torch
from pathlib import Path
from PIL import Image, ImageEnhance
from doclayout_yolo import YOLOv10
from torchvision.ops import nms
from concurrent.futures import ThreadPoolExecutor
from .ocr import run_tesseract


id_to_names = {
    0: "title",
    1: "plain text",
    2: "abandon",
    3: "figure",
    4: "figure_caption",
    5: "table",
    6: "table_caption",
    7: "table_footnote",
    8: "isolate_formula",
    9: "formula_caption",
}


def enhance_and_binarize(img: Image.Image, contrast=2.5, brightness=2.5) -> Image.Image:
    img = img.convert("L")
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img = ImageEnhance.Brightness(img).enhance(brightness)
    # Binarize: threshold at 180
    img = img.point(lambda x: 0 if x < 180 else 255, mode="1")
    return img


DEVICE = (
    "cuda"
    if torch.cuda.is_available()
    else "mps" if torch.backends.mps.is_available() else "cpu"
)

def extract_paragraphs_and_lines(
    page_image_path: str,
    para_output: str,
    save_crops=True,
    return_bboxes=False,
    conf_thres_para=0.25,
    iou_thres_para=0.45,
    model=None,
    inference_lock=None,
):
    if model is None:
        model = YOLOv10(
            "models/DocLayout-YOLO-DocStructBench/doclayout_yolo_docstructbench_imgsz1024.pt"
        ).to(DEVICE)

    try:
        page = Image.open(page_image_path).convert("RGB")
    except Exception as e:
        print(f"[ERROR] Could not open image {page_image_path}: {e}")
        return []

    # AI Layout Detection is GPU-bound and contention-heavy.
    # We lock only the inference part to be sequential, while Tesseract/Preproc stays parallel.
    # We use torch.no_grad() to avoid RuntimeError on MPS with multi-threading.
    with torch.no_grad():
        if inference_lock:
            with inference_lock:
                det_page = model.predict(
                    page, 
                    imgsz=1024, 
                    conf=conf_thres_para, 
                    device=DEVICE,
                    half=(DEVICE != "cpu"), # FP16 on GPU/MPS
                    verbose=False
                )[0]
        else:
            det_page = model.predict(
                page, 
                imgsz=1024, 
                conf=conf_thres_para, 
                device=DEVICE,
                half=(DEVICE != "cpu"),
                verbose=False
            )[0]

    boxes_p, classes_p, scores_p = (
        det_page.boxes.xyxy,
        det_page.boxes.cls,
        det_page.boxes.conf,
    )
    idx_p = nms(torch.Tensor(boxes_p), torch.Tensor(scores_p), iou_thres_para)
    boxes_p = boxes_p[idx_p]
    classes_p = classes_p[idx_p]

    def process_paragraph(i, cls, bbox):
        if id_to_names[int(cls)] != "plain text":
            return None

        x1, y1, x2, y2 = bbox
        crop = page.crop((int(x1), int(y1), int(x2), int(y2)))
        enhanced = enhance_and_binarize(crop)

        if save_crops and para_output:
            para_path = Path(para_output) / f"paragraph_{i}.png"
            enhanced.save(para_path)

        text = run_tesseract(enhanced)
        return ((x1, y1, x2, y2), text.strip())

    # Process paragraphs in parallel
    # Tesseract is CPU-bound, so we use enough workers to saturate the CPU
    # but not too many to avoid context switching overhead.
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(process_paragraph, i, cls, bbox)
            for i, (cls, bbox) in enumerate(zip(classes_p, boxes_p))
        ]
        results = [f.result() for f in futures if f.result() is not None]

    return (
        results
        if return_bboxes
        else {
            f"paragraph_{i}": text.strip()
            for (i, ((x1, y1, x2, y2), text)) in enumerate(results)
        }
    )


def extract_all(image_dir: Path, output_dir: Path, model=None):
    output_dir.mkdir(parents=True, exist_ok=True)

    for image_path in sorted(image_dir.glob("page_*.png")):
        output_json_path = output_dir / f"{image_path.stem}.json"
        
        if output_json_path.exists():
            print(f"[OK] Skipping {image_path.name} — already processed.")
            continue

        try:
            width, height = Image.open(str(image_path)).size
            results = extract_paragraphs_and_lines(
                page_image_path=str(image_path),
                para_output=None,
                save_crops=False,
                return_bboxes=True,
                model=model,
            )
        except Exception as e:
            print(f"[ERROR] Skipping {image_path.name} due to error: {e}")
            continue

        with output_json_path.open("w", encoding="utf-8") as f_json:
            json_data = {
                "metadata": {"width": width, "height": height},
                "paragraphs": [],
            }

            for bbox, text in results:
                int_bbox = list(map(int, bbox))
                json_data["paragraphs"].append(
                    {
                        "bbox": int_bbox,
                        "text": text.strip(),
                        "length": len(text.strip()),
                    }
                )

            json.dump(json_data, f_json, ensure_ascii=False, indent=2)
