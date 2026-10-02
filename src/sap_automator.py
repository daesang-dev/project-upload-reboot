import subprocess
import time
import psutil
import pyautogui
import sys
from pywinauto import Application
from datetime import datetime
from PIL import ImageChops, ImageGrab

# Cấu hình hệ thống SAP
SAP_CONFIG = {
    "app": {
        "path": r"C:\Program Files\SAP\SAP Business One\SAP Business One.exe",
        "process_name": "SAP Business One.exe",
    },
    "credentials": {
        "username": "dsvn57",
        "password": "Dsvn@1427"
    },
    "coords": {
        "posting_date": (644 - 530, 312 - 236),
        "user_name": (633 - 530, 327 - 236),
        "btn_check": (580 + 20 - 530, 377 - 236),
        "btn_create": (1140 - 530, 769 - 236),
        "offset_region": (32, 175, 1030, 333),
        "import_btn": (662, 499)
    },
    "windows": {
        "main_title": "SAP Business One",
        "upload_window": "Sales Order excel upload",
        "create_window": "Sales Order Create"
    }
}

class SAPAutomator:
    def __init__(self):
        """Khởi tạo SAPAutomator với cấu hình nội bộ"""
        self.config = SAP_CONFIG
        self.app = None
        self.win = None

    def _wait_for_pixel_change(self, window, offset_region, interval=1.2, timeout=30):
        """Logic từ file test: Đợi thay đổi pixel với log chi tiết."""
        rect = window.rectangle()
        abs_region = (
            rect.left + offset_region[0], rect.top + offset_region[1], 
            rect.left + offset_region[2], rect.top + offset_region[3]
        )
        print(f"--- Đang theo dõi thay đổi (interval={interval}s) tại: {abs_region} ---")
        
        img_original = ImageGrab.grab(bbox=abs_region)
        start_time = time.time()

        while time.time() - start_time < timeout:
            time.sleep(interval)
            img_current = ImageGrab.grab(bbox=abs_region)
            diff = ImageChops.difference(img_current, img_original).getbbox()
            
            if diff:
                print(f">>> Dữ liệu đã thay đổi sau {round(time.time() - start_time, 1)}s.")
                return True
        
        print("!!! Lỗi: Quá thời gian chờ nhưng không có dữ liệu mới.")
        return False

    def _wait_for_pixel_stability(self, window, offset_region, interval=0.3, timeout=60, stability_time=2.0):
        """Logic từ file test: Đợi ổn định pixel (stability_time khắt khe)."""
        rect = window.rectangle()
        abs_region = (
            rect.left + offset_region[0], rect.top + offset_region[1], 
            rect.left + offset_region[2], rect.top + offset_region[3]
        )
        print(f"--- Đang theo dõi sự ổn định (interval={interval}s) tại: {abs_region} ---")
        
        img_prev = ImageGrab.grab(bbox=abs_region)
        start_time = time.time()
        stable_since = time.time()

        while time.time() - start_time < timeout:
            time.sleep(interval)
            img_curr = ImageGrab.grab(bbox=abs_region)
            diff = ImageChops.difference(img_curr, img_prev).getbbox()
            
            if diff:
                img_prev = img_curr
                stable_since = time.time()
            else:
                if time.time() - stable_since >= stability_time:
                    print(f">>> Dữ liệu đã ổn định sau {round(time.time() - start_time, 1)}s.")
                    return True
        
        print("!!! Lỗi: Quá thời gian chờ nhưng dữ liệu vẫn chưa ổn định.")
        return False

    def _check_and_skip_message(self, max_tries=3):
        """Logic từ file test: Kiểm tra và đóng System Message."""
        message_handled = False
        if not self.win: return False
        for _ in range(max_tries):
            found = False
            for child in self.win.descendants(class_name="TMMDIChildClass"):
                try:
                    if child.window_text() == "System Message":
                        print(f">>> Phát hiện System Message. Đang đóng...")
                        child.set_focus()
                        time.sleep(0.5)
                        child.type_keys("{ENTER}")
                        time.sleep(1.5)
                        found = True
                        message_handled = True
                        break 
                except: continue
            if not found: break
        return message_handled

    def _get_status_state(self, x=1690, y=1020):
        """Logic từ file test: Kiểm tra màu status bar với Debug RGB."""
        try:
            r, g, b = pyautogui.pixel(x, y)
            print(f"   [Debug Pixel] Tại ({x}, {y}) mã màu đang là: RGB({r}, {g}, {b})")
            
            if r > 180 and g < 50 and b < 50: 
                return "RED"
            
            if g > 150 and r < 150 and b < 150 and (g - r) > 30 and (g - b) > 30:
                print(f"   >>> KÍCH HOẠT XANH VÌ RGB({r}, {g}, {b}) THỎA MÃN ĐIỀU KIỆN!")
                return "GREEN"
            
            return "NORMAL"
        except Exception as e:
            print(f"Lỗi đọc pixel: {e}")
            return "UNKNOWN"

    def start_sap(self):
        """Mở SAP, đăng nhập và kết nối pywinauto."""
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == self.config['app']['process_name']:
                print("Đóng tiến trình SAP cũ...")
                proc.kill()
                proc.wait(timeout=5)
        time.sleep(2)

        subprocess.Popen(self.config['app']['path'])
        print("Đang đợi 10 giây để SAP load...")
        time.sleep(10) 

        try:
            self.app = Application(backend="win32").connect(path=self.config['app']['path'], timeout=60)
            self.win = self.app.top_window()
            self.win.set_focus()

            print("\n[HỆ THỐNG] Thực hiện Đăng nhập...")
            login_dialog = self.win.child_window(title=self.config['windows']['main_title'], class_name="TMMDIChildClass")
            login_dialog.Edit0.set_focus()
            
            login_keys = f"{self.config['credentials']['username']}{{TAB}}{self.config['credentials']['password']}{{ENTER}}"
            login_dialog.Edit0.type_keys(login_keys, with_spaces=True)
            
            # --- ĐOẠN CODE QUAN TRỌNG: Chờ đối tượng Miwon xuất hiện (Timeout 240s) ---
            print(">>> Đang chờ đăng nhập thành công (Cửa sổ Miwon)...")
            self.win.child_window(title="Miwon", class_name="TMMDIChildClass").wait('exists', timeout=240)
            print(">>> Đăng nhập thành công!")
            return True
        except Exception as e:
            print(f"Lỗi khởi động SAP: {e}")
            return False

    def _open_function_window(self, window_name):
        """Mở cửa sổ chức năng bằng phím tắt Ctrl+F3 với logic Retry từ file test."""
        self.win.type_keys('^{F3}')
        time.sleep(1)
        
        search_box = self.win.child_window(class_name="TMEditTextClass", found_index=0)
        search_box.wait('ready', timeout=20)
        
        # Logic Retry nhập liệu từ file test
        try:
            search_box.click_input()
            time.sleep(0.5)
            self.win.type_keys("^a{BACKSPACE}" + window_name + "{ENTER}", with_spaces=True, pause=0.1)
        except Exception as e:
            print(f"Lỗi nhập search box, thử lại... {e}")
            search_box.click_input()
            search_box.type_keys("^a{BACKSPACE}" + window_name + "{ENTER}", with_spaces=True, set_foreground=False)
        
        print(f"Đang chờ cửa sổ {window_name} xuất hiện...")
        target_win = self.win.child_window(title_re=f".*{window_name}.*", class_name="TMMDIChildClass")
        target_win.wait('exists', timeout=20).set_focus()
        return target_win

    def upload_excel(self, file_path):
        """Quy trình Upload file Excel (Cập nhật timeout và các bước xác nhận)."""
        print(f"\n=== BẮT ĐẦU QUY TRÌNH 1: UPLOAD FILE EXCEL: {file_path} ===")
        try:
            upload_win = self._open_function_window(self.config['windows']['upload_window'])
            time.sleep(2)

            path_edit = upload_win.child_window(class_name="TMEditTextClass", found_index=0)
            path_edit.click_input()
            time.sleep(1)

            print(f"Đang gõ đường dẫn: {file_path}")
            path_edit.type_keys(file_path, with_spaces=True, pause=0.05)
            time.sleep(2)

            print(f"Đang nhấn nút Import tại {self.config['coords']['import_btn']}...")
            upload_win.click_input(coords=self.config['coords']['import_btn'])
            
            self._wait_for_pixel_change(upload_win, self.config['coords']['offset_region'], interval=1.0, timeout=20)
            
            # Kiểm tra popup xác nhận upload hiện lên 
            wait_start = time.time()
            popup_handled = False
            while time.time() - wait_start < 30: # Timeout 30s
                if self._check_and_skip_message():
                    popup_handled = True
                    break
            
            if not popup_handled:
                print(">>> Không thấy System Message, tự động nhấn ENTER để tiếp tục...")
                upload_win.type_keys("{ENTER}")

            # Kiểm tra dữ liệu được hiển thị ở bảng
            if self._wait_for_pixel_change(upload_win, self.config['coords']['offset_region'], interval=1.5, timeout=60):
                time.sleep(3)
                upload_win.type_keys("{ENTER}")
                time.sleep(3)
                upload_win.type_keys("{ENTER}")
                time.sleep(2)
                upload_win.type_keys("{ESC}")
                return True
        except Exception as e:
            print(f"Lỗi khi thực hiện upload excel: {e}")
        return False

    def fill_create_info(self, posting_date=None):
        """
        Mở cửa sổ Sales Order Create và điền các thông tin user và ngày làm đơn
        """
        
        try:
            create_win = self._open_function_window(self.config['windows']['create_window'])
            time.sleep(5)

            if not posting_date:
                posting_date = datetime.now().strftime("%d%m%Y")

            print("Đang nhập Posting Date và User...")
            create_win.click_input(coords=self.config['coords']['posting_date'])
            create_win.type_keys("^a{BACKSPACE}" + posting_date, with_spaces=True)
            time.sleep(1)
            create_win.click_input(coords=self.config['coords']['user_name'])
            create_win.type_keys("^a{BACKSPACE}" + self.config['credentials']['username'], with_spaces=True)
            
            time.sleep(1)
            self._check_and_skip_message()
            return create_win
        except Exception as e:
            print(f"Lỗi khi điền thông tin: {e}")
            return None

    def execute_create_order(self, create_win):
        """Thực hiện quy trình State Machine để tạo đơn hàng."""
        if not create_win:
            return False
        
        try:
            # Nhấn Enter (=Find) để tìm kiếm dữ liệu
            current_step = 3 
            max_retries = 100 
            attempts = 0

            while attempts < max_retries:
                if current_step == 3:
                    time.sleep(2)
                    # Nhấn Enter (nút tìm kiếm)
                    create_win.set_focus()
                    create_win.type_keys("{ENTER}") 
                    time.sleep(2)
                    
                    # Sau khi nút tìm kiếm được nhấn, chờ vùng hiển thị dữ liệu thay đổi
                    # Trường hợp 1: Phát hiện vùng theo dõi thay đổi (có dữ liệu)
                    if self._wait_for_pixel_change(create_win, self.config['coords']['offset_region'], interval=1.2, timeout=25):
                       # Nhấn vào checkbox để chọn toàn bộ đơn hàng đang hiển thị
                        create_win.click_input(coords=self.config['coords']['btn_check'])
                        
                        time.sleep(0.5) 

                        # Chờ cho checkbox của bảng hiển thị đơn hàng chạy xong (bảng không còn nhấp nháy/thay đổi dữ liệu)
                        if self._wait_for_pixel_stability(create_win, self.config['coords']['offset_region'], interval=0.3, timeout=300, stability_time=10.0):
                            time.sleep(5)
                            current_step = 4
                        else:
                            print("Quá thời gian chờ!")
                            return
                    else:
                        self._check_and_skip_message()
                        attempts += 1; continue

                if current_step == 4:
                    create_win.set_focus()
                    time.sleep(0.5)
                    # Nhấn nút tạo đơn hàng
                    create_win.click_input(coords=self.config['coords']['btn_create'])

                    popup_handled = False
                    retry_done = False
                    wait_popup_start = time.time()

                    # Trong vòng 500 giây kể từ khi ấn nút tạo đơn hàng, kiểm tra xem popup (system message) có hiện lên không
                    while time.time() - wait_popup_start < 500: 
                        if self._check_and_skip_message():
                            popup_handled = True
                            break
                        
                        # Nếu sau 50 giây popup xác nhận không hiện lên thì ấn tạo lại đơn hàng
                        if not retry_done and (time.time() - wait_popup_start > 50):
                            create_win.set_focus()
                            create_win.click_input(coords=self.config['coords']['btn_create'])
                            print("Quá thời gian chờ, nhấn lại nút tạo lại đơn hàng")
                            retry_done = True

                        time.sleep(0.5)
                    
                    # Trường hợp không có popup xác nhận tạo đơn hiện lên sau 500 giây thì chương trình bị huỷ
                    if not popup_handled:
                        print("Không phát hiện popup xác nhận tạo đơn hàng, huỷ chương trình...")
                        return

                    # Bắt đầu theo dõi sau khi popup tạo đơn được xác nhận
                    monitoring_start = time.time()
                    while time.time() - monitoring_start < 800:
                        # Trường hợp phát hiện popup (system message) báo lỗi
                        if self._check_and_skip_message() or self._get_status_state() == "RED":
                            current_step = 3; attempts += 1; break

                        time.sleep(0.5)
                    else:
                        print("Không phát hiện thay đổi khi nhấn Create, quay lại bước tìm kiếm...")
                        current_step = 3; attempts += 1
            
            return False
        except Exception as e:
            print(f"Lỗi quy trình thực thi Create: {e}")
            return False

    def create_sales_order(self, posting_date=None):
        create_win = self.fill_create_info(posting_date)
        if create_win:
            return self.execute_create_order(create_win)
        return False

if __name__ == "__main__":
    # Kiểm tra tham số dòng lệnh
    if len(sys.argv) < 2:
        print("\n[LỖI] Thiếu đường dẫn file Excel.")
        print("Cách dùng: python src/sap_automator.py \"C:\\duong\\dan\\file.xlsx\"")
        sys.exit(1)

    excel_file_path = sys.argv[1]
    
    # Khởi tạo và chạy quy trình
    automator = SAPAutomator()
    
    print(f"--- BẮT ĐẦU TỰ ĐỘNG HÓA SAP VỚI FILE: {excel_file_path} ---")
    
    if automator.start_sap():
        if automator.upload_excel(excel_file_path):
            # Sau khi upload thành công, thực hiện tạo đơn hàng
            automator.create_sales_order()
        else:
            print("[THẤT BẠI] Quy trình Upload Excel không thành công.")
    else:
        print("[THẤT BẠI] Không thể khởi động hoặc đăng nhập SAP.")