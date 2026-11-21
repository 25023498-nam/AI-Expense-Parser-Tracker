import csv

from utils.data_core import save_invoice_to_csv

# Bước 1: Tạo dữ liệu hóa đơn mẫu
hoa_don = {
    "ten_cua_hang": "Happy Mart Terra An Hưng",
    "ngay_thanh_toan": "2026-08-13",
    "tong_tien": 185450,
    "danh_muc": "Mua sắm",
    "danh_sach_mon": []
}


# Bước 2: Gọi hàm lưu hóa đơn
try:
    duong_dan = save_invoice_to_csv(hoa_don)

    print("Lưu hóa đơn thành công!")
    print("Đường dẫn file:", duong_dan)

except Exception as e:
    print("Có lỗi xảy ra:", e)


print("\n=== KIỂM THỬ DỮ LIỆU LỖI ===")

# Hàm đếm số hóa đơn trong CSV
def dem_hoa_don(duong_dan):
    with open(
        duong_dan,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        return len(list(csv.DictReader(file)))


# Hóa đơn bị thiếu tổng tiền
hoa_don_loi = {
    "ten_cua_hang": "Happy Mart",
    "ngay_thanh_toan": "2026-08-13",
    "danh_muc": "Mua sắm"
}

# Đếm số dòng dữ liệu trước khi kiểm thử
so_dong_truoc = dem_hoa_don(duong_dan)

try:
    save_invoice_to_csv(hoa_don_loi)

except ValueError as e:
    print("PASS - Phát hiện dữ liệu thiếu:", e)

else:
    print("FAIL - Không phát hiện dữ liệu thiếu")

# Đếm số dòng sau khi kiểm thử
so_dong_sau = dem_hoa_don(duong_dan)

if so_dong_truoc == so_dong_sau:
    print("PASS - Không lưu hóa đơn lỗi")
else:
    print("FAIL - Đã ghi thêm dữ liệu không hợp lệ")

print("\n=== KIỂM THỬ NGÀY VÀ SỐ TIỀN ===")

# Kiểm tra ngày thanh toán sai
hoa_don_sai_ngay = {
    "ten_cua_hang": "Happy Mart",
    "ngay_thanh_toan": "2026-13-40",
    "tong_tien": 185450,
    "danh_muc": "Mua sắm"
}

# Kiểm tra tổng tiền sai kiểu dữ liệu
hoa_don_sai_tien = {
    "ten_cua_hang": "Happy Mart",
    "ngay_thanh_toan": "2026-08-13",
    "tong_tien": "185450",
    "danh_muc": "Mua sắm"
}

# Danh sách các trường hợp cần thử
danh_sach_test = [
    ("Ngày không hợp lệ", hoa_don_sai_ngay),
    ("Tổng tiền sai kiểu", hoa_don_sai_tien)
]

for ten_test, du_lieu in danh_sach_test:

    so_dong_truoc = dem_hoa_don(duong_dan)

    try:
        save_invoice_to_csv(du_lieu)

    except (ValueError, TypeError) as e:
        so_dong_sau = dem_hoa_don(duong_dan)

        if so_dong_truoc == so_dong_sau:
            print("PASS -", ten_test, ":", e)
        else:
            print("FAIL - Đã lưu dữ liệu lỗi")

    else:
        print("FAIL - Không phát hiện:", ten_test)
