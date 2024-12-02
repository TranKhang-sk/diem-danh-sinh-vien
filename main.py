from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox
from PyQt6.QtCore import QSize
from PyQt6 import uic
import sys
from sinhvien import SinhVienWindow
from diemdanh import DiemDanhWindow
from lichsudiemdanh import LichSuDiemDanhWindow
from lophocphan import LopHocPhanWindow
from tinhdiem import TinhDiemWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hệ thống điểm danh sinh viên")
        
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Khởi tạo các cửa sổ
        self.sinhvien_window = SinhVienWindow()
        self.diemdanh_window = DiemDanhWindow()
        self.lichsu_window = LichSuDiemDanhWindow()
        self.lophocphan_window = LopHocPhanWindow()
        self.tinhdiem_window = TinhDiemWindow()
        
        # Kết nối signal điểm danh với slot cập nhật lịch sử
        self.diemdanh_window.attendance_updated.connect(self.lichsu_window.update_attendance)
        
        # Kết nối signal xóa sinh viên với slot cập nhật lịch sử và tính điểm
        self.sinhvien_window.student_deleted.connect(self.lichsu_window.on_student_deleted)
        self.sinhvien_window.student_deleted.connect(self.tinhdiem_window.on_student_deleted)
        
        # Thêm vào stacked widget
        self.stacked_widget.addWidget(self.sinhvien_window)
        self.stacked_widget.addWidget(self.diemdanh_window)
        self.stacked_widget.addWidget(self.lichsu_window)
        self.stacked_widget.addWidget(self.lophocphan_window)
        self.stacked_widget.addWidget(self.tinhdiem_window)
        
        # Kết nối các nút chuyển đổi
        self.connect_navigation()
        
        # Điều chỉnh kích thước main window theo widget hiện tại
        self.adjust_size()
        
        # Liên kết 2 cửa sổ
        self.diemdanh_window.lichsu_window = self.lichsu_window
        
    def adjust_size(self):
        """Điều chỉnh kích thước main window theo widget đang hiển thị"""
        current_widget = self.stacked_widget.currentWidget()
        if current_widget:
            self.resize(current_widget.size())
            self.setFixedSize(current_widget.size())
    
    def connect_navigation(self):
        # Từ SinhVien window
        self.sinhvien_window.btnDiemDanh.clicked.connect(
            lambda: self.switch_window(self.diemdanh_window))
        self.sinhvien_window.btnLichSu.clicked.connect(
            lambda: self.switch_window(self.lichsu_window))
        self.sinhvien_window.btnLopHocPhan.clicked.connect(
            lambda: self.switch_window(self.lophocphan_window))
        self.sinhvien_window.btnThoat.clicked.connect(self.close)

        # Từ DiemDanh window 
        self.diemdanh_window.btnSinhVien.clicked.connect(
            lambda: self.switch_window(self.sinhvien_window))
        self.diemdanh_window.btnLichSu.clicked.connect(
            lambda: self.switch_window(self.lichsu_window))
        self.diemdanh_window.btnLopHocPhan.clicked.connect(
            lambda: self.switch_window(self.lophocphan_window))
        self.diemdanh_window.btnThoat.clicked.connect(self.close)

        # Từ LichSu window
        self.lichsu_window.btnSinhVien.clicked.connect(
            lambda: self.switch_window(self.sinhvien_window))
        self.lichsu_window.btnDiemDanh.clicked.connect(
            lambda: self.switch_window(self.diemdanh_window))
        self.lichsu_window.btnLopHocPhan.clicked.connect(
            lambda: self.switch_window(self.lophocphan_window))
        self.lichsu_window.btnThoat.clicked.connect(self.close)

        # Từ LopHocPhan window
        self.lophocphan_window.btnSinhVien.clicked.connect(
            lambda: self.switch_window(self.sinhvien_window))
        self.lophocphan_window.btnDiemDanh.clicked.connect(
            lambda: self.switch_window(self.diemdanh_window))
        self.lophocphan_window.btnLichSu.clicked.connect(
            lambda: self.switch_window(self.lichsu_window))
        self.lophocphan_window.btnThoat.clicked.connect(self.close)

        # Từ TinhDiem window
        self.tinhdiem_window.btnSinhVien.clicked.connect(
            lambda: self.switch_window(self.sinhvien_window))
        self.tinhdiem_window.btnDiemDanh.clicked.connect(
            lambda: self.switch_window(self.diemdanh_window))
        self.tinhdiem_window.btnLichSu.clicked.connect(
            lambda: self.switch_window(self.lichsu_window))
        self.tinhdiem_window.btnLopHocPhan.clicked.connect(
            lambda: self.switch_window(self.lophocphan_window))
        self.tinhdiem_window.btnThoat.clicked.connect(self.close)

        # Kết nối nút Tính Điểm từ các window khác
        self.sinhvien_window.btnTinhDiem.clicked.connect(
            lambda: self.switch_window(self.tinhdiem_window))
        self.diemdanh_window.btnTinhDiem.clicked.connect(
            lambda: self.switch_window(self.tinhdiem_window))
        self.lichsu_window.btnTinhDiem.clicked.connect(
            lambda: self.switch_window(self.tinhdiem_window))
        self.lophocphan_window.btnTinhDiem.clicked.connect(
            lambda: self.switch_window(self.tinhdiem_window))

    def switch_window(self, window):
        """Chuyển đổi giữa các cửa sổ"""
        # Tắt camera nếu đang ở giao diện điểm danh
        if isinstance(self.stacked_widget.currentWidget(), DiemDanhWindow):
            self.diemdanh_window.stop_camera()
        
        self.stacked_widget.setCurrentWidget(window)
        self.adjust_size()

    def show_tinh_diem(self):
        """Chuyển đến giao diện tính điểm"""
        self.switch_window(self.tinhdiem_window)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())