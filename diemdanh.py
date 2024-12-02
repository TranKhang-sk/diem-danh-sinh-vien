from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import QTimer, QDateTime, Qt, pyqtSignal
from PyQt6 import uic
from database import Database
import cv2
import numpy as np
from datetime import datetime
import json

class DiemDanhWindow(QMainWindow):
    attendance_updated = pyqtSignal(str)
    history_updated = pyqtSignal(str)  # Thêm signal để kết nối với lịch sử điểm danh
    
    def __init__(self):
        super().__init__()
        uic.loadUi("diemdanh.ui", self)
        self.db = Database()
        
        # Khởi tạo các biến
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.student_recognized = False
        
        # Load student mapping
        try:
            with open('student_mapping.json', 'r') as f:
                # Chuyển key từ string sang int
                mapping_data = json.load(f)
                self.student_mapping = {int(v): k for k, v in mapping_data.items()}
            print("Đã load student mapping:")
            print(self.student_mapping)
        except Exception as e:
            print(f"Lỗi load student mapping: {e}")
            self.student_mapping = {}
        
        # Khởi tạo face detector
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        # Khởi tạo LBPH recognizer
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        
        try:
            # Load pretrained model
            self.recognizer.read('face_model.yml')
            print("Đã load model nhận diện thành công!")
        except Exception as e:
            print(f"Lỗi load model: {e}")
        
        # Setup UI và kết nối
        self.setup_connections()
        self.setup_ui()

    def setup_connections(self):
        self.btnMoCamera.clicked.connect(self.start_camera)
        self.btnDongCamera.clicked.connect(self.stop_camera)
        self.btnDD.clicked.connect(self.mark_attendance)

    def setup_ui(self):
        self.btnDD.setEnabled(False)
        self.txtNgayHienTai.setText(QDateTime.currentDateTime().toString('dd/MM/yyyy'))

    def start_camera(self):
        """Bắt đầu camera"""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            QMessageBox.warning(self, "Lỗi", "Không thể mở camera!")
            return
            
        self.timer.start(80)
        self.btnMoCamera.setEnabled(False)
        self.btnDongCamera.setEnabled(True)
        self.btnDD.setEnabled(False)

    def stop_camera(self):
        """Dừng camera"""
        if self.cap is not None:
            self.timer.stop()
            self.cap.release()
            self.cap = None
            self.image_label.clear()
            self.btnMoCamera.setEnabled(True)
            self.btnDongCamera.setEnabled(False)
            self.btnDD.setEnabled(False)

    def recognize_face(self, frame):
        """Nhận diện khuôn mặt trong frame"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            for (x, y, w, h) in faces:
                # Vẽ khung xanh cho khuôn mặt phát hiện được
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # Cắt vùng khuôn mặt
                face_roi = gray[y:y+h, x:x+w]
                face_roi = cv2.resize(face_roi, (100, 100))
                
                try:
                    # Nhận diện khuôn mặt
                    label, confidence = self.recognizer.predict(face_roi)
                    print(f"Label: {label}, Confidence: {confidence}")
                    
                    if confidence < 85:  # Ngưỡng tin cậy
                        # Lấy mã sinh viên từ mapping
                        if label in self.student_mapping:
                            ma_sv = self.student_mapping[label]
                            print(f"Mã sinh viên nhận diện được: {ma_sv}")
                            
                            # Kiểm tra trong database
                            query = "SELECT COUNT(*) as count FROM sinh_vien WHERE ma_sv = %s"
                            result = self.db.fetch_data(query, (ma_sv,))
                            
                            if result and result[0]['count'] > 0:
                                self.display_student_info(ma_sv)
                                self.student_recognized = True
                                self.btnDD.setEnabled(True)
                                
                                # Vẽ khung đỏ cho khuôn mặt nhận diện thành công
                                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                                return
                            else:
                                print(f"Không tìm thấy sinh viên với mã {ma_sv} trong database")
                        else:
                            print(f"Không tìm thấy mapping cho label {label}")
                            print("Current mapping:", self.student_mapping)
                
                except Exception as e:
                    print(f"Lỗi nhận diện: {e}")
            
            # Nếu không nhận diện được
            self.student_recognized = False
            self.btnDD.setEnabled(False)

        except Exception as e:
            print(f"Lỗi phát hiện khuôn mặt: {e}")

    def display_student_info(self, ma_sv):
        """Hiển thị thông tin sinh viên"""
        query = "SELECT * FROM sinh_vien WHERE ma_sv = %s"
        result = self.db.fetch_data(query, (ma_sv,))
        
        if result:
            student = result[0]
            self.current_student = student
            
            # Hiển thị thông tin cơ bản
            self.lblMaSinhVien.setText(student['ma_sv'])
            self.lblTenSinhVien.setText(student['ho_ten'])
            self.lblGioiTinh.setText(student['gioi_tinh'])
            
            # Hiển thị ảnh đại diện
            if student['anh_dai_dien']:
                pixmap = QPixmap()
                pixmap.loadFromData(student['anh_dai_dien'])
                scaled_pixmap = pixmap.scaled(
                    self.lblAvatar.width(),
                    self.lblAvatar.height(),
                    Qt.AspectRatioMode.KeepAspectRatio
                )
                self.lblAvatar.setPixmap(scaled_pixmap)
            
            # Đặt trạng thái mặc định là "Chưa điểm danh"
            self.check_attendance_status(ma_sv)

    def update_frame(self):
        """Cập nhật frame từ camera"""
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Nhận diện khuôn mặt
                self.recognize_face(frame)
                
                # Hiển thị frame
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_frame.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                self.image_label.setPixmap(QPixmap.fromImage(qt_image))
            else:
                self.timer.stop()
        else:
            self.timer.stop()

    def check_attendance_status(self, ma_sv):
        """Kiểm tra trạng thái điểm danh"""
        query = """
            SELECT COUNT(*) as count FROM diem_danh 
            WHERE ma_sv = %s 
            AND DATE(ngay_diem_danh) = CURDATE()
        """
        result = self.db.fetch_data(query, (ma_sv,))
        
        if result and result[0]['count'] > 0:
            self.lblTrangThai.setText(f"Đã điểm danh {result[0]['count']} lần")
        else:
            self.lblTrangThai.setText("Chưa điểm danh")
        
        # Luôn cho phép điểm danh
        self.btnDD.setEnabled(True)

    def mark_attendance(self):
        """Thực hiện điểm danh"""
        if not self.student_recognized:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhận diện sinh viên trước!")
            return

        # Lấy thời gian hiện tại
        now = datetime.now()
        current_date = now.strftime("%A, %d %B %Y")
        current_time = now.strftime("%H:%M:%S")
        
        # Đếm số lần điểm danh trong ngày
        query = """
            SELECT COUNT(*) as count FROM diem_danh 
            WHERE ma_sv = %s 
            AND DATE(ngay_diem_danh) = CURDATE()
        """
        result = self.db.fetch_data(query, (self.current_student['ma_sv'],))
        attendance_count = result[0]['count'] + 1 if result else 1
        
        # Cập nhật UI
        self.txtNgayHienTai.setText(current_date)
        self.lblNgayDiemDanh.setText(current_date)
        self.lblThoiGian.setText(current_time)
        self.lblTrangThai.setText(f"Đã điểm danh {attendance_count} lần")
        
        # Lưu vào database
        query = """
            INSERT INTO diem_danh (ma_sv, ngay_diem_danh, thoi_gian, trang_thai)
            VALUES (%s, %s, %s, %s)
        """
        params = (
            self.current_student['ma_sv'],
            now.date(),
            now.time(),
            "Có mặt"
        )

        if self.db.execute_query(query, params):
            QMessageBox.information(
                self,
                "Điểm danh thành công",
                f"""
Sinh viên: {self.current_student['ho_ten']}
Mã số: {self.current_student['ma_sv']}
Ngày: {now.strftime('%d/%m/%Y')}
Thời gian: {now.strftime('%H:%M:%S')}
Lần điểm danh thứ: {attendance_count}
                """.strip()
            )
            
            # Phát signal để cập nhật lịch sử điểm danh
            self.attendance_updated.emit(self.current_student['ma_sv'])

    def closeEvent(self, event):
        self.stop_camera()
        event.accept()
