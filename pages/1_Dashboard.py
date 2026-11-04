import pandas as pd
import streamlit as st

from utils.data_core import load_expenses


def dinh_dang_tien(so):
    """Hiển thị số tiền kiểu Việt Nam: 215000 -> 215.000 đ"""
    return f"{so:,.0f}".replace(",", ".") + " đ"


st.set_page_config(page_title="Dashboard chi tiêu", page_icon="📊")
st.title("📊 Dashboard chi tiêu")

# ---------- Bước 1: đọc sổ và làm sạch ----------
df = load_expenses()

df["ngay"] = pd.to_datetime(df["ngay_thanh_toan"], errors="coerce")
df["tong_tien"] = pd.to_numeric(df["tong_tien"], errors="coerce").fillna(0)
df = df.dropna(subset=["ngay"])  # bỏ dòng có ngày không đọc được
df["thang"] = df["ngay"].dt.strftime("%Y-%m")

if df.empty:
    st.info("Chưa có hóa đơn nào. Hãy nhập hóa đơn ở trang chính.")
    st.stop()

# ---------- Bước 2: con số tóm tắt ----------
c1, c2, c3 = st.columns(3)
c1.metric("Tổng chi", dinh_dang_tien(df["tong_tien"].sum()))
c2.metric("Số hóa đơn", len(df))
c3.metric("Trung bình mỗi hóa đơn", dinh_dang_tien(df["tong_tien"].mean()))

# ---------- Bước 3: biểu đồ theo tháng ----------
st.subheader("Chi tiêu theo tháng")
theo_thang = df.groupby("thang")["tong_tien"].sum().sort_index()
st.bar_chart(theo_thang)

# ---------- Bước 4: biểu đồ theo ngày ----------
st.subheader("Chi tiêu theo ngày")
theo_ngay = df.groupby("ngay")["tong_tien"].sum().sort_index()
st.line_chart(theo_ngay)

# ---------- Bước 5: biểu đồ theo danh mục ----------
st.subheader("Chi tiêu theo danh mục")
theo_dm = df.groupby("danh_muc")["tong_tien"].sum().sort_values(ascending=False)
st.bar_chart(theo_dm)

# ---------- Bước 6: bảng chi tiết ----------
st.subheader("Chi tiết từng hóa đơn")
bang = (
    df.sort_values("ngay", ascending=False)
    [["ngay_thanh_toan", "ten_cua_hang", "tong_tien", "danh_muc"]]
    .rename(columns={
        "ngay_thanh_toan": "Ngày",
        "ten_cua_hang": "Cửa hàng",
        "tong_tien": "Tổng tiền",
        "danh_muc": "Danh mục",
    })
)
st.dataframe(bang, hide_index=True, use_container_width=True)