import json
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "database.csv"

COLUMNS = ["ngay_thanh_toan", "ten_cua_hang", "tong_tien", "danh_muc", "danh_sach_mon"]


def ensure_database():
    """Tạo thư mục data và file CSV với tiêu đề cột, nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists():
        pd.DataFrame(columns=COLUMNS).to_csv(DB_PATH, index=False, encoding="utf-8-sig")


def load_expenses():
    """Đọc toàn bộ lịch sử chi tiêu thành một bảng."""
    ensure_database()
    df = pd.read_csv(DB_PATH, encoding="utf-8-sig")
    df["tong_tien"] = pd.to_numeric(df["tong_tien"], errors="coerce").fillna(0)
    return df


def _to_int(value):
    """Chuyển số tiền về số nguyên. Chấp nhận cả '65.000' và 65000."""
    if isinstance(value, (int, float)):
        return int(value)
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    return int(digits) if digits else 0


def _clean_record(record):
    """Làm sạch một hóa đơn trước khi ghi vào CSV."""
    danh_sach = record.get("danh_sach_mon") or []
    return {
        "ngay_thanh_toan": str(record.get("ngay_thanh_toan") or "").strip(),
        "ten_cua_hang": str(record.get("ten_cua_hang") or "").strip(),
        "tong_tien": _to_int(record.get("tong_tien") or 0),
        "danh_muc": str(record.get("danh_muc") or "Khác").strip(),
        "danh_sach_mon": json.dumps(danh_sach, ensure_ascii=False),
    }


def save_expense(record):
    """Ghi thêm một hóa đơn vào cuối file CSV."""
    ensure_database()
    row = _clean_record(record)
    pd.DataFrame([row], columns=COLUMNS).to_csv(
        DB_PATH, mode="a", header=False, index=False, encoding="utf-8-sig"
    )