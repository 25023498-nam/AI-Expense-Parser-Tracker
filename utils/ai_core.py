import os
import json
from google import genai
from dotenv import load_dotenv
from PIL import Image

# 1. Load API Key từ file .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

def extract_invoice_data(image_path):
    # Mở file ảnh
    img = Image.open(image_path)
    
    # Kỹ thuật Prompt ép AI trả về chuẩn JSON
    prompt = """
    Bạn là hệ thống trích xuất dữ liệu hóa đơn. Hãy đọc ảnh và trả về dữ liệu dạng JSON thuần túy (không chứa markdown ```json, không kèm câu chào hỏi) với cấu trúc sau:
    {
      "ten_cua_hang": "Tên cửa hàng/siêu thị",
      "ngay_thanh_toan": "YYYY-MM-DD",
      "tong_tien": 0,
      "danh_muc": "Ăn uống/Mua sắm/Di chuyển/Khác",
      "danh_sach_mon": [
        {"ten_mon": "tên item", "gia": 0}
      ]
    }
    """
    
    # Gửi ảnh và yêu cầu trích xuất đến Gemini
    response = client.models.generate_content(
        model="gemini-flash-lite-latest",
        contents=[img, prompt]
    )
    
    return response.text

# --- CHẠY TEST TRỰC TIẾP ---
if __name__ == "__main__":
    test_image = r"assets/nghieng.png"  # Thay đường dẫn ảnh của bạn
    print("Đang gửi ảnh lên Gemini API...")
    result = extract_invoice_data(test_image)
    print("\n--- KẾT QUẢ AI TRẢ VỀ ---")
    print(result)
    hoa_don = json.loads(result)
    print("JSON hợp lệ, tổng tiền:", hoa_don["tong_tien"])