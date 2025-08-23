import os
import subprocess


def start_fastapi():
    port = os.environ.get("PORT", "8000")
    subprocess.run(["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", port])


if __name__ == "__main__":
    start_fastapi()
