from dotenv import load_dotenv
import os
from groq import Groq

load_dotenv("D:/food/.env")
api_key = os.getenv("GROQ_API_KEY")
print("API Key:", api_key[:8] + "...")  # Print first 8 chars for safety

try:
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": "Test"}],
        model="llama-3.3-70b-versatile"  # Updated model
    )
    print("Response:", response.choices[0].message.content)
except Exception as e:
    print("Error:", e)