from datetime import datetime

import pandas as pd
import streamlit as st

from utils.ai_core import extract_invoice_data
from utils.data_core import load_expenses, save_expense

DANH_MUC = ["Ăn uống", "Mua sắm", "Di chuyển", "Khác"]


def safe_int(value):
    """Chuyển '150.000', 150000 hoặc 150000.0 thành số nguyên. Lỗi thì trả về 0."""
    if isinstance(value, (int, float)):
        return int(value)
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return int(digits) if digits else 0


st.set_page_config(page_title="AI Expense Tracker", page_icon="🧾")
st.title("🧾 Nhập hóa đơn")

# ---------- Bước 1: tải ảnh và gọi AI ----------
uploaded = st.file_uploader("Chọn ảnh hóa đơn", type=["png", "jpg", "jpeg"])

if uploaded is not None and st.button("Trích xuất bằng AI"):
    uploaded.seek(0)  # tua băng về đầu trước khi đọc
    with st.spinner("Đang đọc hóa đơn..."):
        try:
            st.session_state["draft"] = extract_invoice_data(uploaded)
            st.session_state["draft_file"] = uploaded.name
            st.session_state.pop("items", None)  # xóa bảng món cũ
        except Exception as e:
            st.error(f"Không đọc được hóa đơn: {e}")

# ---------- Bước 2: hiện form để sửa ----------
draft = st.session_state.get("draft")
cung_file = uploaded is not None and st.session_state.get("draft_file") == uploaded.name

if draft and cung_file:
    st.subheader("Kiểm tra và sửa")

    col1, col2 = st.columns(2)
    ten = col1.text_input("Tên cửa hàng", value=str(draft.get("ten_cua_hang", "")))
    ngay = col2.text_input("Ngày (YYYY-MM-DD)", value=str(draft.get("ngay_thanh_toan", "")))
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
    if st.button("Xác nhận và lưu"):
        try:
            datetime.strptime(ngay, "%Y-%m-%d")
        except ValueError:
            st.error("Ngày phải đúng dạng YYYY-MM-DD, ví dụ 2025-01-15.")
        else:
            mon = (
                items.dropna(subset=["ten_mon"])
                .assign(gia=lambda d: pd.to_numeric(d["gia"], errors="coerce").fillna(0).astype(int))
                .to_dict("records")
            )
            save_expense({
                "ngay_thanh_toan": ngay,
                "ten_cua_hang": ten,
                "tong_tien": tong,
                "danh_muc": danh_muc,
                "danh_sach_mon": mon,
            })
            st.session_state.pop("draft", None)
            st.session_state.pop("draft_file", None)
            st.success("Đã lưu hóa đơn vào sổ.")

# ---------- Chân trang ----------
st.divider()
so = load_expenses()
st.caption(f"Sổ hiện có {len(so)} hóa đơn.")