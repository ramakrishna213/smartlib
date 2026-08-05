from google import genai

client = genai.Client(
    api_key="AQ.Ab8RN6Ib59pvWKPGnZQtFG_E7oRCrjdXkZMmb4z-o_sT493ogg"
)

response = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents="Hello"
)

print(response.text)