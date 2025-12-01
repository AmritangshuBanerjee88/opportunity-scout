"""
Template for testing the endpoint.
Copy this file and add your own API key.
DO NOT commit files with actual API keys!
"""

import requests
import json
import os

# Get credentials from environment variables (SAFE)
ENDPOINT_URL = os.getenv("AZURE_ML_ENDPOINT_A", "YOUR_ENDPOINT_URL_HERE")
API_KEY = os.getenv("AZURE_ML_KEY_A", "YOUR_API_KEY_HERE")

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
    "azureml-model-deployment": "default"
}

payload = {
    "keywords": ["AI Ethics"],
    "opportunity_types": ["conference", "webinar"],
    "max_results": 10
}

print("🔍 Testing endpoint...")
print(f"   Keywords: {payload['keywords']}")
print("\n⏳ This may take 1-2 minutes...\n")

try:
    response = requests.post(
        ENDPOINT_URL,
        headers=headers,
        json=payload,
        timeout=180
    )
    
    if response.status_code == 200:
        result = response.json()
        if isinstance(result, str):
            result = json.loads(result)
        
        opportunities = result.get("opportunities", [])
        print(f"✅ SUCCESS! Found {len(opportunities)} opportunities")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text[:500])

except Exception as e:
    print(f"❌ Error: {e}")
