import json
import torch
from pathlib import Path
from PIL import Image, ImageEnhance
from doclayout_yolo import YOLOv10
from torchvision.ops import nms
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


def extract_paragraphs_and_lines(
    page_image_path: str,
    para_output: str,
    save_crops=True,
    return_bboxes=False,
    conf_thres_para=0.25,
    iou_thres_para=0.45,
):
    device = (
        "cuda"
        if torch.cuda.is_available()
        else "mps" if torch.backends.mps.is_available() else "cpu"
    )
    model = YOLOv10(
        "models/DocLayout-YOLO-DocStructBench/doclayout_yolo_docstructbench_imgsz1024.pt"
    )

    page = Image.open(page_image_path).convert("RGB")
    det_page = model.predict(page, imgsz=1024, conf=conf_thres_para, device=device)[0]
    boxes_p, classes_p, scores_p = (
        det_page.boxes.xyxy,
        det_page.boxes.cls,
        det_page.boxes.conf,
    )
    idx_p = nms(torch.Tensor(boxes_p), torch.Tensor(scores_p), iou_thres_para)
    boxes_p = boxes_p[idx_p]
    classes_p = classes_p[idx_p]

    results = []
    for i, (cls, (x1, y1, x2, y2)) in enumerate(zip(classes_p, boxes_p)):
        if id_to_names[int(cls)] != "plain text":
            continue

        crop = page.crop((int(x1), int(y1), int(x2), int(y2)))
        enhanced = enhance_and_binarize(crop)

        if save_crops and para_output:
            para_path = Path(para_output) / f"paragraph_{i}.png"
            enhanced.save(para_path)

        text = run_tesseract(enhanced)
        results.append(((x1, y1, x2, y2), text.strip()))

    return (
        results
        if return_bboxes
        else {
            f"paragraph_{i}": text.strip()
            for (i, ((x1, y1, x2, y2), text)) in enumerate(results)
        }
    )


def extract_all(image_dir: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    for image_path in sorted(image_dir.glob("page_*.png")):
        print(f"Processing {image_path.name}")
        width, height = Image.open(str(image_path)).size

        results = extract_paragraphs_and_lines(
            page_image_path=str(image_path),
            para_output=None,
            save_crops=False,
            return_bboxes=True,
        )

        output_json_path = output_dir / f"{image_path.stem}.json"

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
