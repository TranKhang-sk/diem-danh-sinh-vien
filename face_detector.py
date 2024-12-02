import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import cv2
import numpy as np
import os
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap
from database import Database

class FaceDetector(QObject):
    face_detected = pyqtSignal(np.ndarray)
    
    def __init__(self):
        super().__init__()
        # Khởi tạo face cascade
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        # Khởi tạo LBPH recognizer
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.camera = None
        self.timer = None
        
        # Thử load model đã lưu
        try:
            print("Đã load model từ file!".encode('utf-8').decode('utf-8'))
            self.recognizer.read('face_model.yml')
            print("Model loaded successfully!")
        except:
            print("Không tìm thấy model, bắt đầu train mới...".encode('utf-8').decode('utf-8'))
            self.train_model()

    def train_model(self):
        """Train model nhận diện khuôn mặt từ database"""
        try:
            db = Database()
            faces = []
            labels = []
            
            # Lấy dữ liệu từ database
            query = "SELECT ma_sv, anh_khuon_mat_1, anh_khuon_mat_2, anh_khuon_mat_3, anh_khuon_mat_4, anh_khuon_mat_5 FROM sinh_vien"
            students = db.fetch_data(query)
            
            if not students:
                print("Không có dữ liệu sinh viên trong database!")
                return

            for student in students:
                try:
                    # Lấy số từ mã sinh viên (ví dụ: SV54810213 -> 54810213)
                    ma_sv = student['ma_sv']
                    label = int(ma_sv.replace('SV', ''))
                    print(f"Đang xử lý sinh viên: {ma_sv} -> label: {label}")
                    
                    # Xử lý 5 ảnh khuôn mặt của mỗi sinh viên
                    for i in range(1, 6):
                        face_data = student[f'anh_khuon_mat_{i}']
                        if face_data:
                            # Chuyển binary thành numpy array
                            nparr = np.frombuffer(face_data, np.uint8)
                            img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
                            
                            if img is not None and img.size > 0:
                                # Resize về kích thước chuẩn
                                img = cv2.resize(img, (100, 100))
                                faces.append(img)
                                labels.append(label)
                                print(f"Đã thêm ảnh {i} của sinh viên {ma_sv}")
                except Exception as e:
                    print(f"Lỗi xử lý sinh viên {ma_sv}: {str(e)}")
                    continue
            
            if len(faces) > 0 and len(labels) > 0:
                # Chuyển đổi sang numpy array
                faces = np.array(faces)
                labels = np.array(labels, dtype=np.int32)
                
                print("Thông tin training:")
                print(f"Số lượng ảnh: {len(faces)}")
                print(f"Labels: {labels}")
                
                # Train model
                print("Bắt đầu train model...")
                self.recognizer.train(faces, labels)
                print("Train model thành công!")
                
                # Lưu model
                self.recognizer.save('face_model.yml')
                print("Đã lưu model!")
            else:
                print("Không có đủ dữ liệu để train model!")
                
        except Exception as e:
            print(f"Lỗi trong quá trình train model: {str(e)}")

    def detect_faces(self, frame):
        """Phát hiện khuôn mặt trong frame"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        return faces

    def start_camera(self, image_label):
        """Bắt đầu camera"""
        self.camera = cv2.VideoCapture(0)
        self.image_label = image_label
        
        # Tạo timer để cập nhật frame
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        """Cập nhật frame từ camera và nhận diện khuôn mặt"""
        if self.camera is not None and self.camera.isOpened():
            ret, frame = self.camera.read()
            if ret:
                # Phát hiện khuôn mặt
                faces = self.detect_faces(frame)
                
                if len(faces) > 0:
                    for (x, y, w, h) in faces:
                        # Vẽ khung xung quanh khuôn mặt
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        
                        # Cắt và xử lý khuôn mặt
                        face_roi = frame[y:y+h, x:x+w]
                        # Resize khuôn mặt về kích thước chuẩn
                        face_roi = cv2.resize(face_roi, (100, 100))
                        # Gửi khuôn mặt để xử lý
                        self.face_detected.emit(face_roi)
                
                # Hiển thị frame
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                    self.image_label.width(),
                    self.image_label.height(),
                    Qt.AspectRatioMode.KeepAspectRatio
                )
                self.image_label.setPixmap(scaled_pixmap)

    def stop_camera(self):
        """Dừng camera"""
        if self.camera is not None:
            self.camera.release()
        if self.timer is not None:
            self.timer.stop()
