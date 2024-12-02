from PyQt6.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox, QFileDialog
from PyQt6 import uic
from PyQt6.QtCore import Qt
from database import Database
from openpyxl import Workbook
from datetime import datetime

class TinhDiemWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('tinhdiem.ui', self)
        self.db = Database()
        
        # Kết nối các nút điều hướng
        self.btnSinhVien.clicked.connect(self.on_sinh_vien_clicked)
        self.btnDiemDanh.clicked.connect(self.on_diem_danh_clicked)
        self.btnLichSu.clicked.connect(self.on_lich_su_clicked)
        self.btnLopHocPhan.clicked.connect(self.on_lop_hoc_phan_clicked)
        self.btnThoat.clicked.connect(self.on_thoat_clicked)
        
        # Kết nối các nút chức năng
        self.btnTinh.clicked.connect(self.calculate_score)
        self.btnXuatExcel.clicked.connect(self.xuat_danh_sach_lop)
        self.tblTinhDiem.cellClicked.connect(self.get_item)
        
        # Tự động tải dữ liệu khi khởi tạo
        self.load_data()

    def xuat_danh_sach_lop(self):
        """Xuất danh sách lớp ra file Excel"""
        # Kiểm tra nếu bảng không có dữ liệu
        if self.tblTinhDiem.rowCount() == 0:
            QMessageBox.warning(self, "Thông báo", "Không có dữ liệu để xuất!")
            return

        # Mở hộp thoại lưu file
        file_name = f"danh_sach_lop_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Lưu file Excel", file_name, "Excel Files (*.xlsx)"
        )
        
        if not file_path:  # Nếu người dùng hủy
            return

        try:
            # Tạo workbook Excel
            wb = Workbook()
            ws = wb.active
            ws.title = "Danh sách lớp"

            # Ghi tiêu đề cột
            headers = ["Mã Sinh Viên", "Tên Sinh Viên", "Lớp", "Giới Tính", "Điểm"]
            ws.append(headers)

            # Ghi dữ liệu từ bảng vào file Excel
            for row in range(self.tblTinhDiem.rowCount()):
                row_data = []
                for col in range(self.tblTinhDiem.columnCount()):
                    item = self.tblTinhDiem.item(row, col)
                    row_data.append(item.text() if item else "")
                ws.append(row_data)

            # Định dạng cột (tùy chọn)
            for column in ws.columns:
                max_length = 0
                column = list(column)
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2)
                ws.column_dimensions[column[0].column_letter].width = adjusted_width

            # Lưu file Excel
            wb.save(file_path)
            QMessageBox.information(self, "Thông báo", "Xuất file Excel thành công!")

        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Đã xảy ra lỗi khi xuất file: {str(e)}")

    # Các phương thức điều hướng
    def on_sinh_vien_clicked(self):
        # Signal sẽ được kết nối từ MainWindow
        pass

    def on_diem_danh_clicked(self):
        # Signal sẽ được kết nối từ MainWindow
        pass

    def on_lich_su_clicked(self):
        # Signal sẽ được kết nối từ MainWindow
        pass

    def on_lop_hoc_phan_clicked(self):
        # Signal sẽ được kết nối từ MainWindow
        pass

    def on_thoat_clicked(self):
        # Signal sẽ được kết nối từ MainWindow
        pass

    def load_data(self):
        """Load dữ liệu sinh viên vào bảng"""
        query = """
            SELECT ma_sv, ho_ten, lop, gioi_tinh, diem 
            FROM sinh_vien 
            ORDER BY ma_sv
        """
        result = self.db.fetch_data(query)
        
        if result:
            self.tblTinhDiem.setRowCount(len(result))
            for row, student in enumerate(result):
                self.tblTinhDiem.setItem(row, 0, QTableWidgetItem(str(student['ma_sv'])))
                self.tblTinhDiem.setItem(row, 1, QTableWidgetItem(student['ho_ten']))
                self.tblTinhDiem.setItem(row, 2, QTableWidgetItem(student['lop']))
                self.tblTinhDiem.setItem(row, 3, QTableWidgetItem(student['gioi_tinh']))
                self.tblTinhDiem.setItem(row, 4, QTableWidgetItem(str(student['diem'] if student['diem'] else '')))
        else:
            QMessageBox.warning(self, "Thông báo", "Không có dữ liệu sinh viên!")

    def get_item(self, row, col):
        """Lấy thông tin sinh viên khi click vào bảng"""
        if row >= 0:
            ma_sv = self.tblTinhDiem.item(row, 0).text()
            query = """
                SELECT ma_sv, ho_ten, lop, gioi_tinh 
                FROM sinh_vien 
                WHERE ma_sv = %s
            """
            result = self.db.fetch_data(query, (ma_sv,))
            
            if result:
                student = result[0]
                self.txtMaSinhVien.setText(student['ma_sv'])
                self.txtTenSinhVien.setText(student['ho_ten'])
                self.txtGioiTinh.setText(student['gioi_tinh'])
                self.txtLop.setText(student['lop'])
                
                # Xóa dữ liệu cũ trong các ô nhập điểm
                self.txtCoPhep.clear()
                self.txtChuaPhep.clear()
                self.txtCoMat.clear()
                self.txtDiemQuaTrinh.clear()

    def calculate_score(self):
        """Tính điểm quá trình"""
        try:
            co_mat = int(self.txtCoMat.text() or 0)
            co_phep = int(self.txtCoPhep.text() or 0)
            khong_phep = int(self.txtChuaPhep.text() or 0)
            
            tong_diem = self.tinh_diem_qua_trinh(co_mat, co_phep, khong_phep)
            
            if isinstance(tong_diem, str):
                QMessageBox.warning(self, "Cảnh báo", tong_diem)
                return
                
            self.txtDiemQuaTrinh.setText(str(tong_diem))
            
            ma_sv = self.txtMaSinhVien.text()
            if ma_sv:
                query = "UPDATE sinh_vien SET diem = %s WHERE ma_sv = %s"
                if self.db.execute_query(query, (tong_diem, ma_sv)):
                    QMessageBox.information(self, "Thông báo", 
                                         f"Đã cập nhật điểm {tong_diem} cho sinh viên {ma_sv}")
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Lỗi", "Không thể cập nhật điểm!")
            
        except ValueError:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập số hợp lệ!")

    @staticmethod
    def tinh_diem_qua_trinh(co_mat, co_phep, khong_phep):
        """Tính điểm quá trình dựa trên số buổi học"""
        max_buoi_hoc = 12
        tong_diem = 10

        if co_mat + co_phep + khong_phep > max_buoi_hoc:
            return "Tổng số buổi vượt quá 12 buổi học!"

        diem_bi_tru = (co_phep * 0.5) + (khong_phep * 1)
        tong_diem -= diem_bi_tru

        return max(tong_diem, 0)

    def update_student_list(self, ma_sv=None):
        """Cập nhật danh sách sinh viên sau khi thêm mới"""
        query = """
            SELECT ma_sv, ho_ten, lop, gioi_tinh, diem 
            FROM sinh_vien 
            ORDER BY ma_sv
        """
        result = self.db.fetch_data(query)
        
        if result:
            self.tblTinhDiem.setRowCount(len(result))
            selected_row = None
            
            for row, student in enumerate(result):
                # Thêm thông tin sinh viên vào bảng
                self.tblTinhDiem.setItem(row, 0, QTableWidgetItem(str(student['ma_sv'])))
                self.tblTinhDiem.setItem(row, 1, QTableWidgetItem(student['ho_ten']))
                self.tblTinhDiem.setItem(row, 2, QTableWidgetItem(student['lop']))
                self.tblTinhDiem.setItem(row, 3, QTableWidgetItem(student['gioi_tinh']))
                self.tblTinhDiem.setItem(row, 4, QTableWidgetItem(str(student['diem'] if student['diem'] else '')))
                
                # Nếu là sinh viên mới thêm, lưu lại vị trí row
                if ma_sv and str(student['ma_sv']) == str(ma_sv):
                    selected_row = row
            
            # Nếu có sinh viên mới, select row đó
            if selected_row is not None:
                self.tblTinhDiem.selectRow(selected_row)
                # Scroll đến row được chọn
                self.tblTinhDiem.scrollToItem(self.tblTinhDiem.item(selected_row, 0))
                # Hiển thị thông tin sinh viên mới
                self.get_item(selected_row, 0)

    def on_student_deleted(self, ma_sv):
        """Xử lý khi sinh viên bị xóa từ giao diện sinh viên"""
        # Tìm và xóa sinh viên khỏi bảng tính điểm
        for row in range(self.tblTinhDiem.rowCount()):
            if self.tblTinhDiem.item(row, 0).text() == ma_sv:
                self.tblTinhDiem.removeRow(row)
                break
