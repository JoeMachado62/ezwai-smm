"""
Test Replicate API directly using HTTP requests
Compares both HTTP API and Python SDK methods
"""
import os
import sys
import requests
import json
import time
from dotenv import load_dotenv

# Fix Windows console encoding for checkmarks
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
SEEDREAM_VERSION = "054cd8c667f535616fd66710ce20c8949bf64ac3d9a3459e338f026424be8bec"

def test_http_api():
    """Test using raw HTTP requests (matches curl examples)"""
    print("="*80)
    print("TEST 1: HTTP API (Raw Requests)")
    print("="*80)

    # Create prediction
    create_url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Bearer {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "version": SEEDREAM_VERSION,
        "input": {
            "prompt": "Professional business meeting photograph, shot with high-end camera, natural light, bokeh, magazine quality, photorealistic",
            "size": "2K",
            "aspect_ratio": "16:9",
            "max_images": 1
        }
    }

    print("\n1. Creating prediction...")
    print(f"URL: {create_url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    response = requests.post(create_url, headers=headers, json=payload)

    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Body:\n{json.dumps(response.json(), indent=2)}")

    if response.status_code == 201:
        prediction = response.json()
        prediction_id = prediction["id"]
        print(f"\n✓ Prediction created successfully!")
        print(f"Prediction ID: {prediction_id}")
        print(f"Status: {prediction['status']}")

        # Poll for completion
        print("\n2. Polling for completion...")
        get_url = f"https://api.replicate.com/v1/predictions/{prediction_id}"

        max_attempts = 60
        for attempt in range(max_attempts):
            time.sleep(2)
            get_response = requests.get(get_url, headers=headers)
            prediction = get_response.json()
            status = prediction["status"]

            print(f"Attempt {attempt + 1}/{max_attempts}: Status = {status}")

            if status == "succeeded":
                print("\n✓ Image generation succeeded!")
                print(f"Output: {prediction.get('output')}")
                return prediction
            elif status == "failed":
                print(f"\n✗ Image generation failed!")
                print(f"Error: {prediction.get('error')}")
                return None
            elif status == "canceled":
                print(f"\n✗ Image generation canceled!")
                return None

        print("\n✗ Timeout waiting for image generation")
        return None
    else:
        print(f"\n✗ Failed to create prediction")
        return None


def test_python_sdk():
    """Test using Replicate Python SDK"""
    print("\n" + "="*80)
    print("TEST 2: Python SDK (replicate.run())")
    print("="*80)

    import replicate
    replicate.api_token = REPLICATE_API_TOKEN

    print("\n1. Generating image with SDK...")
    input_data = {
        "prompt": "Professional small business owner photograph, high-end camera, studio lighting, magazine quality, photorealistic",
        "size": "2K",
        "aspect_ratio": "4:3",
        "max_images": 1
    }

    print(f"Input: {json.dumps(input_data, indent=2)}")

    try:
        output = replicate.run(
            "bytedance/seedream-4",
            input=input_data
        )

        print(f"\n✓ SDK generation succeeded!")
        print(f"Output type: {type(output)}")
        print(f"Output: {output}")

        if isinstance(output, list) and len(output) > 0:
            print(f"Image URL: {output[0]}")
        elif isinstance(output, str):
            print(f"Image URL: {output}")

        return output
    except Exception as e:
        print(f"\n✗ SDK generation failed!")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("Replicate API Test")
    print(f"Token: {REPLICATE_API_TOKEN[:10]}..." if REPLICATE_API_TOKEN else "NO TOKEN FOUND")
    print(f"Model Version: {SEEDREAM_VERSION}")

    # Test HTTP API
    http_result = test_http_api()

    # Test Python SDK
    sdk_result = test_python_sdk()

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"HTTP API: {'✓ Success' if http_result else '✗ Failed'}")
    print(f"Python SDK: {'✓ Success' if sdk_result else '✗ Failed'}")
