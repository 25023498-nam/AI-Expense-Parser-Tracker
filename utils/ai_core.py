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
Bạn là hệ thống trích xuất dữ liệu từ ảnh hóa đơn, biên lai và chứng từ thanh toán.

Hãy đọc ảnh và chỉ trả về một đối tượng JSON hợp lệ.
Không sử dụng markdown ```json, không giải thích và không thêm lời chào.

Quy tắc:
1. "ten_cua_hang" là tên cửa hàng, siêu thị, nhà hàng hoặc đơn vị cung cấp dịch vụ.
   Ví dụ: EVN, công ty nước, nhà mạng, bệnh viện hoặc trường học.
2. Nếu không xác định được giá trị nào, trả về null, không tự suy đoán.
3. "ngay_thanh_toan" là ngày khách hàng thực sự thanh toán.
   Nếu ảnh chỉ có ngày phát hành hoặc hạn thanh toán mà không có ngày thanh toán, trả về null.
4. Ngày phải có định dạng YYYY-MM-DD.
5. "tong_tien" là số tiền cuối cùng khách hàng phải trả hoặc đã trả.
6. Các giá tiền phải là số, không chứa dấu chấm phân cách, ký hiệu tiền tệ hoặc chữ.
7. "danh_muc" chỉ nhận một trong các giá trị:
   "Ăn uống", "Mua sắm", "Di chuyển", "Hóa đơn & tiện ích",
   "Y tế", "Giáo dục", "Giải trí", "Khác".
8. Với hóa đơn dịch vụ không có danh sách món, hãy tạo một mục mô tả dịch vụ.
   Ví dụ: "Tiền điện tháng 10/2026", "Cước Internet tháng 10/2026".
9. Không được tự tạo thông tin không xuất hiện hoặc không thể suy ra chắc chắn từ ảnh.

Cấu trúc JSON:
{
  "ten_cua_hang": "Tên cửa hàng hoặc đơn vị cung cấp dịch vụ",
  "ngay_thanh_toan": "YYYY-MM-DD hoặc null",
  "tong_tien": 0,
  "danh_muc": "Một trong các danh mục quy định",
  "danh_sach_mon": [
    {
      "ten_mon": "Tên mặt hàng hoặc nội dung dịch vụ",
      "gia": 0
    }
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