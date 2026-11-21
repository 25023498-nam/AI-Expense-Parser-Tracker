import csv
from pathlib import Path
from datetime import datetime

COT_CSV = [
    "ten_cua_hang",
    "ngay_thanh_toan",
    "tong_tien",
    "danh_muc"
]


def save_invoice_to_csv(hoa_don):

    # Kiểm tra dữ liệu đầu vào
    if not isinstance(hoa_don, dict):
        raise TypeError("Dữ liệu hóa đơn phải là dict")

    # Kiểm tra các trường bắt buộc
    for cot in COT_CSV:
        if cot not in hoa_don or hoa_don[cot] is None:
            raise ValueError(f"Thiếu dữ liệu: {cot}")

    # Kiểm tra tên cửa hàng và danh mục
    for cot in ["ten_cua_hang", "danh_muc"]:
        if not isinstance(hoa_don[cot], str) or not hoa_don[cot].strip():
            raise ValueError(f"Dữ liệu không hợp lệ: {cot}")

    # Kiểm tra ngày thanh toán
    ngay = hoa_don["ngay_thanh_toan"]
    if not isinstance(ngay, str):
        raise ValueError("Ngày thanh toán phải là chuỗi")

    try:
        ngay_hop_le = datetime.strptime(ngay, "%Y-%m-%d")
        if ngay_hop_le.strftime("%Y-%m-%d") != ngay:
            raise ValueError()
    except ValueError:
        raise ValueError("Ngày không hợp lệ, cần YYYY-MM-DD")

    # Kiểm tra tổng tiền
    tien = hoa_don["tong_tien"]

    if type(tien) is not int or tien < 0:
        raise ValueError("Tổng tiền phải là số nguyên không âm")

    # Đường dẫn đến file CSV tại thư mục gốc
    thu_muc_goc = Path(__file__).resolve().parents[1]
    duong_dan = thu_muc_goc / "hoa_don_tu_json.csv"

    # Kiểm tra file có rỗng hoặc chưa tồn tại
    ghi_header = (
        not duong_dan.exists()
        or duong_dan.stat().st_size == 0
    )

    # Ghi dữ liệu vào CSV
    with open(
        duong_dan,
        mode="a",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=COT_CSV
        )

        if ghi_header:
            writer.writeheader()

        writer.writerow({
            cot: hoa_don[cot] for cot in COT_CSV
        })

    return duong_dan