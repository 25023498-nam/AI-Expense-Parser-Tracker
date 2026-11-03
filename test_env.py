import os
from dotenv import load_dotenv

load_dotenv() # Nạp cấu hình từ file

api_key = os.getenv("GEMINI_API_KEY") # Lấy một giá trị cụ thể.

if api_key:
    print("Đã đọc được API key!")
else:
    print("Chưa tìm thấy API key.")