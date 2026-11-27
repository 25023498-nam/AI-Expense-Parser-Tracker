# AI Expense Parser & Tracker

Ứng dụng web giúp ghi chép chi tiêu tự động từ ảnh hóa đơn. Người dùng tải ảnh hoặc chụp hóa đơn, AI (Google Gemini) đọc và trích xuất thông tin, người dùng kiểm tra và sửa nếu cần, sau đó dữ liệu được lưu vào file CSV trên máy để thống kê trên Dashboard.

> Dự án học tập của **Nhóm 18** – Học phần Trí tuệ nhân tạo (CS2046), Track 1.1 (Application). Chạy cục bộ trên máy cá nhân, không phải sản phẩm thương mại.

---

## Tính năng

- Tải ảnh hóa đơn từ máy hoặc chụp trực tiếp bằng camera.
- Trích xuất tự động: tên cửa hàng, ngày thanh toán, tổng tiền, danh mục và danh sách món kèm giá.
- Bảng kiểm duyệt cho phép sửa từng trường và từng món trước khi lưu.
- Lưu lịch sử chi tiêu vào `data/database.csv` trên máy của bạn.
- Dashboard thống kê theo tháng, theo ngày và theo danh mục.

## Công nghệ sử dụng

| Thành phần | Công nghệ |
| :--- | :--- |
| Ngôn ngữ | Python 3.10 trở lên |
| Giao diện | Streamlit |
| Mô hình AI | Gemini (Google AI), truy cập qua `google-genai` |
| Dữ liệu | pandas, CSV |
| Xử lý ảnh | Pillow |
| Cấu hình | python-dotenv |

---

## 1. Yêu cầu trước khi cài đặt

