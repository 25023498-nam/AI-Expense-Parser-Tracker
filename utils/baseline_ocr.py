import json
import os
import re
import sys
import unicodedata
from datetime import date

import pytesseract
from PIL import Image, ImageOps

import shutil

def _find_tesseract():
    if os.environ.get("TESSERACT_CMD"):
        return os.environ["TESSERACT_CMD"]
    found = shutil.which("tesseract")
    if found:
        return found
    for p in (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
    ):
        if os.path.exists(p):
            return p
    return None

_cmd = _find_tesseract()
if _cmd:
    pytesseract.pytesseract.tesseract_cmd = _cmd
else:
    raise SystemExit("Chưa tìm thấy Tesseract. Hãy cài từ https://github.com/UB-Mannheim/tesseract/wiki")
OCR_LANG = "vie+eng"
OCR_CONFIG = "--oem 3 --psm 6"  # psm 6: một khối văn bản đồng nhất, hợp với hóa đơn


# ---------------------------------------------------------------- OCR
def preprocess(img: Image.Image) -> Image.Image:
    """Chuẩn hóa ảnh: sửa xoay EXIF, xám, tăng tương phản, phóng to nếu nhỏ."""
    img = ImageOps.exif_transpose(img)
    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img)
    if img.width < 1000:
        scale = 1000 / img.width
        img = img.resize((1000, int(img.height * scale)), Image.LANCZOS)
    return img


def ocr_text(image_path: str) -> str:
    img = preprocess(Image.open(image_path))
    return pytesseract.image_to_string(img, lang=OCR_LANG, config=OCR_CONFIG)


# ---------------------------------------------------------------- Helpers
def strip_accents(s: str) -> str:
    """Bỏ dấu tiếng Việt để regex không phụ thuộc OCR đọc đúng dấu."""
    s = s.replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def parse_amount(token: str):
    """'1.234.567' / '1,234,567' / '1.234.567,00' -> 1234567."""
    token = re.sub(r"[.,]\d{2}$", "", token) if re.search(r"[.,]\d{3}[.,]\d{2}$", token) else token
    digits = re.sub(r"[.,\s]", "", token)
    return int(digits) if digits.isdigit() else None


AMOUNT_RE = re.compile(r"\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{2})?|\d{4,}")
SEP_AMOUNT_RE = re.compile(r"(?<!\d)\d{1,3}(?:[.,]\d{3})+(?!\d)")


def amounts_in(line: str):
    out = []
    for m in AMOUNT_RE.finditer(line):
        v = parse_amount(m.group())
        if v is not None:
            out.append(v)
    return out


# ---------------------------------------------------------------- Ngày
DATE_PATTERNS = [
    # (regex, thứ tự nhóm: d, m, y)
    (re.compile(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})"), (3, 2, 1)),
    (re.compile(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})"), (1, 2, 3)),
    (re.compile(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{2})(?!\d)"), (1, 2, 3)),
    (re.compile(r"ngay\s*(\d{1,2})\s*thang\s*(\d{1,2})\s*nam\s*(\d{4})"), (1, 2, 3)),
]


def extract_date(text: str):
    t = strip_accents(text)
    for rx, (gd, gm, gy) in DATE_PATTERNS:
        for m in rx.finditer(t):
            d, mo, y = int(m.group(gd)), int(m.group(gm)), int(m.group(gy))
            if y < 100:
                y += 2000
            try:
                return date(y, mo, d).isoformat()  # YYYY-MM-DD
            except ValueError:
                continue
    return None


# ---------------------------------------------------------------- Tổng tiền
# Ưu tiên từ trên xuống: khóa nào khớp trước thì dùng
TOTAL_KEYS = [
    r"tong\s*thanh\s*toan", r"tong\s*cong", r"tong\s*tien", r"can\s*thanh\s*toan",
    r"thanh\s*tien", r"grand\s*total", r"total", r"tong",
]
EXCLUDE_KEYS = (
    r"khach\s*dua|tien\s*thua|tien\s*mat|giam\s*gia|chiet\s*khau"
    r"|\bvat\b|thue|sub\s*total|tam\s*tinh|diem"
)


def extract_total(text: str):
    lines = [strip_accents(l) for l in text.splitlines() if l.strip()]
    for key in TOTAL_KEYS:
        rx = re.compile(key)
        cands = []
        for i, line in enumerate(lines):
            if not rx.search(line) or re.search(EXCLUDE_KEYS, line):
                continue
            nums = amounts_in(line)
            if not nums and i + 1 < len(lines):  # số tiền nằm ở dòng kế tiếp
                nums = amounts_in(lines[i + 1])
            if nums:
                cands.append(nums[-1])
        if cands:
            return cands[-1]  # dòng khớp cuối cùng (thường là tổng cuối hóa đơn)
        # Fallback: số tiền lớn nhất (chỉ số có dấu phân cách nghìn)
    all_nums = [parse_amount(m.group()) for l in lines for m in SEP_AMOUNT_RE.finditer(l)]
    all_nums = [n for n in all_nums if n]
    return max(all_nums) if all_nums else None


# ---------------------------------------------------------------- Cửa hàng
def extract_store(text: str):
    """Heuristic: dòng đầu tiên có chữ cái, đủ dài, không phải địa chỉ/SĐT/ngày."""
    skip = re.compile(
        r"dia\s*chi|\b(?:dt|tel|sdt|hotline|mst)\b|ma\s*so\s*thue|www|http|\d{3,}"
        r"|hoa\s*don|phieu|receipt|invoice"
    )
    for line in text.splitlines():
        line = line.strip()
        if len(re.findall(r"[^\W\d_]", line)) < 3:
            continue
        if skip.search(strip_accents(line)):
            continue
        return line
    return None


# ---------------------------------------------------------------- API chính
def extract_invoice_data(image_path) -> dict:
    """Cùng chữ ký và schema với ai_core.extract_invoice_data."""
    text = ocr_text(str(image_path))
    return {
        "ten_cua_hang": extract_store(text) or "",
        "ngay_thanh_toan": extract_date(text) or "",
        "tong_tien": extract_total(text) or 0,
        "danh_muc": "Khác",
        "danh_sach_mon": [],  # Tesseract + regex không tách được món (mục 4.7)
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Dùng: python baseline_ocr.py <đường_dẫn_ảnh>")
    out = extract_invoice_data(sys.argv[1])
    print("--- CHỮ OCR ĐỌC ĐƯỢC ---")
    print(ocr_text(sys.argv[1]))
    print(json.dumps(out, ensure_ascii=False, indent=2))