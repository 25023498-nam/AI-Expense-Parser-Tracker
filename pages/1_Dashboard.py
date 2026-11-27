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

if df.empty:
    st.info("Chưa có hóa đơn nào. Hãy nhập hóa đơn ở trang chính.")
    st.stop()

df["ngay"] = pd.to_datetime(df["ngay_thanh_toan"], errors="coerce")
df["tong_tien"] = pd.to_numeric(df["tong_tien"], errors="coerce").fillna(0)

# Tạo bảng phụ chỉ gồm các hóa đơn có ngày hợp lệ
df_co_ngay = df.dropna(subset=["ngay"]).copy()

# Tạo cột tháng cho biểu đồ
df_co_ngay["thang"] = df_co_ngay["ngay"].dt.strftime("%Y-%m")


# ---------- Bước 2: con số tóm tắt ----------
c1, c2, c3 = st.columns(3)
c1.metric("Tổng chi", dinh_dang_tien(df["tong_tien"].sum()))
c2.metric("Số hóa đơn", len(df))
c3.metric("Trung bình mỗi hóa đơn", dinh_dang_tien(df["tong_tien"].mean()))

# ---------- Bước 3: biểu đồ theo tháng ----------
st.subheader("Chi tiêu theo tháng")

if df_co_ngay.empty:
    st.info("Chưa có hóa đơn nào có ngày hợp lệ.")
else:
    theo_thang = (df_co_ngay.groupby("thang")["tong_tien"].sum().sort_index())
    st.bar_chart(theo_thang)

# ---------- Bước 4: biểu đồ theo ngày ----------
st.subheader("Chi tiêu theo ngày")

if df_co_ngay.empty:
    st.info("Chưa có hóa đơn nào có ngày hợp lệ.")
else:
    theo_ngay = (
        df_co_ngay.groupby("ngay")["tong_tien"]
        .sum()
        .sort_index()
    )
    st.line_chart(theo_ngay)

# ---------- Bước 5: biểu đồ theo danh mục ----------
st.subheader("Chi tiêu theo danh mục")
theo_dm = df.groupby("danh_muc")["tong_tien"].sum().sort_values(ascending=False)
st.bar_chart(theo_dm)

# ---------- Bước 6: bảng chi tiết ----------
st.subheader("Chi tiết từng hóa đơn")

df["ngay_hien_thi"] = (df["ngay"].dt.strftime("%Y-%m-%d").fillna("Chưa có ngày"))

bang = (
    df.sort_values("ngay", ascending=False, na_position="last")
    [["ngay_hien_thi", "ten_cua_hang", "tong_tien", "danh_muc"]]
    .rename(columns={
        "ngay_hien_thi": "Ngày",
        "ten_cua_hang": "Cửa hàng/Đơn vị",
        "tong_tien": "Tổng tiền",
        "danh_muc": "Danh mục",
    })
)

bang["Tổng tiền"] = bang["Tổng tiền"].apply(dinh_dang_tien)

st.dataframe(bang, hide_index=True, use_container_width=True)