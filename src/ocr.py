from PIL import Image, ImageEnhance
import pytesseract


def enhance(image: Image.Image, contrast=2.5, brightness=2.5) -> Image.Image:
    img = ImageEnhance.Contrast(image.convert("L")).enhance(contrast)
    img = ImageEnhance.Brightness(img).enhance(brightness)
    return img


def run_tesseract(image: Image.Image, lang="hye-calfa-n", config="--psm 6") -> str:
    return pytesseract.image_to_string(image, lang=lang, config=config).strip()
