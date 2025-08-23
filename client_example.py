#!/usr/bin/env python3
import requests
import time
import json

BASE_URL = "https://haratch-ocr-k32bm6hyxa-uc.a.run.app"

def start_computation(year: int, month: int):
    """Start a computation and return the request ID"""
    response = requests.post(
        f"{BASE_URL}/compute",
        json={"year": year, "month": month}
    )
    response.raise_for_status()
    return response.json()["request_id"]

def get_status(request_id: str):
    """Get the status of a computation"""
    response = requests.get(f"{BASE_URL}/status/{request_id}")
    response.raise_for_status()
    return response.json()

def get_result(request_id: str):
    """Get the result of a completed computation"""
    response = requests.get(f"{BASE_URL}/result/{request_id}")
    response.raise_for_status()
    return response.json()

def poll_for_completion(request_id: str, poll_interval: int = 10):
    """Poll for completion and return the result"""
    print(f"🚀 Started computation with request ID: {request_id}")
    
    while True:
        status = get_status(request_id)
        print(f"📊 Status: {status['status']} (Progress: {status.get('progress', 0)}%)")
        
        if status['status'] == 'completed':
            print("✅ Computation completed! Fetching results...")
            result = get_result(request_id)
            return result
        elif status['status'] == 'failed':
            print("❌ Computation failed!")
            return None
        
        time.sleep(poll_interval)

def main():
    # Example: Process August 1925 issue
    year = 1925
    month = 8
    
    print(f"🎯 Starting OCR processing for {year}-{month:02d}")
    
    try:
        # Start the computation
        request_id = start_computation(year, month)
        
        # Poll for completion
        result = poll_for_completion(request_id)
        
        if result:
            print(f"📄 Processed {len(result['pages'])} pages")
            print(f"📁 Results saved to: {result.get('result_url', 'N/A')}")
            
            # Show first page summary
            if result['pages']:
                first_page = result['pages'][0]
                print(f"📖 First page has {len(first_page['data']['paragraphs'])} paragraphs")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
