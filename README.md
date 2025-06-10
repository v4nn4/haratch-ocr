# haratch-ocr

Armenian OCR on Haratch (Յառաջ) using Tesseract with [Calfa](https://github.com/calfa-co/hye-tesseract) `hye-calfa-n`, [DocLayout-YOLO](https://github.com/opendatalab/DocLayout-YOLO) and Gemini.

## Installation

Uses [Poetry](https://python-poetry.org/):

```bash
poetry install
```

Download the model weights:

- Get the model file on Hugging Face: https://huggingface.co/juliozhao/DocLayout-YOLO-DocStructBench/tree/main
- Place the file in: `models/DocLayout-YOLO-DocStructBench/`

Create a `.env` file with your Gemini API key:

```ini
GEMINI_API_KEY=your-key-here
```

## Usage

```
poetry run python main.py extract --pdf_file="data/raw/HARATCH_1925_08-Aout.pdf"
poetry run python main.py translate
```