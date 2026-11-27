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

MODEL_NAME = "gemini-3.5-flash-lite"

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
    with Image.open(image_path) as image:
        return _generate_json([image.convert("RGB"), PROMPT])


def extract_invoice_batch(files):
    """Đọc nhiều ảnh trong một yêu cầu, ghép kết quả bằng ID của ảnh."""
    rules = PROMPT.replace(
        "Hãy đọc ảnh và chỉ trả về một đối tượng JSON hợp lệ.",
        "Áp dụng các quy tắc và cấu trúc hóa đơn dưới đây riêng cho từng ảnh.",
    )
    contents = [
        rules
        + '\nTrả về một mảng JSON. Mỗi phần tử có "image_id" đúng như nhãn ngay trước ảnh '
        + 'và "invoice" là đối tượng hóa đơn theo cấu trúc trên. Nếu không đọc được, '
        + 'đặt "invoice" thành null. Trả về đúng một phần tử cho mỗi ID, không gộp ảnh.'
    ]
    expected = set()
    for image_id, uploaded in files.items():
        uploaded.seek(0)
        try:
            with Image.open(uploaded) as image:
                rgb = image.convert("RGB")
        except (OSError, ValueError, Image.DecompressionBombError):
            continue
        contents.extend([f"image_id: {image_id}", rgb])
        expected.add(image_id)

    if not expected:
        return {}
    response = _generate_json(contents)
    if not isinstance(response, list):
        raise ValueError("AI không trả về danh sách kết quả cho nhóm ảnh.")

    invoices = {}
    seen = set()
    for result in response:
        if not isinstance(result, dict):
            continue
        image_id = result.get("image_id")
        if not isinstance(image_id, str) or image_id not in expected:
            continue
        if image_id in seen:
            invoices.pop(image_id, None)
            continue
        seen.add(image_id)
        invoice = result.get("invoice")
        if isinstance(invoice, dict) and invoice:
            invoices[image_id] = invoice
    return invoices


def _generate_json(contents):
    client = get_client()
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
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
