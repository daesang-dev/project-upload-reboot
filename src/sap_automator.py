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
        try:
            r, g, b = pyautogui.pixel(x, y)
            
            if r > 180 and g < 50 and b < 50: 
                return "RED"
            
            if g > 150 and r < 150 and b < 150 and (g - r) > 30 and (g - b) > 30:
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
            
            self.win.child_window(title="Miwon", class_name="TMMDIChildClass").wait('exists', timeout=240)
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
        try:
            upload_win = self._open_function_window(self.config['windows']['upload_window'])
            time.sleep(2)

            path_edit = upload_win.child_window(class_name="TMEditTextClass", found_index=0)
            path_edit.click_input()
            time.sleep(1)

            path_edit.type_keys(file_path, with_spaces=True, pause=0.05)
            time.sleep(2)

            upload_win.click_input(coords=self.config['coords']['import_btn'])
            
            self._wait_for_pixel_change(upload_win, self.config['coords']['offset_region'], interval=1.0, timeout=20)
            
            wait_start = time.time()
            upload_confirm = False
            while time.time() - wait_start < 30: # Timeout 30s
                if self._check_and_skip_message():
                    upload_confirm = True
                    break
                time.sleep(0.5)
            
            if not upload_confirm:
                upload_win.type_keys("{ENTER}")

            if self._wait_for_pixel_change(upload_win, self.config['coords']['offset_region'], interval=1.5, timeout=40):
                time.sleep(3)
                upload_win.type_keys("{ENTER}")
                time.sleep(3)
                upload_win.type_keys("{ENTER}")
                time.sleep(2)
                upload_win.type_keys("{ESC}")
                return True
            else:
                print("!!! Lỗi Upload: Dữ liệu không load.")
        except Exception as e:
            print(f"Lỗi quy trình Upload: {e}")
        return False

    def fill_create_info(self, posting_date=None):
        """Mở cửa sổ Create Sales Order và điền thông tin ngày, user."""
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
        if not create_win:
            return False
        
        try:
            current_step = 3 
            max_retries = 100 
            attempts = 0

            while attempts < max_retries:
                if current_step == 3:
                    time.sleep(3)
                    create_win.set_focus()
                    create_win.type_keys("{ENTER}") 
                    
                    if self._wait_for_pixel_change(create_win, self.config['coords']['offset_region'], interval=1.2, timeout=25):
                        time.sleep(1)
                        pyautogui.moveTo(500, 500, duration=0.5)
                        pyautogui.moveRel(0, 10, duration=0.5)
                        time.sleep(1)
                        
                        create_win.click_input(coords=self.config['coords']['btn_check'])
                        
                        time.sleep(0.5) 
                        if self._wait_for_pixel_stability(create_win, self.config['coords']['offset_region'], interval=0.3, timeout=300, stability_time=10.0):
                            time.sleep(5)
                            current_step = 4
                        else:
                            attempts += 1; continue
                    else:
                        self._check_and_skip_message()
                        attempts += 1; continue

                if current_step == 4:
                    create_win.set_focus()
                    time.sleep(0.5)
                    create_win.click_input(coords=self.config['coords']['btn_create'])

                    create_order_confirm = False
                    retry_done = False
                    wait_popup_start = time.time()
                    while time.time() - wait_popup_start < 500: 
                        if self._check_and_skip_message():
                            create_order_confirm = True
                            break
                        
                        # Logic Retry: Nếu quá 100s chưa thấy popup, thử nhấn Create lại lần nữa
                        if not retry_done and (time.time() - wait_popup_start > 100):
                            create_win.set_focus()
                            create_win.click_input(coords=self.config['coords']['btn_create'])
                            retry_done = True

                        time.sleep(0.5)
                    
                    if not create_order_confirm:
                        print("Không thấp popup xác nhận tạo đơn hàng xuất hiện")

                    monitoring_start = time.time()
                    while time.time() - monitoring_start < 800:
                        if self._check_and_skip_message():
                            current_step = 3; attempts += 1; break

                        status_color = self._get_status_state()
                        if status_color == "RED":
                            time.sleep(2)
                            current_step = 3; attempts += 1; break

                        time.sleep(0.5)
                    else:
                        print("!!! Quá thời gian chờ phản hồi sau khi nhấn Create.")
                        current_step = 3; attempts += 1
            
            return False
        except Exception as e:
            print(f"Lỗi quy trình thực thi Create: {e}")
            return False

    def create_sales_order(self, posting_date=None):
        """Quy trình Create Sales Order (Gộp 2 bước)."""
        print("\n=== BẮT ĐẦU QUY TRÌNH 2: CREATE SALES ORDER ===")
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