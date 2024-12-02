# Hệ Thống Điểm Danh Sinh Viên Sử Dụng Nhận Diện Khuôn Mặt AI

Hệ thống quản lý điểm danh sinh viên hiện đại sử dụng công nghệ nhận diện khuôn mặt AI để tự động hóa quá trình điểm danh trong các cơ sở giáo dục.

## Tính Năng

- **Điểm Danh Bằng Nhận Diện Khuôn Mặt**: Tự động phát hiện và nhận diện khuôn mặt sinh viên để điểm danh
- **Xử Lý Thời Gian Thực**: Xử lý điểm danh theo thời gian thực sử dụng computer vision
- **Giao Diện Thân Thiện**: Giao diện đồ họa đơn giản và dễ sử dụng được xây dựng bằng PyQt6
- **Tích Hợp Cơ Sở Dữ Liệu**: Lưu trữ và quản lý dữ liệu điểm danh hiệu quả
- **Chức Năng Xuất Dữ Liệu**: Xuất dữ liệu điểm danh ra định dạng Excel
- **Quản Lý Sinh Viên**: Thêm và quản lý thông tin sinh viên kèm ảnh

## Yêu Cầu Hệ Thống

- Python 3.8 trở lên
- OpenCV
- PyQt5
- face_recognition
- pandas
- numpy
- openpyxl

## Hướng Dẫn Cài Đặt

1. Tải mã nguồn về máy:
```bash
git clone https://github.com/yourusername/student-attendance-system.git
cd student-attendance-system
```

2. Cài đặt các gói thư viện cần thiết:
```bash
pip install -r requirements.txt
```

## Cách Sử Dụng

1. Chạy ứng dụng chính:
```bash
python main.py
```

2. Hệ thống cung cấp các chức năng chính sau:
   - Thêm sinh viên mới kèm ảnh
   - Điểm danh bằng webcam
   - Xem danh sách điểm danh
   - Xuất dữ liệu điểm danh ra Excel

## Cấu Trúc Dự Án

```
├── main.py              # File chương trình chính
├── database/            # Thư mục chứa cơ sở dữ liệu
├── student_images/      # Thư mục chứa ảnh sinh viên
├── attendance_records/  # Thư mục chứa bản ghi điểm danh
└── requirements.txt     # File chứa các thư viện cần thiết
```
