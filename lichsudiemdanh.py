from PyQt6.QtWidgets import QMainWindow, QTableWidgetItem
from PyQt6.QtCore import Qt
from PyQt6 import uic
from database import Database
from datetime import datetime

class LichSuDiemDanhWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("lichsudiemdanh.ui", self)
        self.db = Database()
        self.setup_table()
        
    def showEvent(self, event):
        """Override showEvent để load dữ liệu mới khi cửa sổ được hiển thị"""
        super().showEvent(event)
        self.load_data()  # Refresh dữ liệu mỗi khi cửa sổ được hiển thị

    def setup_table(self):
        """Thiết lập cấu hình bảng"""
        # Thiết lập độ rộng cột
        self.tblSinhVien.setColumnWidth(0, 150)  # Mã SV
        self.tblSinhVien.setColumnWidth(1, 250)  # Tên SV
        self.tblSinhVien.setColumnWidth(2, 150)  # Lớp
        self.tblSinhVien.setColumnWidth(3, 150)  # Ngày
        self.tblSinhVien.setColumnWidth(4, 150)  # Thời gian
        
        # Căn giữa các cột
        self.tblSinhVien.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Không cho phép sửa trực tiếp trên bảng
        self.tblSinhVien.setEditTriggers(self.tblSinhVien.EditTrigger.NoEditTriggers)

        # Kết nối nút tìm kiếm
        self.btnTimKiem.clicked.connect(self.search_attendance)

    def load_data(self):
        """Load tất cả lịch sử điểm danh"""
        self.tblSinhVien.setRowCount(0)
        
        query = """
            SELECT dd.ma_sv, sv.ho_ten, sv.lop, 
                   DATE_FORMAT(dd.ngay_diem_danh, '%d/%m/%Y') as ngay,
                   TIME_FORMAT(dd.thoi_gian, '%H:%i:%s') as thoi_gian
            FROM diem_danh dd
            JOIN sinh_vien sv ON dd.ma_sv = sv.ma_sv
            ORDER BY dd.ngay_diem_danh DESC, dd.thoi_gian DESC
        """
        
        try:
            records = self.db.fetch_data(query)
            if records:
                for row, record in enumerate(records):
                    self.tblSinhVien.insertRow(row)
                    self.tblSinhVien.setItem(row, 0, QTableWidgetItem(record['ma_sv']))
                    self.tblSinhVien.setItem(row, 1, QTableWidgetItem(record['ho_ten']))
                    self.tblSinhVien.setItem(row, 2, QTableWidgetItem(record['lop']))
                    self.tblSinhVien.setItem(row, 3, QTableWidgetItem(record['ngay']))
                    self.tblSinhVien.setItem(row, 4, QTableWidgetItem(record['thoi_gian']))
        except Exception as e:
            print(f"Lỗi khi tải dữ liệu: {str(e)}")

    def search_attendance(self):
        """Tìm kiếm lịch sử điểm danh theo mã sinh viên hoặc tên"""
        search_text = self.txtTimKiem.text().strip()
        
        if not search_text:
            self.load_data()
            return
            
        self.tblSinhVien.setRowCount(0)
        
        query = """
            SELECT dd.ma_sv, sv.ho_ten, sv.lop, 
                   DATE_FORMAT(dd.ngay_diem_danh, '%d/%m/%Y') as ngay,
                   TIME_FORMAT(dd.thoi_gian, '%H:%i:%s') as thoi_gian
            FROM diem_danh dd
            JOIN sinh_vien sv ON dd.ma_sv = sv.ma_sv
            WHERE dd.ma_sv LIKE %s OR sv.ho_ten LIKE %s
            ORDER BY dd.ngay_diem_danh DESC, dd.thoi_gian DESC
        """
        
        try:
            search_pattern = f"%{search_text}%"
            records = self.db.fetch_data(query, (search_pattern, search_pattern))
            
            if records:
                for row, record in enumerate(records):
                    self.tblSinhVien.insertRow(row)
                    self.tblSinhVien.setItem(row, 0, QTableWidgetItem(record['ma_sv']))
                    self.tblSinhVien.setItem(row, 1, QTableWidgetItem(record['ho_ten']))
                    self.tblSinhVien.setItem(row, 2, QTableWidgetItem(record['lop']))
                    self.tblSinhVien.setItem(row, 3, QTableWidgetItem(record['ngay']))
                    self.tblSinhVien.setItem(row, 4, QTableWidgetItem(record['thoi_gian']))
        except Exception as e:
            print(f"Lỗi khi tìm kiếm: {str(e)}")

    def update_attendance(self, ma_sv):
        """Cập nhật bảng khi có điểm danh mới"""
        query = """
            SELECT dd.ma_sv, sv.ho_ten, sv.lop, 
                   DATE_FORMAT(dd.ngay_diem_danh, '%d/%m/%Y') as ngay,
                   TIME_FORMAT(dd.thoi_gian, '%H:%i:%s') as thoi_gian
            FROM diem_danh dd
            JOIN sinh_vien sv ON dd.ma_sv = sv.ma_sv
            WHERE dd.ma_sv = %s
            AND DATE(dd.ngay_diem_danh) = CURDATE()
            ORDER BY dd.ngay_diem_danh DESC, dd.thoi_gian DESC
            LIMIT 1
        """
        
        try:
            record = self.db.fetch_data(query, (ma_sv,))
            if record:
                # Thêm bản ghi mới vào đầu bảng
                self.tblSinhVien.insertRow(0)
                self.tblSinhVien.setItem(0, 0, QTableWidgetItem(record[0]['ma_sv']))
                self.tblSinhVien.setItem(0, 1, QTableWidgetItem(record[0]['ho_ten']))
                self.tblSinhVien.setItem(0, 2, QTableWidgetItem(record[0]['lop']))
                self.tblSinhVien.setItem(0, 3, QTableWidgetItem(record[0]['ngay']))
                self.tblSinhVien.setItem(0, 4, QTableWidgetItem(record[0]['thoi_gian']))
                
                # Tự động cuộn lên đầu bảng
                self.tblSinhVien.scrollToTop()
        except Exception as e:
            print(f"Lỗi khi cập nhật lịch sử điểm danh: {str(e)}")

    def on_student_deleted(self, ma_sv):
        """Xóa tất cả bản ghi điểm danh của sinh viên bị xóa"""
        # Xóa khỏi database trước
        query = "DELETE FROM diem_danh WHERE ma_sv = %s"
        self.db.execute_query(query, (ma_sv,))
        
        # Sau đó xóa khỏi bảng hiển thị
        for row in range(self.tblSinhVien.rowCount() - 1, -1, -1):
            if self.tblSinhVien.item(row, 0).text() == ma_sv:
                self.tblSinhVien.removeRow(row)