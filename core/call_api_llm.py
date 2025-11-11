from google import genai
from google.genai import types
import time 
GOOGLE_API =  ""
client = genai.Client(api_key= GOOGLE_API)

def call_api_gemi(prompt, model = '2.0-flash', temperture = 0.1, max_retries = 200, retry_delay = 2):
    for attempt in range(max_retries):
        try:
            # Tạo nội dung
            response = client.models.generate_content( model=f"gemini-{model}", contents=prompt, config=types.GenerateContentConfig( temperature = temperture ))
        
            return response.text
        except Exception as e:
            print(f"Lần thử {attempt + 1} thất bại: {e}")
            if attempt < max_retries - 1:
                print(f"Đang thử lại sau {retry_delay} giây...")
                time.sleep(retry_delay)
            else:
                print("Đã hết số lần thử lại. Thất bại.") 
                return None