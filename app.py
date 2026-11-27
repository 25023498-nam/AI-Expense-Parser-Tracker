from datetime import datetime
from hashlib import sha256

import pandas as pd
import streamlit as st
import base64

from pathlib import Path
from utils.ai_core import extract_invoice_batch, extract_invoice_data
from utils.data_core import DuplicateImageError, load_expenses, save_expense

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

MAX_IMAGES_PER_REQUEST = 5
DUPLICATE_MESSAGE = "Ảnh này đã được dùng cho một hóa đơn đã lưu."


def review_invoice(image_hash, draft, drafts):
    col1, col2 = st.columns(2)
    ten = col1.text_input("Tên cửa hàng", value=str(draft.get("ten_cua_hang") or ""), key=f"store_{image_hash}")
    ngay_ai = draft.get("ngay_thanh_toan")

    # Đổi None, "None" và "null" thành ô trống
    if ngay_ai is None or str(ngay_ai).strip().lower() in {"none", "null"}:
        ngay_ai = ""

    ngay = col2.text_input(
        "Ngày (YYYY-MM-DD)",
        value=str(ngay_ai), key=f"date_{image_hash}"
    )
    tong = col1.number_input(
        "Tổng tiền (đ)", min_value=0, step=1000, value=max(0, safe_int(draft.get("tong_tien"))),
        key=f"total_{image_hash}"
    )
    dm = draft.get("danh_muc")
    danh_muc = col2.selectbox(
        "Danh mục",
        DANH_MUC,
        index=DANH_MUC.index(dm) if dm in DANH_MUC else DANH_MUC.index("Khác"),
        key=f"category_{image_hash}",
    )

    st.markdown("**Danh sách món** (sửa, thêm hoặc xóa dòng được)")
    items_df = pd.DataFrame(draft.get("danh_sach_mon") or [], columns=["ten_mon", "gia"])
    items = st.data_editor(items_df, num_rows="dynamic", key=f"items_{image_hash}")

    # ---------- Bước 3: kiểm tra và lưu ----------
    if st.button("Xác nhận và lưu", key=f"save_{image_hash}"):
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
                return

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
            "image_hash": image_hash,
        }

        # Ghi thật vào CSV
        try:
            save_expense(hoa_don_moi)
        except DuplicateImageError:
            st.warning(DUPLICATE_MESSAGE)
        except OSError:
            st.error("Chưa lưu được hóa đơn. Hãy đóng sổ CSV nếu đang mở rồi thử lại.")
        else:
            drafts.pop(image_hash, None)
            st.success("Đã lưu hóa đơn vào sổ.")


with st.container(border=True):
    st.subheader("1. Tải ảnh hóa đơn")
    uploads = st.file_uploader(
        "Chọn ảnh PNG, JPG hoặc JPEG",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )
    saved_hashes = set(load_expenses()["image_hash"].dropna())
    selected = {}
    for uploaded in uploads:
        image_hash = sha256(uploaded.getbuffer()).hexdigest()
        if image_hash in saved_hashes:
            st.warning(f"{uploaded.name} — {DUPLICATE_MESSAGE}")
        elif image_hash in selected:
            st.warning(f"{uploaded.name} — Ảnh trùng trong lượt tải lên.")
        else:
            selected[image_hash] = uploaded

    drafts = {
        image_hash: draft
        for image_hash, draft in st.session_state.get("drafts", {}).items()
        if image_hash in selected
    }
    st.session_state["drafts"] = drafts
    pending = {image_hash: file for image_hash, file in selected.items() if image_hash not in drafts}

    # Giữ khả năng trích xuất lại khi chỉ chọn một ảnh.
    if len(selected) == 1:
        pending = selected

    multiple = len(selected) > 1
    scan = st.button(
        "✨ Quét tất cả" if multiple else "✨ Trích xuất bằng AI",
        type="primary",
        use_container_width=True,
        disabled=not pending,
    )

    if scan and pending:
        with st.spinner("AI đang đọc hóa đơn..."):
            if multiple:
                pending_ids = list(pending)
                for start in range(0, len(pending_ids), MAX_IMAGES_PER_REQUEST):
                    group_ids = pending_ids[start:start + MAX_IMAGES_PER_REQUEST]
                    group = {image_hash: pending[image_hash] for image_hash in group_ids}
                    try:
                        results = extract_invoice_batch(group)
                    except Exception as error:
                        names = ", ".join(file.name for file in group.values())
                        st.error(f"Không đọc được nhóm ảnh ({names}): {error}")
                        continue

                    drafts.update(results)
                    for image_hash in group.keys() - results.keys():
                        st.warning(f"{group[image_hash].name} — Không nhận được kết quả cho ảnh này.")
            else:
                image_hash, uploaded = next(iter(pending.items()))
                uploaded.seek(0)
                try:
                    draft = extract_invoice_data(uploaded)
                except Exception as error:
                    st.error(f"Không đọc được hóa đơn: {error}")
                else:
                    drafts[image_hash] = draft
                    for widget in ("store", "date", "total", "category", "items"):
                        st.session_state.pop(f"{widget}_{image_hash}", None)

if drafts:
    st.subheader("Kiểm tra và sửa")
    for image_hash, uploaded in selected.items():
        if image_hash in drafts:
            with st.container(border=True):
                st.write(uploaded.name)
                if multiple:
                    st.image(uploaded.getvalue(), width=220)
                review_invoice(image_hash, drafts[image_hash], drafts)

# ---------- Chân trang ----------
st.divider()
so = load_expenses()
st.caption(f"Sổ hiện có {len(so)} hóa đơn.")
