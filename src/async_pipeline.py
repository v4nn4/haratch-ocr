import threading
import uuid
import json
from pathlib import Path
from google.cloud import storage
from .download import download_issue
from .pdf import convert_pdf_pages
from .extract import extract_paragraphs_and_lines
from PIL import Image

class AsyncProcessor:
    def __init__(self, bucket_name="haratch-ocr-results"):
        self.bucket_name = bucket_name
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(bucket_name)
        self.active_jobs = {}
        
    def create_bucket_if_not_exists(self):
        if not self.bucket.exists():
            self.bucket = self.storage_client.create_bucket(self.bucket_name)
    
    def process_page(self, page_path: Path) -> dict:
        width, height = Image.open(str(page_path)).size
        
        results = extract_paragraphs_and_lines(
            page_image_path=str(page_path),
            para_output=None,
            save_crops=False,
            return_bboxes=True,
        )
        
        json_data = {
            "metadata": {"width": width, "height": height},
            "paragraphs": []
        }
        
        for bbox, text in results:
            int_bbox = list(map(int, bbox))
            json_data["paragraphs"].append({
                "bbox": int_bbox,
                "hye": text.strip()
            })
        
        return json_data
    
    def save_results_to_gcs(self, request_id: str, results: dict):
        blob = self.bucket.blob(f"results/{request_id}.json")
        blob.upload_from_string(
            json.dumps(results, ensure_ascii=False, indent=2),
            content_type="application/json"
        )
    
    def update_status(self, request_id: str, status: str, progress: int = None):
        status_data = {
            "status": status,
            "progress": progress
        }
        if status == "completed":
            status_data["result_url"] = f"gs://{self.bucket_name}/results/{request_id}.json"
        
        blob = self.bucket.blob(f"status/{request_id}.json")
        blob.upload_from_string(
            json.dumps(status_data, ensure_ascii=False, indent=2),
            content_type="application/json"
        )
    
    def process_issue_async(self, request_id: str, year: int, month: int):
        try:
            self.update_status(request_id, "downloading", 0)
            
            issue_id = f"{year}-{month:02d}"
            pdf_path = download_issue(year, month)
            
            self.update_status(request_id, "converting", 20)
            image_dir = Path("data") / "generated" / "images" / issue_id
            image_paths = convert_pdf_pages(pdf_path, image_dir)
            
            self.update_status(request_id, "processing", 40)
            results = {
                "issue": issue_id,
                "pages": []
            }
            
            total_pages = len(image_paths)
            for i, page_path in enumerate(image_paths):
                page_result = self.process_page(page_path)
                results["pages"].append({
                    "page": i + 1,
                    "data": page_result
                })
                
                progress = 40 + int((i + 1) / total_pages * 50)
                self.update_status(request_id, "processing", progress)
            
            self.update_status(request_id, "saving", 90)
            self.save_results_to_gcs(request_id, results)
            
            self.update_status(request_id, "completed", 100)
            
        except Exception as e:
            self.update_status(request_id, "failed")
            raise e
        finally:
            if request_id in self.active_jobs:
                del self.active_jobs[request_id]
    
    def start_computation(self, year: int, month: int) -> str:
        request_id = str(uuid.uuid4())
        self.active_jobs[request_id] = "pending"
        
        self.create_bucket_if_not_exists()
        
        thread = threading.Thread(
            target=self.process_issue_async,
            args=(request_id, year, month)
        )
        thread.daemon = True
        thread.start()
        
        return request_id
    
    def get_status(self, request_id: str) -> dict:
        try:
            blob = self.bucket.blob(f"status/{request_id}.json")
            if not blob.exists():
                if request_id in self.active_jobs:
                    return {"status": "pending", "progress": 0}
                else:
                    return {"status": "not_found"}
            
            content = blob.download_as_text()
            return json.loads(content)
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_result(self, request_id: str) -> dict:
        try:
            blob = self.bucket.blob(f"results/{request_id}.json")
            if not blob.exists():
                return {"status": "not_found"}
            
            content = blob.download_as_text()
            return json.loads(content)
        except Exception as e:
            return {"status": "error", "message": str(e)}

processor = AsyncProcessor()
