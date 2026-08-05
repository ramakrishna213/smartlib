from dotenv import load_dotenv
import os
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print("API Key starts with:", api_key[:8])

client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Say Hello"
    )
    print("✅ API Key is VALID")
    print(response.text)
except Exception as e:
    print("❌ API Key is INVALID")
    print(e)