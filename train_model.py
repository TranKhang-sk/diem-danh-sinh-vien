import cv2
import numpy as np
from database import Database
import sys

# Thêm cấu hình UTF-8 cho console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def train_face_model():
    """Train model nhận diện khuôn mặt từ database"""
    try:
        # Khởi tạo recognizer
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        db = Database()
        faces = []
        labels = []
        
        print("Bắt đầu quá trình training...")
        
        # Lấy dữ liệu từ database
        query = "SELECT ma_sv, anh_khuon_mat_1, anh_khuon_mat_2, anh_khuon_mat_3, anh_khuon_mat_4, anh_khuon_mat_5 FROM sinh_vien"
        students = db.fetch_data(query)
        
        if not students:
            print("Không có dữ liệu sinh viên trong database!")
            return False

        # Tạo dictionary để map mã sinh viên với ID nhỏ hơn
        student_ids = {}
        current_id = 1

        for student in students:
            try:
                ma_sv = student['ma_sv']
                # Gán ID nhỏ hơn cho mỗi sinh viên
                if ma_sv not in student_ids:
                    student_ids[ma_sv] = current_id
                    current_id += 1
                
                label = student_ids[ma_sv]
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
            
            print("\nThông tin training:")
            print(f"Số lượng ảnh: {len(faces)}")
            print(f"Labels: {labels}")
            print("\nMap mã sinh viên với label:")
            student_mapping = {}
            for ma_sv, label in student_ids.items():
                student_mapping[ma_sv] = label
                print(f"{ma_sv} -> {label}")
            
            # Lưu mapping để sử dụng khi nhận diện
            import json
            with open('student_mapping.json', 'w') as f:
                json.dump(student_mapping, f)
            print("\nĐã lưu mapping vào file student_mapping.json")
            
            # Train model
            print("\nBắt đầu train model...")
            recognizer.train(faces, labels)
            print("Train model thành công!")
            
            # Lưu model
            recognizer.save('face_model.yml')
            print("Đã lưu model vào file face_model.yml!")
            return True
        else:
            print("Không có đủ dữ liệu để train model!")
            return False
            
    except Exception as e:
        print(f"Lỗi trong quá trình train model: {str(e)}")
        return False

if __name__ == "__main__":
    # Chạy training khi chạy file này trực tiếp
    if train_face_model():
        print("\nQuá trình training hoàn tất thành công!")
    else:
        print("\nQuá trình training thất bại!") 