1. **Python 3.10 trở lên.** Kiểm tra bằng lệnh `python --version`. Tải tại [python.org](https://www.python.org/downloads/). Trên Windows, khi cài nhớ tick ô **Add python.exe to PATH**.
2. **Git.** Tải tại [git-scm.com](https://git-scm.com/downloads).
3. **Khóa API Gemini (miễn phí).** Vào [Google AI Studio](https://aistudio.google.com/apikey), đăng nhập bằng tài khoản Google, bấm **Create API key** và sao chép khóa.

> Khóa API là thông tin cá nhân. Không chia sẻ, không đưa lên GitHub. Gói miễn phí có giới hạn số lượt gọi mỗi phút và mỗi ngày, và giới hạn này có thể thay đổi theo thời gian của Google.

---

## 2. Tải mã nguồn

Mở terminal (PowerShell trên Windows, Terminal trên macOS/Linux) và chạy:

```bash
git clone https://github.com/<tên-tài-khoản>/AI-Expense-Parser-Tracker.git
cd AI-Expense-Parser-Tracker
```

Thay `<tên-tài-khoản>` bằng tên tài khoản GitHub của nhóm.

---

## 3. Tạo môi trường ảo

Môi trường ảo giữ thư viện của dự án tách khỏi Python chung của máy.

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Khi kích hoạt thành công, đầu dòng lệnh có chữ `(.venv)`.

> Nếu PowerShell báo lỗi về *execution policy*, chạy một lần lệnh sau rồi kích hoạt lại:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

---

## 4. Cài thư viện

Cài đặt bằng đúng Python của `.venv`:

**Windows:**

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**macOS / Linux:**

```bash
python -m pip install -r requirements.txt
```

Đợi đến khi thấy dòng `Successfully installed ...`.

---

## 5. Cấu hình khóa API

Tạo file `.env` từ file mẫu:

**Windows:**

```powershell
copy .env.example .env
```

**macOS / Linux:**

```bash
cp .env.example .env
```

Mở file `.env` và thay phần giá trị bằng khóa của bạn:

```
GEMINI_API_KEY=dán_khóa_của_bạn_vào_đây
```

Lưu ý:
- Không có khoảng trắng quanh dấu `=`.
- Không đặt trong dấu ngoặc kép.
- File `.env` nằm ở thư mục gốc của dự án, ngang hàng với `app.py`.

---

## 6. Kiểm tra AI hoạt động

Chạy thử bộ trích xuất trên ảnh mẫu:

**Windows:**

```powershell
.venv\Scripts\python.exe utils\ai_core.py
```

**macOS / Linux:**

```bash
python utils/ai_core.py
```

Nếu thành công, terminal in ra thông tin hóa đơn dạng JSON và tổng tiền. Nếu báo `Chưa có GEMINI_API_KEY`, quay lại bước 5.

---

## 7. Chạy ứng dụng

**Windows:**

```powershell
.venv\Scripts\python.exe -m streamlit run app.py
```

**macOS / Linux:**

```bash
python -m streamlit run app.py
```

Trình duyệt sẽ tự mở `http://localhost:8501`. Nếu không tự mở, sao chép địa chỉ này vào trình duyệt.

Để dừng ứng dụng, quay lại terminal và nhấn `Ctrl + C`.

### Cách sử dụng

1. Ở trang **Nhập hóa đơn**, chọn một ảnh hóa đơn (PNG, JPG, JPEG).
2. Bấm **Trích xuất bằng AI** và đợi kết quả.
3. Kiểm tra và sửa thông tin trong form. Có thể thêm, sửa hoặc xóa dòng món hàng.
4. Bấm **Xác nhận và lưu**. Hóa đơn được ghi vào sổ.
5. Chuyển sang trang **Dashboard** để xem thống kê. Dashboard tự cập nhật khi có hóa đơn mới.

Nhập từng hóa đơn một. Muốn nhập ảnh khác, chọn ảnh mới và bấm trích xuất lại.

---

## 8. Dữ liệu được lưu ở đâu

- Lịch sử chi tiêu nằm trong `data/database.csv`, được tạo tự động ở lần chạy đầu tiên.
- Dữ liệu nằm trên máy bạn và không được gửi đi đâu, ngoài ảnh được gửi đến API Gemini để trích xuất.
- Đóng trình duyệt không làm mất dữ liệu đã xác nhận. Thay đổi chưa bấm xác nhận sẽ mất khi làm mới trang.
- Để sao lưu, sao chép file `data/database.csv` ra nơi khác. Để bắt đầu lại từ đầu, xóa file này, lần chạy sau sẽ tạo sổ trắng.

Có thể mở `database.csv` bằng Excel để xem. Đóng Excel trước khi lưu trong ứng dụng, vì Windows khóa file đang mở.

---

## 9. Đánh giá độ chính xác (tùy chọn)

Dự án có script so sánh AI với phương pháp truyền thống (Tesseract + regex) trên bộ ảnh đánh giá. Để chạy, cần:

1. Cài Tesseract OCR, chọn gói ngôn ngữ tiếng Việt khi cài.
2. Đặt ảnh đánh giá vào `assets/test_images/` và tạo file nhãn `labels.json` cùng thư mục.
3. Chạy:

```bash
python evaluate.py
```

Kết quả nằm trong thư mục `results/`. Thư mục này và bộ ảnh đánh giá không được đưa lên GitHub.

---

## 10. Xử lý lỗi thường gặp

| Triệu chứng | Nguyên nhân | Cách sửa |
| :--- | :--- | :--- |
| `No module named 'streamlit'` | Cài thư viện vào Python chung, hoặc chưa kích hoạt `.venv` | Dùng `.venv\Scripts\python.exe -m pip install -r requirements.txt` rồi chạy app bằng `.venv\Scripts\python.exe -m streamlit run app.py` |
| `Chưa có GEMINI_API_KEY` | Thiếu file `.env` hoặc sai nội dung | Kiểm tra file `.env` nằm ở thư mục gốc, đúng định dạng ở bước 5 |
| Báo lỗi `429` hoặc `quota` | Hết lượt gọi miễn phí | Chờ vài phút rồi thử lại |
| Báo `JSON không hợp lệ` | AI trả về sai định dạng | Thử lại với ảnh rõ hơn, hoặc sửa tay trong bảng |
| `PermissionError` khi lưu | `database.csv` đang mở trong Excel | Đóng Excel rồi bấm lưu lại |
| Trang trắng hoặc không mở được | Cổng 8501 đang bị chiếm | Chạy `python -m streamlit run app.py --server.port 8502` |
| Tiếng Việt bị lỗi trong Excel | Mở file bằng mã hóa sai | Mở bằng Excel qua chức năng **Data > From Text/CSV**, chọn UTF-8 |
| `ModuleNotFoundError: No module named 'utils'` | Chạy lệnh từ sai thư mục | Đứng ở thư mục gốc `AI-Expense-Parser-Tracker` rồi chạy lại |

---

## Cấu trúc dự án

```
AI-Expense-Parser-Tracker/
├── app.py                 # Trang chính: nhập và kiểm tra hóa đơn
├── pages/
│   └── 1_Dashboard.py     # Trang thống kê chi tiêu
├── utils/
│   ├── ai_core.py         # Gọi Gemini, trả về dữ liệu hóa đơn dạng dict
│   ├── data_core.py       # Đọc và ghi sổ chi tiêu (CSV)
│   └── baseline_ocr.py    # Phương pháp đối chứng: Tesseract + regex
├── evaluate.py            # Đánh giá độ chính xác trên bộ ảnh
├── assets/                # Ảnh mẫu và bộ ảnh đánh giá
├── data/                  # Sổ chi tiêu (tự tạo, không đưa lên GitHub)
├── .env.example           # Mẫu cấu hình khóa API
├── requirements.txt       # Danh sách thư viện
└── README.md
```

---

## Lưu ý bảo mật

- Không đưa file `.env`, thư mục `data/` và `results/` lên GitHub. Các mục này đã được liệt kê trong `.gitignore`.
- Trước khi chụp màn hình hoặc quay demo, che các thông tin cá nhân trên hóa đơn như số điện thoại, số thẻ, địa chỉ.
- Nếu khóa API bị lộ, vào Google AI Studio để xóa khóa cũ và tạo khóa mới.

---

## Giấy phép và thông tin nhóm

Dự án phục vụ mục đích học tập trong học phần Trí tuệ nhân tạo.
