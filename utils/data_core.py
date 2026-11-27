import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Lock

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "database.csv"

COLUMNS = ["ngay_thanh_toan", "ten_cua_hang", "tong_tien", "danh_muc", "danh_sach_mon", "image_hash"]
DATABASE_LOCK = Lock()


class DuplicateImageError(ValueError):
    """Ảnh này đã được dùng cho một hóa đơn đã lưu."""


def ensure_database():
    """Tạo thư mục data và file CSV với tiêu đề cột, nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists():
        pd.DataFrame(columns=COLUMNS).to_csv(DB_PATH, index=False, encoding="utf-8-sig")


def load_expenses():
    """Đọc toàn bộ lịch sử chi tiêu thành một bảng."""
    with DATABASE_LOCK:
        ensure_database()
        df = pd.read_csv(DB_PATH, encoding="utf-8-sig", dtype={"image_hash": str})
    if "image_hash" not in df.columns:
        df["image_hash"] = ""
    df["tong_tien"] = pd.to_numeric(df["tong_tien"], errors="coerce").fillna(0)
    return df


def image_already_saved(image_hash):
    return load_expenses()["image_hash"].eq(image_hash).any()


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
        "image_hash": record.get("image_hash") or "",
    }


def save_expense(record):
    """Kiểm tra trùng và lưu hóa đơn trong cùng một lần cập nhật CSV."""
    row = _clean_record(record)
    with DATABASE_LOCK:
        ensure_database()
        df = pd.read_csv(DB_PATH, dtype=str, keep_default_na=False, encoding="utf-8-sig")
        if "image_hash" not in df.columns:
            df["image_hash"] = ""
        if row["image_hash"] and df["image_hash"].eq(row["image_hash"]).any():
            raise DuplicateImageError

        updated = pd.concat([df, pd.DataFrame([row], columns=COLUMNS)], ignore_index=True)
        with NamedTemporaryFile(dir=DB_PATH.parent, delete=False) as temporary:
            temporary_path = Path(temporary.name)
        try:
            updated.to_csv(temporary_path, index=False, encoding="utf-8-sig")
            temporary_path.replace(DB_PATH)
        finally:
            temporary_path.unlink(missing_ok=True)
