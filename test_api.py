import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(
    api_key = api_key,
    http_options = {"timeout": 30000}
)

print ("Đang gửi yêu cầu...", flush = True)

response = client.models.generate_content(
    model = "gemini-flash-lite-latest",
    contents = "Chỉ trả lời: Kết nối thành công!"
)
print (response.text)

client.close()