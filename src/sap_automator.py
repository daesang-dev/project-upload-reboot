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
        "username": "dsvn55",
        "password": "Dsvn@6026"
    },
    "coords": {
        "posting_date": (644 - 530, 312 - 236),
        "user_name": (633 - 530, 327 - 236),
        "btn_check": (580 - 530, 377 - 236),
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
            
            # Đợi SAP phản hồi sau khi nhấn Import (thay vì sleep cứng 2s)
            self._wait_for_pixel_change(upload_win, self.config['coords']['offset_region'], interval=1.0, timeout=20)
            
            # Cần thay đợi system message rồi mới ấn enter
            print(">>> Đang đợi System Message xuất hiện...")
            wait_start = time.time()
            popup_handled = False
            while time.time() - wait_start < 30: # Timeout 30s
                if self._check_and_skip_message():
                    popup_handled = True
                    break
                time.sleep(0.5)
            
            if not popup_handled:
                print(">>> Không thấy System Message, tự động nhấn ENTER để tiếp tục...")
                upload_win.type_keys("{ENTER}")

            # Sử dụng tham số khắt khe: interval 1.5, timeout 40
            if self._wait_for_pixel_change(upload_win, self.config['coords']['offset_region'], interval=1.5, timeout=40):
                print(">>> Dữ liệu Upload đã load. Đang xác nhận các bước cuối...")
                time.sleep(3)
                upload_win.type_keys("{ENTER}")
                time.sleep(3)
                upload_win.type_keys("{ENTER}")
                time.sleep(2)
                upload_win.type_keys("{ESC}")
                print("=== HOÀN THÀNH UPLOAD EXCEL ===")
                return True
            else:
                print("!!! Lỗi Upload: Dữ liệu không load.")
        except Exception as e:
            print(f"Lỗi quy trình Upload: {e}")
        return False

    def create_sales_order(self, posting_date=None):
        """Quy trình Create Sales Order (Sử dụng State Machine 100% từ file test)."""
        print("\n=== BẮT ĐẦU QUY TRÌNH 2: CREATE SALES ORDER ===")
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
            create_win.type_keys("^a{BACKSPACE}" + self.config['credentials']['username'] + "{ENTER}", with_spaces=True)
            
            time.sleep(1)
            self._check_and_skip_message()

            # --- KÍCH HOẠT STATE MACHINE (Khớp hoàn toàn file test) ---
            print("\n--- KÍCH HOẠT STATE MACHINE CHO CREATE ---")
            current_step = 3 
            max_retries = 100 
            attempts = 0

            while attempts < max_retries:
                # [BƯỚC 3] TÌM DỮ LIỆU & TICK CHỌN TẤT CẢ
                if current_step == 3:
                    print(f"\n[BƯỚC 3] Đang thực hiện Find dữ liệu (Lần thử {attempts + 1})...")
                    time.sleep(3)
                    create_win.set_focus()
                    create_win.type_keys("{ENTER}") 
                    
                    if self._wait_for_pixel_change(create_win, self.config['coords']['offset_region'], interval=1.2, timeout=25):
                        print(">>> Dữ liệu đã load. Đang đợi status bar biến mất...")
                        time.sleep(1)
                        # Mouse Wiggle logic
                        pyautogui.moveTo(500, 500, duration=0.5)
                        pyautogui.moveRel(0, 10, duration=0.5)
                        time.sleep(1)
                        
                        print(">>> Đang nhấn nút Checkbox tổng...")
                        create_win.click_input(coords=self.config['coords']['btn_check'])
                        
                        print(">>> Đang đợi hệ thống xử lý xong Checkbox (Đợi ổn định)...")
                        time.sleep(0.5) 
                        # Tham số khắt khe: timeout 120, stability 3.0
                        if self._wait_for_pixel_stability(create_win, self.config['coords']['offset_region'], interval=0.3, timeout=120, stability_time=3.0):
                            print(">>> Dữ liệu đã ổn định hoàn toàn. Chuẩn bị sang Bước 4.")
                            time.sleep(5)
                            current_step = 4
                        else:
                            print("!!! Lỗi: Đã nhấn Checkbox nhưng không thấy thay đổi.")
                            attempts += 1; continue
                    else:
                        print("!!! Không thấy dữ liệu xuất hiện. Kiểm tra Popup...")
                        self._check_and_skip_message()
                        attempts += 1; continue

                # [BƯỚC 4] NHẤN CREATE -> ĐỢI POPUP -> KIỂM TRA KẾT QUẢ
                if current_step == 4:
                    print("\n[BƯỚC 4] Chuẩn bị nhấn Create...")
                    
                    # XÓA MÀU XANH CŨ (Vòng lặp 15s + Mouse Wiggle)
                    print(">>> Đang đợi Status Bar cũ biến mất để không bắt nhầm...")
                    start_wait = time.time()
                    while time.time() - start_wait < 15:
                        pyautogui.moveTo(500, 500, duration=0.5)
                        pyautogui.moveRel(0, 10, duration=0.5)
                        if self._get_status_state() == "NORMAL":
                            print(">>> Status Bar đã sạch. Tiến hành nhấn Create.")
                            break
                        time.sleep(1)
                    else:
                        print("!!! Cảnh báo: Status bar vẫn còn màu của bước trước.")

                    print(">>> Đang thực hiện lệnh CREATE...")
                    create_win.set_focus()
                    time.sleep(0.5)
                    create_win.click_input(coords=self.config['coords']['btn_create'])

                    # 1. Đợi Popup xác nhận (Timeout 500s khắt khe)
                    print(">>> Đang đợi Popup xác nhận xuất hiện...")
                    popup_handled = False
                    retry_done = False
                    wait_popup_start = time.time()
                    while time.time() - wait_popup_start < 500: 
                        if self._check_and_skip_message():
                            print(">>> Đã phát hiện và đóng Popup xác nhận.")
                            popup_handled = True
                            break
                        
                        # Logic Retry: Nếu quá 100s chưa thấy popup, thử nhấn Create lại lần nữa
                        if not retry_done and (time.time() - wait_popup_start > 100):
                            print(">>> Sau 100s chưa thấy popup, thực hiện nhấn CREATE lần 2...")
                            create_win.set_focus()
                            create_win.click_input(coords=self.config['coords']['btn_create'])
                            retry_done = True

                        time.sleep(0.5)
                    
                    if not popup_handled:
                        print("!!! Cảnh báo: Không thấy Popup xuất hiện sau thời gian chờ.")

                    # 2. Giám sát kết quả cuối (Timeout 800s khắt khe)
                    print(">>> Đang giám sát kết quả cuối (Status Bar & Popups)...")
                    monitoring_start = time.time()
                    while time.time() - monitoring_start < 800:
                        if self._check_and_skip_message():
                            print(">>> Phát hiện Popup lỗi/cảnh báo sau Create. Quay lại Bước 3.")
                            current_step = 3; attempts += 1; break

                        status_color = self._get_status_state()
                        if status_color == "RED":
                            print("!!! Create thất bại (Status RED). Quay lại Bước 3.")
                            time.sleep(2)
                            current_step = 3; attempts += 1; break
                            
                        if status_color == "GREEN":
                            print("\n=== THÀNH CÔNG THỰC SỰ! Đã tạo đơn hàng. ===")
                            return True 

                        time.sleep(0.5)
                    else:
                        print("!!! Quá thời gian chờ phản hồi sau khi nhấn Create.")
                        current_step = 3; attempts += 1
            
            return False
        except Exception as e:
            print(f"Lỗi quy trình Create: {e}")
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