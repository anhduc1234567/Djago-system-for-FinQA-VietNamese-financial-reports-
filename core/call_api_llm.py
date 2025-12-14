from google import genai
from google.genai import types
import time 
import os
from dotenv import load_dotenv
load_dotenv()

GOOGLE_API = os.getenv("GOOGLE_API")
client = genai.Client(api_key= GOOGLE_API)

def call_api_gemi(prompt, model = '', temperture = 0, max_retries = 20, retry_delay = 2):

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content( model=model, contents=prompt, config=types.GenerateContentConfig( temperature = temperture ))
            return response.text
        except Exception as e:
            print(f"Lần thử {attempt + 1} thất bại: {e}")
            if attempt < max_retries - 1:
                print(f"Đang thử lại sau {retry_delay} giây...")
                time.sleep(retry_delay)
            else:
                print("Đã hết số lần thử lại. Thất bại.") 
                return None

