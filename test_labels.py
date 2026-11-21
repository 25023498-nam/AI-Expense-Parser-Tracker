import json
from pathlib import Path
from datetime import date

# Đường dẫn thư mục dự án
ROOT = Path(__file__).resolve().parent

# Đường dẫn file labels.json
LABELS_PATH = ROOT / "assets" / "labels.json"

# Danh sách các ảnh cần có nhãn
DANH_SACH_ANH = [
    "an_uong.png",
    "sieu_thi.png",
    "nghieng.png"
]

# Các trường bắt buộc của mỗi hóa đơn
CAC_TRUONG = [
    "ten_cua_hang",
    "ngay_thanh_toan",
    "tong_tien",
    "danh_muc"
]

# Đọc labels.json
with open(LABELS_PATH, "r", encoding="utf-8") as file:
    labels = json.load(file)

print("=== KIỂM TRA LABELS.JSON ===")

for ten_anh in DANH_SACH_ANH:

    print("\nĐang kiểm tra:", ten_anh)

    # Kiểm tra ảnh có tồn tại
    anh_path = ROOT / "assets" / ten_anh

    if not anh_path.is_file():
        print("FAIL - Không tìm thấy ảnh")
        continue

    # Kiểm tra hóa đơn có nhãn chưa
    if ten_anh not in labels:
        print("FAIL - Chưa có dữ liệu nhãn")
        continue

    hoa_don = labels[ten_anh]

    if not isinstance(hoa_don, dict):
        print("FAIL - Nhãn phải là dict")
        continue

    # Kiểm tra các trường bắt buộc
    if any(cot not in hoa_don for cot in CAC_TRUONG):
        print("FAIL - Thiếu trường dữ liệu")
        continue

    # Kiểm tra tên cửa hàng và danh mục
    if any(
        not isinstance(hoa_don[cot], str)
        or not hoa_don[cot].strip()
        for cot in ["ten_cua_hang", "danh_muc"]
    ):
        print("FAIL - Tên cửa hàng hoặc danh mục sai")
        continue

    # Kiểm tra số tiền
    if type(hoa_don["tong_tien"]) is not int \
            or hoa_don["tong_tien"] < 0:
        print("FAIL - Tổng tiền không hợp lệ")
        continue

    # Kiểm tra ngày
    try:
        ngay = hoa_don["ngay_thanh_toan"]
        date.fromisoformat(ngay)

        if len(ngay) != 10:
            raise ValueError()

    except (ValueError, TypeError):
        print("FAIL - Ngày thanh toán không hợp lệ")
        continue

    print("PASS - Nhãn có cấu trúc hợp lệ")

print("\nĐã hoàn tất kiểm tra!")