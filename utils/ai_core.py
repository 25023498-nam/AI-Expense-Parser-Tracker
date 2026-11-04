import os
import json
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

# Đường dẫn tuyệt đối đến thư mục gốc dự án (file này nằm trong utils/)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

MODEL_NAME = "gemini-flash-lite-latest"

PROMPT = """
Bạn là hệ thống trích xuất dữ liệu hóa đơn. Hãy đọc ảnh và trả về dữ liệu dạng JSON thuần túy,
không chứa markdown ```json, không kèm câu chào hỏi, với cấu trúc sau:
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


def get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Chưa có GEMINI_API_KEY. Hãy tạo file .env theo hướng dẫn trong README.")
    return genai.Client(api_key=api_key)


def extract_invoice_data(image_path):
    """Đọc ảnh hóa đơn và trả về dict theo schema đã định nghĩa."""
    client = get_client()
    img = Image.open(image_path).convert("RGB")

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[img, PROMPT],
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )

    text = (response.text or "").strip()
    # Dự phòng: bỏ markdown nếu mô hình vẫn trả về ```json
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"AI trả về không phải JSON hợp lệ: {text[:200]}") from e


# --- CHẠY TEST TRỰC TIẾP ---
if __name__ == "__main__":
    test_image = BASE_DIR / "assets" / "nghieng.png"
    print("Đang gửi ảnh lên Gemini API...")
    try:
        hoa_don = extract_invoice_data(test_image)
    except Exception as e:
        print("Lỗi:", e)
        raise SystemExit(1)

    print("\n--- KẾT QUẢ AI TRẢ VỀ ---")
    print(json.dumps(hoa_don, ensure_ascii=False, indent=2))
    print("Tổng tiền:", hoa_don.get("tong_tien"))