# Haratch OCR Processor

An OCR processor that downloads issues of the newspaper Haratch and runs Armenian OCR on them.

## Features

- Downloads newspaper issues from webaram archives
- Converts PDF pages to images
- Runs DocLayout-YOLO for document layout detection
- Runs Tesseract with hye-calfa-n model for Armenian OCR
- Parallel processing with Dask
- FastAPI API with health and run endpoints
- Docker containerization with Dask dashboard

## Optional Features

- Translation support (requires `poetry install --extras translate`)

## Installation

```bash
# Core OCR functionality
poetry install

# With translation support (optional)
poetry install --extras translate
```

The Docker setup automatically downloads the required models:
- `hye-calfa-n.traineddata` from [calfa-co/hye-tesseract](https://github.com/calfa-co/hye-tesseract)
- DocLayout-YOLO model from HuggingFace

## Usage

### CLI (for debugging)

```bash
# Extract OCR from images
poetry run python main.py extract

# Run full pipeline on an issue
poetry run python main.py run 1925 8
```

### API

```bash
# Start the server
poetry run python start_server.py

# Health check
curl http://localhost:8000/health

# Run OCR on an issue
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"year": 1925, "month": 8}'
```

### Docker

```bash
# Build the image
docker build -t haratch-ocr .

# Run the container
docker run -p 8000:8000 -p 8787:8787 haratch-ocr
```

### GCP Cloud Run Deployment

```bash
# Setup GCP project (first time only)
./setup-gcp.sh

# Deploy to Cloud Run
./deploy.sh
```

The deployment includes:
- 4 CPU cores, 8GB memory
- 1 hour timeout for OCR processing
- Automatic scaling

## API Endpoints

- `GET /health` - Check if AI models are available
- `POST /run` - Run OCR pipeline on an issue (year and month)

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
- Poetry for dependency management
- Tesseract with [hye-calfa-n model](https://github.com/calfa-co/hye-tesseract) from calfa-co
- DocLayout-YOLO model from HuggingFace
- Dask for parallelization
- FastAPI for API
- Docker for containerization

## Optional Dependencies

- Translation: python-dotenv, openai, google-generativeai