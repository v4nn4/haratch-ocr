FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    wget \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /usr/share/tessdata && \
    wget -O /usr/share/tessdata/hye-calfa-n.traineddata \
    https://raw.githubusercontent.com/calfa-co/hye-tesseract/main/hye-calfa-n.traineddata

WORKDIR /app

RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --only main --no-root

COPY . .

RUN mkdir -p models/DocLayout-YOLO-DocStructBench
RUN python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='microsoft/DocLayout-YOLO-DocStructBench', filename='doclayout_yolo_docstructbench_imgsz1024.pt', local_dir='models/DocLayout-YOLO-DocStructBench')"

EXPOSE 8000 8787

CMD ["python", "start_server.py"]
