from datetime import datetime

import pandas as pd
import streamlit as st
import base64

from pathlib import Path
from utils.ai_core import extract_invoice_data
from utils.data_core import load_expenses, save_expense

def set_background():
    def png_url(filename):
        path = Path(__file__).resolve().parent / filename
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f'url("data:image/png;base64,{encoded}")'

    light = png_url("light_background.png")
    dark = png_url("dark_background.png")
    initial = dark if st.context.theme.type == "dark" else light

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: {initial};
            background-image: light-dark({light}, {dark});
            background-size: 100% 100%;
            background-position: top center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style> 
        """,
            unsafe_allow_html=True
    )

set_background() 

DANH_MUC = ["Ăn uống", "Mua sắm", "Di chuyển", "Khác"]


def safe_int(value):
    """Chuyển '150.000', 150000 hoặc 150000.0 thành số nguyên. Lỗi thì trả về 0."""
    if isinstance(value, (int, float)):
        return int(value)
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return int(digits) if digits else 0


st.set_page_config(page_title="AI Expense Tracker", page_icon="🧾", layout ="centered")
st.markdown(
    """
    <style>
        .hero {
            padding: 24px 28px;
            margin-bottom: 24px;
            border-radius: 20px;
            background: linear-gradient(
                110deg,
                light-dark(#DED8F8, #25263D) 0%,
                light-dark(#E8F5FF, #1D3042) 100%
            );
            border: 1px solid light-dark(#DED9FF, #484C68);
            box-shadow: 0 8px 24px rgba(76, 81, 191, 0.08);
        }

        .hero-title {
            color: light-dark(#252B48, #F6F4FF);
            font-size: 36px;
            font-weight: 750;
            margin: 0;
        }

        .hero-description {
            color: light-dark(#525E73, #CBD5E1);
            font-size: 16px;
            margin: 8px 0 0 0;
        }

        .section-label {
            color: light-dark(#5548C8, #C3BCFF);
            font-size: 14px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }
    </style>

    <div class="hero">
        <p class="section-label">AI Expense Parser</p>
        <h1 class="hero-title">🧾 Nhập hóa đơn</h1>
        <p class="hero-description">
            Tải ảnh lên, để AI trích xuất và quản lý chi tiêu của bạn.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
#st.title("🧾 Nhập hóa đơn")

# ---------- Bước 1: tải ảnh và gọi AI ----------
with st.container(border=True):
    st.subheader("1. Tải ảnh hóa đơn")

    uploaded = st.file_uploader(
        "Chọn ảnh PNG, JPG hoặc JPEG",
        type=["png", "jpg", "jpeg"]
    )

    trich_xuat = st.button(
        "✨ Trích xuất bằng AI",
        type="primary",
        use_container_width=True,
        disabled=uploaded is None
    )

    if uploaded is not None and trich_xuat:
        # Đưa con trỏ về đầu file trước khi đọc
        uploaded.seek(0)

        with st.spinner("AI đang đọc hóa đơn..."):
            try:
                st.session_state["draft"] = extract_invoice_data(uploaded)
                st.session_state["draft_file"] = uploaded.name

                # Xóa bảng món của hóa đơn cũ
                st.session_state.pop("items", None)

            except Exception as e:
                st.error(f"Không đọc được hóa đơn: {e}")

# ---------- Bước 2: hiện form để sửa ----------
draft = st.session_state.get("draft")
cung_file = uploaded is not None and st.session_state.get("draft_file") == uploaded.name

if draft and cung_file:
    st.subheader("Kiểm tra và sửa")

    col1, col2 = st.columns(2)
    ten = col1.text_input("Tên cửa hàng", value=str(draft.get("ten_cua_hang", "")))
    ngay_ai = draft.get("ngay_thanh_toan")

    # Đổi None, "None" và "null" thành ô trống
    if ngay_ai is None or str(ngay_ai).strip().lower() in {"none", "null"}:
        ngay_ai = ""

    ngay = col2.text_input(
        "Ngày (YYYY-MM-DD)",
        value=str(ngay_ai)
    )
    tong = col1.number_input(
        "Tổng tiền (đ)", min_value=0, step=1000, value=safe_int(draft.get("tong_tien"))
    )
    dm = draft.get("danh_muc")
    danh_muc = col2.selectbox(
        "Danh mục",
        DANH_MUC,
        index=DANH_MUC.index(dm) if dm in DANH_MUC else DANH_MUC.index("Khác"),
    )

    st.markdown("**Danh sách món** (sửa, thêm hoặc xóa dòng được)")
    items_df = pd.DataFrame(draft.get("danh_sach_mon") or [], columns=["ten_mon", "gia"])
    items = st.data_editor(items_df, num_rows="dynamic", key="items")

    # ---------- Bước 3: kiểm tra và lưu ----------
    if st.button("Xác nhận và lưu", key="xac_nhan_luu"):
    # Làm sạch ngày
        ngay = ngay.strip()

        if ngay.lower() in {"none", "null"}:
            ngay = ""

        # Chỉ kiểm tra nếu có nhập ngày
        if ngay:
            try:
                datetime.strptime(ngay, "%Y-%m-%d")
            except ValueError:
                st.error(
                    "Ngày phải đúng dạng YYYY-MM-DD, ví dụ 2025-01-15."
                )
                st.stop()

        # Xử lý danh sách món
        mon = (
            items.dropna(subset=["ten_mon"])
            .assign(
                gia=lambda d: pd.to_numeric(
                    d["gia"],
                    errors="coerce"
                ).fillna(0).astype(int)
            )
            .to_dict("records")
        )

        # Dữ liệu chuẩn bị lưu
        hoa_don_moi = {
            "ngay_thanh_toan": ngay or None,
            "ten_cua_hang": ten,
            "tong_tien": tong,
            "danh_muc": danh_muc,
            "danh_sach_mon": mon,
        }

        # Ghi thật vào CSV
        save_expense(hoa_don_moi)

        # Chỉ xóa bản nháp sau khi đã ghi CSV
        st.session_state.pop("draft", None)
        st.session_state.pop("draft_file", None)

        # Chỉ hiện thành công sau khi save_expense chạy xong
        st.success("Đã lưu hóa đơn vào sổ.")
# ---------- Chân trang ----------
st.divider()
so = load_expenses()
st.caption(f"Sổ hiện có {len(so)} hóa đơn.")