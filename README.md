# Bộ công cụ QR Code và tra cứu danh sách

Ứng dụng web xây dựng bằng Python và Streamlit, gồm hai công cụ:

1. **Tạo mã QR** từ đường dẫn URL hoặc văn bản bất kỳ, tùy chỉnh giao diện và tải về dưới dạng ảnh PNG.
2. **Lọc trùng và tra cứu** danh sách học viên: dán danh sách số CMND/CCCD và họ tên từ Excel, đối chiếu với file danh sách để lấy giáo viên hồ sơ, rồi xuất kết quả ra file Excel.

## Mục lục

- [Tính năng](#tính-năng)
- [Bảo mật dữ liệu](#bảo-mật-dữ-liệu)
- [Công nghệ sử dụng](#công-nghệ-sử-dụng)
- [Cấu trúc dự án](#cấu-trúc-dự-án)
- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Cài đặt và chạy cục bộ](#cài-đặt-và-chạy-cục-bộ)
- [Hướng dẫn sử dụng](#hướng-dẫn-sử-dụng)
- [Triển khai lên Streamlit Community Cloud](#triển-khai-lên-streamlit-community-cloud)
- [Cấu hình](#cấu-hình)
- [Xử lý sự cố](#xử-lý-sự-cố)
- [Định hướng phát triển](#định-hướng-phát-triển)
- [Giấy phép](#giấy-phép)

## Tính năng

### Công cụ tạo mã QR

- Tạo mã QR từ URL hoặc văn bản bất kỳ (hỗ trợ tiếng Việt có dấu và nhiều dòng), xem trước theo thời gian thực.
- Hiển thị số ký tự của nội dung và báo lỗi rõ ràng khi nội dung quá dài so với dung lượng tối đa của mã QR.
- Tùy chỉnh màu mã QR, màu nền và độ phân giải ảnh tải về.
- Chọn mức sửa lỗi (7%, 15%, 25%, 30%).
- Tùy chọn thêm ảnh chìm phía sau mã QR (PNG, JPG, WEBP) và điều chỉnh độ đậm. Bỏ trống thì mã QR vẫn được tạo bình thường.
- Cảnh báo khi độ tương phản giữa màu mã QR và màu nền quá thấp, dễ gây khó quét.
- Tải mã QR về dưới dạng ảnh PNG.

### Công cụ lọc trùng và tra cứu

- Dán trực tiếp hai cột (số CMND/CCCD, họ tên học viên) từ Excel.
- Tải lên file Excel danh sách học viên (.xlsx) làm nguồn tra cứu.
- Tự động nhận diện cột theo tiêu đề `SỐ CMND/CCCD`, `HỌ TÊN HỌC VIÊN`, `GIÁO VIÊN HỒ SƠ`, có thể chọn lại cột và trang tính thủ công.
- Lọc dòng trùng theo số CMND/CCCD, giữ dòng xuất hiện đầu tiên.
- Đối chiếu theo số CMND/CCCD, vẫn khớp khi Excel làm mất số 0 ở đầu.
- Cảnh báo các dòng không tìm thấy và các dòng khớp CCCD nhưng khác họ tên.
- Xuất file Excel gồm 3 cột: số CMND/CCCD, họ tên học viên, giáo viên hồ sơ. Các ô giáo viên để trống được tô màu vàng.

## Bảo mật dữ liệu

File danh sách học viên chứa thông tin cá nhân (số CMND/CCCD, địa chỉ, số điện thoại).

- Chỉ tải file lên qua giao diện ứng dụng khi sử dụng, **không đưa file Excel vào repository GitHub**.
- File `.gitignore` đã chặn `*.xlsx`, `*.xls` và `*.csv` để tránh commit nhầm.
- Ứng dụng triển khai trên Streamlit Community Cloud mặc định có thể được truy cập bởi bất kỳ ai có đường dẫn. Nếu dùng với dữ liệu thật, hãy giới hạn người xem trong phần **Settings, Sharing** của ứng dụng.

## Công nghệ sử dụng

| Thành phần         | Mục đích                       |
| ------------------ | ------------------------------ |
| Python 3.9 trở lên | Ngôn ngữ lập trình             |
| Streamlit          | Xây dựng giao diện web         |
| qrcode             | Sinh mã QR                     |
| Pillow             | Xử lý và xuất ảnh              |
| pandas             | Đọc và đối chiếu dữ liệu Excel |
| openpyxl           | Đọc và ghi file Excel (.xlsx)  |

## Cấu trúc dự án

```
qr-generator/
├── .streamlit/
│   └── config.toml      # Cấu hình giao diện (theme)
├── .gitignore           # Danh sách file/thư mục bị Git bỏ qua
├── app.py               # Mã nguồn chính (công cụ tạo QR và tra cứu danh sách)
├── requirements.txt     # Danh sách thư viện phụ thuộc
└── README.md            # Tài liệu dự án
```

## Yêu cầu hệ thống

- Python 3.9 trở lên
- Git
- Trình duyệt web hiện đại (Chrome, Edge, Firefox, Safari)

## Cài đặt và chạy cục bộ

### 1. Clone repository

```bash
git clone https://github.com/LTDat11/qr-generator.git
cd qr-generator
```

### 2. Tạo môi trường ảo

```bash
python -m venv .venv
```

Kích hoạt môi trường ảo:

```bash
# Windows (CMD)
.venv\Scripts\activate.bat

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

### 3. Cài đặt thư viện

```bash
pip install -r requirements.txt
```

### 4. Chạy ứng dụng

```bash
streamlit run app.py
```

Ứng dụng mặc định chạy tại `http://localhost:8501`.

## Hướng dẫn sử dụng

### Tab Tạo mã QR

1. Nhập nội dung vào ô **Nội dung**: một đường dẫn như `https://example.com` hoặc một đoạn văn bản bất kỳ.
2. Mã QR xuất hiện ở khung **Xem trước** bên phải.
3. (Tùy chọn) Mở mục **Tùy chỉnh giao diện** để đổi màu, độ phân giải, mức sửa lỗi hoặc tải lên ảnh chìm.
4. Bấm **Tải về PNG** để lưu mã QR.

Lưu ý: nếu nhập đường dẫn, hãy ghi đầy đủ giao thức (`https://`) để điện thoại nhận diện đó là liên kết và mở được trực tiếp. Nội dung càng dài thì mã QR càng dày đặc và khó quét, nên giữ văn bản ngắn gọn khi có thể.

Khuyến nghị: dùng màu mã QR tối trên nền sáng và chọn mức sửa lỗi từ Trung bình trở lên để mã dễ quét trên mọi thiết bị.

Khi dùng ảnh chìm, nên chọn mức sửa lỗi Khá cao hoặc Cao, giữ độ đậm ảnh ở mức 30% trở xuống và ưu tiên ảnh sáng, ít chi tiết. Luôn quét thử bằng điện thoại trước khi sử dụng.

### Tab Lọc trùng và tra cứu

1. Ở mục **File danh sách học viên**, tải lên file Excel (.xlsx) chứa các cột `SỐ CMND/CCCD`, `HỌ TÊN HỌC VIÊN`, `GIÁO VIÊN HỒ SƠ`.
2. Ở mục **Dữ liệu cần tra cứu**, dán hai cột đã copy từ Excel (số CMND/CCCD và họ tên), mỗi học viên một dòng. Có thể dán kèm dòng tiêu đề, ứng dụng sẽ tự bỏ qua.
3. Xem bảng kết quả và các thống kê: số dòng đã dán, số dòng trùng đã loại, số dòng tìm thấy và không tìm thấy.
4. Bấm **Tải về Excel** để lấy file kết quả.

Nếu tiêu đề cột trong file khác với tên mặc định, mở mục **Tùy chọn nguồn dữ liệu** để chọn lại trang tính và các cột tương ứng.

Ví dụ dữ liệu dán vào (cách nhau bằng phím Tab khi copy từ Excel):

```
075304020310	BÙI TÚ AN
086193007793	BÙI TRẦN PHƯƠNG ANH
```

## Triển khai lên Streamlit Community Cloud

### 1. Đẩy mã nguồn lên GitHub

Đảm bảo file `.gitignore` đã tồn tại trước khi chạy `git add .` để không đưa thư mục `.venv` lên repository.

```bash
git add .
git commit -m "Update project"
git push origin main
```

### 2. Tạo ứng dụng trên Streamlit

1. Truy cập [share.streamlit.io](https://share.streamlit.io) và đăng nhập bằng tài khoản GitHub.
2. Chọn **Create app**, sau đó chọn **Deploy a public app from GitHub**.
3. Chọn repository `qr-generator`, nhánh `main`, file chính `app.py`.
4. Bấm **Deploy** và chờ quá trình cài đặt hoàn tất.

### 3. Cập nhật sau khi triển khai

Mỗi lần push code mới lên nhánh `main`, Streamlit Community Cloud sẽ tự động triển khai lại.

## Cấu hình

Giao diện được cấu hình trong `.streamlit/config.toml`:

| Khóa                             | Giá trị mặc định | Mô tả                                |
| -------------------------------- | ---------------- | ------------------------------------ |
| `theme.base`                     | `light`          | Chế độ sáng hoặc tối                 |
| `theme.primaryColor`             | `#2563EB`        | Màu nhấn của nút và thành phần chính |
| `theme.backgroundColor`          | `#F8FAFC`        | Màu nền trang                        |
| `theme.secondaryBackgroundColor` | `#FFFFFF`        | Màu nền các khung nội dung           |
| `theme.textColor`                | `#0F172A`        | Màu chữ                              |

Các thông số của mã QR (viền, mức sửa lỗi mặc định) nằm trong hàm `build_qr_png` của `app.py`.

## Xử lý sự cố

| Vấn đề                           | Nguyên nhân thường gặp                               | Cách xử lý                                                              |
| -------------------------------- | ---------------------------------------------------- | ----------------------------------------------------------------------- |
| `streamlit: command not found`   | Chưa kích hoạt môi trường ảo                         | Kích hoạt `.venv` rồi chạy lại                                          |
| `ModuleNotFoundError: qrcode`    | Chưa cài thư viện                                    | Chạy `pip install -r requirements.txt`                                  |
| Deploy lỗi trên Streamlit Cloud  | Thiếu thư viện trong `requirements.txt`              | Mở **Manage app**, xem log và bổ sung thư viện                          |
| Báo không đọc được file Excel    | File sai định dạng hoặc đang bị khóa                 | Lưu lại dưới dạng `.xlsx` rồi tải lên lại                               |
| Dòng nào cũng báo không tìm thấy | Chọn sai cột số CMND/CCCD                            | Mở **Tùy chọn nguồn dữ liệu** và chọn lại cột                           |
| Repository nặng bất thường       | Thư mục `.venv` bị đưa lên Git                       | Thêm `.venv/` vào `.gitignore`, chạy `git rm -r --cached .venv`         |
| Điện thoại không quét được mã    | Độ tương phản thấp, mã quá nhỏ hoặc ảnh chìm quá đậm | Dùng màu tối trên nền sáng, tăng độ phân giải ảnh, giảm độ đậm ảnh chìm |

## Định hướng phát triển

- Chèn logo vào giữa mã QR.
- Xuất ảnh định dạng SVG.
- Tạo hàng loạt mã QR từ danh sách URL.
- Hỗ trợ các mẫu dữ liệu có cấu trúc như Wi-Fi, vCard, email.
- Cho phép chọn thêm các cột khác của file danh sách để xuất ra kết quả.
- Đối chiếu theo họ tên khi dữ liệu dán vào không có số CMND/CCCD.

## Giấy phép

Dự án được phát hành theo giấy phép MIT. Xem file `LICENSE` để biết thêm chi tiết.
