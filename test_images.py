from pathlib import Path
from PIL import Image

thu_muc = Path(__file__).resolve().parent / "assets"

danh_sach_anh = [
    "an_uong.png",
    "sieu_thi.png",
    "nghieng.png"
]

for ten_anh in danh_sach_anh:
    duong_dan = thu_muc / ten_anh

    try:
        with Image.open(duong_dan) as img:
            img.verify()

        print("PASS -", ten_anh)

    except Exception as e:
        print("FAIL -", ten_anh, ":", e)
