from PyQt6.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QTableWidgetItem
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6 import uic
from database import Database
from face_detector import FaceDetector
import cv2
import os
import numpy as np

class SinhVienWindow(QMainWindow):
    # Thêm signal cho việc xóa sinh viên
    student_deleted = pyqtSignal(str)  # Signal phát ra mã sinh viên bị xóa
    
    def __init__(self):
        super().__init__()
        uic.loadUi("sinhvien.ui", self)
        self.db = Database()
        self.face_detector = FaceDetector()
        self.selected_image = None
        
        # Thêm các biến cho camera
        self.camera_running = False
        self.captured_images = []
        self.image_count = 0
        self.face_quality_threshold = 80  # Ngưỡng chất lượng khuôn mặt
        self.face_size_min = 150  # Kích thước tối thiểu của khuôn mặt
        self.current_quality = 0  # Chất lượng khuôn mặt hiện tại
        
        self.setup_connections()
        self.load_data()

    def setup_connections(self):
        self.btnChonAnh.clicked.connect(self.choose_image)
        self.btnMoCamera.clicked.connect(self.open_camera)
        self.btnThem.clicked.connect(self.add_student)
        self.btnSua.clicked.connect(self.edit_student)
        self.btnXoa.clicked.connect(self.delete_student)
        self.btnLamMoi.clicked.connect(self.load_data)
        self.btnTimKiem.clicked.connect(self.search_student)
        self.tblSinhVien.itemClicked.connect(self.load_student_data)

    def choose_image(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Chọn ảnh", "", "Image Files (*.png *.jpg *.jpeg)"
        )
        if file_name:
            self.selected_image = file_name
            pixmap = QPixmap(file_name)
            scaled_pixmap = pixmap.scaled(
                self.lblAvatar.width(),
                self.lblAvatar.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.lblAvatar.setPixmap(scaled_pixmap)

    def open_camera(self):
        """Bắt đầu camera và thu thập ảnh khuôn mặt"""
        # Khởi tạo camera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            QMessageBox.warning(self, "Lỗi", "Không thể mở camera!")
            return

        self.camera_running = True
        self.captured_images = []
        self.image_count = 0
        self.current_quality = 0

        # Timer để cập nhật frame và tự động chụp
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        QMessageBox.information(
            self, 
            "Hướng dẫn chụp ảnh", 
            "Hướng dẫn chụp ảnh khuôn mặt:\n\n" +
            "1. Đảm bảo khuôn mặt nằm trong khung trắng\n" +
            "2. Nhìn thẳng vào camera\n" +
            "3. Đảm bảo ánh sáng đầy đủ\n" +
            "4. Giữ khuôn mặt ổn định\n" +
            "5. Hệ thống sẽ tự động chụp khi khuôn mặt đạt chất lượng tốt\n\n" +
            "Hệ thống sẽ tự động chụp 5 ảnh chất lượng tốt nhất."
        )

    def check_face_quality(self, face_img):
        """Kiểm tra chất lượng khuôn mặt"""
        if face_img is None or face_img.size == 0:
            return 0
        
        # Kiểm tra kích thước
        h, w = face_img.shape[:2]
        if h < self.face_size_min or w < self.face_size_min:
            return 50
        
        # Kiểm tra độ tương phản
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        contrast = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Kiểm tra độ sáng
        brightness = np.mean(gray)
        
        # Tính điểm chất lượng (0-100)
        quality_score = min(100, (contrast * 0.5 + (brightness/255.0) * 50))
        
        return quality_score

    def update_frame(self):
        """Cập nhật frame từ camera và tự động chụp khi đạt chất lượng"""
        if hasattr(self, 'cap') and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Phát hiện khuôn mặt
                faces = self.face_detector.detect_faces(frame)
                
                # Vẽ hướng dẫn căn chỉnh
                h, w = frame.shape[:2]
                center_x, center_y = w//2, h//2
                target_size = min(w, h) // 3
                cv2.rectangle(frame, 
                            (center_x - target_size//2, center_y - target_size//2),
                            (center_x + target_size//2, center_y + target_size//2),
                            (255, 255, 255), 2)
                
                if len(faces) == 1:
                    x, y, w, h = faces[0]
                    face_img = frame[y:y+h, x:x+w]
                    quality = self.check_face_quality(face_img)
                    self.current_quality = quality
                    
                    # Vẽ khung xung quanh khuôn mặt (xanh nếu chất lượng tốt, đỏ nếu kém)
                    color = (0, 255, 0) if quality >= self.face_quality_threshold else (0, 0, 255)
                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                    
                    # Hiển thị chỉ số chất lượng
                    cv2.putText(frame, f"Quality: {quality:.0f}%", 
                              (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                    
                    # Tự động chụp khi đạt chất lượng
                    if quality >= self.face_quality_threshold and self.image_count < 5:
                        self.captured_images.append(face_img)
                        self.image_count += 1
                        QMessageBox.information(self, "Chụp ảnh thành công", 
                            f"Đã chụp ảnh {self.image_count}/5\n" +
                            f"Chất lượng ảnh: {quality:.0f}%")
                        
                        if self.image_count >= 5:
                            self.stop_camera()
                            QMessageBox.information(self, "Hoàn thành", 
                                "Đã thu thập đủ 5 ảnh chất lượng tốt!\n" +
                                "Vui lòng điền thông tin và nhấn nút Thêm để lưu.")
                            return
                            
                elif len(faces) > 1:
                    # Cảnh báo nhiều khuôn mặt
                    cv2.putText(frame, "WARNING: Multiple faces detected!", 
                              (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Hiển thị hướng dẫn
                cv2.putText(frame, "Align face within the white box", 
                          (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(frame, f"Images: {self.image_count}/5", 
                          (10, h-20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Chuyển đổi frame để hiển thị
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                    self.lblFace.width(), 
                    self.lblFace.height(),
                    Qt.AspectRatioMode.KeepAspectRatio
                )
                self.lblFace.setPixmap(scaled_pixmap)

    def load_data(self):
        # Xóa dữ liệu cũ
        self.tblSinhVien.setRowCount(0)
        
        # Lấy dữ liệu từ database
        query = "SELECT ma_sv, ho_ten, lop, gioi_tinh FROM sinh_vien"
        students = self.db.fetch_data(query)
        
        if students:
            for row, student in enumerate(students):
                self.tblSinhVien.insertRow(row)
                self.tblSinhVien.setItem(row, 0, QTableWidgetItem(student['ma_sv']))
                self.tblSinhVien.setItem(row, 1, QTableWidgetItem(student['ho_ten']))
                self.tblSinhVien.setItem(row, 2, QTableWidgetItem(student['lop']))
                self.tblSinhVien.setItem(row, 3, QTableWidgetItem(student['gioi_tinh']))

    def add_student(self):
        """Thêm sinh viên mới với đầy đủ thông tin và ảnh"""
        # 1. Kiểm tra thông tin cơ bản
        ma_sv = self.txtMaSinhVien.text()
        ten_sv = self.txtTenSinhVien.text()
        gioi_tinh = self.cbGioiTinh.currentText()
        lop = self.txtLop.text()

        if not all([ma_sv, ten_sv, lop]):
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng điền đầy đủ thông tin!")
            return

        # 2. Kiểm tra mã sinh viên đã tồn tại
        check_query = "SELECT ma_sv FROM sinh_vien WHERE ma_sv = %s"
        if self.db.fetch_data(check_query, (ma_sv,)):
            QMessageBox.warning(self, "Cảnh báo", "Mã sinh viên đã tồn tại!")
            return

        # 3. Kiểm tra ảnh đại diện
        if not self.selected_image or not os.path.exists(self.selected_image):
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn ảnh đại diện!")
            return

        # 4. Kiểm tra đã có đủ 5 ảnh khuôn mặt chưa
        if len(self.captured_images) != 5:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chụp đủ 5 ảnh khuôn mặt trước khi thêm!")
            return

        try:
            # 5. Đọc ảnh đại diện
            with open(self.selected_image, 'rb') as file:
                avatar_data = file.read()

            # 6. Chuẩn bị các ảnh khuôn mặt
            face_images = []
            for face_img in self.captured_images:
                resized_img = cv2.resize(face_img, (224, 224))
                _, img_encoded = cv2.imencode('.jpg', resized_img)
                face_images.append(img_encoded.tobytes())

            # 7. Thêm sinh viên với đầy đủ thông tin
            query = """
                INSERT INTO sinh_vien (
                    ma_sv, ho_ten, gioi_tinh, lop, anh_dai_dien,
                    anh_khuon_mat_1, anh_khuon_mat_2, anh_khuon_mat_3, anh_khuon_mat_4, anh_khuon_mat_5
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (ma_sv, ten_sv, gioi_tinh, lop, avatar_data) + tuple(face_images)
            
            if self.db.execute_query(query, params):
                # 8. Thêm sinh viên mới vào bảng
                row = self.tblSinhVien.rowCount()
                self.tblSinhVien.insertRow(row)
                self.tblSinhVien.setItem(row, 0, QTableWidgetItem(ma_sv))
                self.tblSinhVien.setItem(row, 1, QTableWidgetItem(ten_sv))
                self.tblSinhVien.setItem(row, 2, QTableWidgetItem(lop))
                self.tblSinhVien.setItem(row, 3, QTableWidgetItem(gioi_tinh))

                # 9. Chọn dòng vừa thêm
                self.tblSinhVien.selectRow(row)

                QMessageBox.information(self, "Thông báo", "Thêm sinh viên thành công!")
                
                # 10. Xóa form và reset các biến
                self.clear_form()
                self.captured_images.clear()
                self.image_count = 0
                self.lblFace.clear()
            else:
                QMessageBox.warning(self, "Lỗi", "Không thể thêm sinh viên!")

        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể thêm sinh viên: {str(e)}")

    def edit_student(self):
        current_row = self.tblSinhVien.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn sinh viên cần sửa!")
            return

        ma_sv = self.txtMaSinhVien.text()
        ten_sv = self.txtTenSinhVien.text()
        gioi_tinh = self.cbGioiTinh.currentText()
        lop = self.txtLop.text()

        # Đọc ảnh đại diện mới nếu có
        avatar_data = None
        if self.selected_image and os.path.exists(self.selected_image):
            with open(self.selected_image, 'rb') as file:
                avatar_data = file.read()

        # Cập nhật thông tin sinh viên
        if avatar_data:
            query = """
                UPDATE sinh_vien 
                SET ho_ten = %s, gioi_tinh = %s, lop = %s, anh_dai_dien = %s
                WHERE ma_sv = %s
            """
            params = (ten_sv, gioi_tinh, lop, avatar_data, ma_sv)
        else:
            query = """
                UPDATE sinh_vien 
                SET ho_ten = %s, gioi_tinh = %s, lop = %s
                WHERE ma_sv = %s
            """
            params = (ten_sv, gioi_tinh, lop, ma_sv)

        if self.db.execute_query(query, params):
            QMessageBox.information(self, "Thông báo", "Cập nhật thông tin thành công!")
            self.load_data()
        else:
            QMessageBox.warning(self, "Lỗi", "Không thể cập nhật thông tin!")

    def delete_student(self):
        current_row = self.tblSinhVien.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn sinh viên cần xóa!")
            return

        ma_sv = self.tblSinhVien.item(current_row, 0).text()
        reply = QMessageBox.question(self, "Xác nhận", 
                                   "Bạn có chắc muốn xóa sinh viên này?\nMọi dữ liệu điểm danh của sinh viên cũng sẽ bị xóa!",
                                   QMessageBox.StandardButton.Yes | 
                                   QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Xóa dữ liệu điểm danh trước
                delete_attendance = "DELETE FROM diem_danh WHERE ma_sv = %s"
                self.db.execute_query(delete_attendance, (ma_sv,))
                
                # Sau đó xóa sinh viên
                delete_student = "DELETE FROM sinh_vien WHERE ma_sv = %s"
                if self.db.execute_query(delete_student, (ma_sv,)):
                    # Phát signal với mã sinh viên bị xóa
                    self.student_deleted.emit(ma_sv)
                    QMessageBox.information(self, "Thông báo", "Xóa sinh viên thành công!")
                    self.load_data()
                    self.clear_form()
                else:
                    QMessageBox.warning(self, "Lỗi", "Không thể xóa sinh viên!")
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", f"Lỗi khi xóa sinh viên: {str(e)}")

    def search_student(self):
        ma_sv = self.txtTimKiem.text()
        if not ma_sv:
            self.load_data()
            return

        query = """
            SELECT ma_sv, ho_ten, lop, gioi_tinh 
            FROM sinh_vien 
            WHERE ma_sv LIKE %s
        """
        students = self.db.fetch_data(query, (f"%{ma_sv}%",))

        self.tblSinhVien.setRowCount(0)
        if students:
            for row, student in enumerate(students):
                self.tblSinhVien.insertRow(row)
                self.tblSinhVien.setItem(row, 0, QTableWidgetItem(student['ma_sv']))
                self.tblSinhVien.setItem(row, 1, QTableWidgetItem(student['ho_ten']))
                self.tblSinhVien.setItem(row, 2, QTableWidgetItem(student['lop']))
                self.tblSinhVien.setItem(row, 3, QTableWidgetItem(student['gioi_tinh']))

    def load_student_data(self, item):
        row = item.row()
        self.txtMaSinhVien.setText(self.tblSinhVien.item(row, 0).text())
        self.txtTenSinhVien.setText(self.tblSinhVien.item(row, 1).text())
        self.txtLop.setText(self.tblSinhVien.item(row, 2).text())
        self.cbGioiTinh.setCurrentText(self.tblSinhVien.item(row, 3).text())

        # Load ảnh đại diện
        query = "SELECT anh_dai_dien FROM sinh_vien WHERE ma_sv = %s"
        result = self.db.fetch_data(query, (self.tblSinhVien.item(row, 0).text(),))
        if result and result[0]['anh_dai_dien']:
            pixmap = QPixmap()
            pixmap.loadFromData(result[0]['anh_dai_dien'])
            scaled_pixmap = pixmap.scaled(
                self.lblAvatar.width(),
                self.lblAvatar.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.lblAvatar.setPixmap(scaled_pixmap)

    def clear_form(self):
        self.txtMaSinhVien.clear()
        self.txtTenSinhVien.clear()
        self.txtLop.clear()
        self.cbGioiTinh.setCurrentIndex(0)
        self.lblAvatar.clear()
        self.selected_image = None

    def stop_camera(self):
        """Dừng camera"""
        if hasattr(self, 'cap'):
            self.cap.release()
        if hasattr(self, 'timer'):
            self.timer.stop()
        self.lblFace.clear()

    def save_face_images(self):
        """Lưu các ảnh khuôn mặt vào database"""
        ma_sv = self.txtMaSinhVien.text()
        if not ma_sv:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn sinh viên trước khi lưu ảnh!")
            return

        if len(self.captured_images) != 5:
            QMessageBox.warning(self, "Lỗi", f"Cần đủ 5 ảnh (hiện có {len(self.captured_images)} ảnh)!")
            return

        try:
            # Chuẩn bị query để cập nhật tất cả ảnh trong một lần
            query = """
                UPDATE sinh_vien 
                SET anh_khuon_mat_1 = %s, anh_khuon_mat_2 = %s, anh_khuon_mat_3 = %s, anh_khuon_mat_4 = %s, anh_khuon_mat_5 = %s
                WHERE ma_sv = %s
            """
            
            # Chuyển đổi tất cả ảnh thành binary
            image_binaries = []
            for face_img in self.captured_images:
                # Resize ảnh về kích thước phù hợp (ví dụ: 224x224)
                resized_img = cv2.resize(face_img, (224, 224))
                # Chuyển ảnh thành binary
                _, img_encoded = cv2.imencode('.jpg', resized_img)
                image_binaries.append(img_encoded.tobytes())
            
            # Thêm mã sinh viên vào cuối danh sách tham số
            params = tuple(image_binaries + [ma_sv])
            
            # Thực hiện cập nhật
            if self.db.execute_query(query, params):
                QMessageBox.information(self, "Thông báo", 
                    "Đã lưu 5 ảnh khuôn mặt thành công!")
                # Xóa danh sách ảnh đã chụp
                self.captured_images.clear()
                self.image_count = 0
                
                # Giữ nguyên dòng được chọn trong bảng
                current_row = self.tblSinhVien.currentRow()
                if current_row >= 0:
                    self.tblSinhVien.selectRow(current_row)
            else:
                QMessageBox.warning(self, "Lỗi", "Không thể lưu ảnh vào CSDL!")

        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không thể lưu ảnh: {str(e)}")
