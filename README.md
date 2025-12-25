# Haratch OCR Processor

An OCR processor that downloads issues of the newspaper Haratch and runs Armenian OCR on them.

## Features

- Downloads newspaper issues from webaram archives
- Converts PDF pages to images
- Runs DocLayout-YOLO for document layout detection
- Runs Tesseract with hye-calfa-n model for Armenian OCR

## Optional Features

- Translation support (requires `uv sync --extra translate`)

## Installation

```bash
# Core OCR functionality
uv sync

# With translation support (optional)
uv sync --extra translate
```

You'll also need:
- Tesseract with [hye-calfa-n model](https://github.com/calfa-co/hye-tesseract) from calfa-co
- DocLayout-YOLO model from HuggingFace (downloaded automatically)

## Usage

### CLI

```bash
# Run simple OCR on an issue (no translation)
uv run python main.py simple --year 1925 --month 8

# Run full OCR with translation
uv run python main.py full --year 1925 --month 8
```

## Output Format

Results are saved in JSON format per page:

```json
{
  "metadata": {
    "width": 3824,
    "height": 5664
  },
  "paragraphs": [
    {
      "bbox": [2235, 3890, 3694, 4703],
      "hye": "Armenian text..."
    }
  ]
}
```

## Dependencies

- Python 3.12+
- Tesseract with [hye-calfa-n model](https://github.com/calfa-co/hye-tesseract) from calfa-co
- DocLayout-YOLO model from HuggingFace

## Optional Dependencies

- Translation: python-dotenv, openai, google-generativeai