import os
import sys
import json

# Add app to path
sys.path.insert(0, os.path.abspath('.'))

from app.ai.providers.gemini.adapter import GeminiProvider
from app.ai.providers.base import ProviderConfig

def test_gemini_json():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("GOOGLE_API_KEY not found in env")
        return

    provider = GeminiProvider(ProviderConfig(name="gemini", api_key=api_key))
    
    prompt = """
    Return a JSON object with a 'test' key and 'success' value. 
    The JSON must be exactly: {"test": "success"}
    """
    
    print("Testing generate_structured (no schema)...")
    try:
        resp = provider.generate_structured(prompt)
        print(f"Content: {resp.content}")
        data = json.loads(resp.content)
        print(f"Parsed: {data}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_gemini_json()
