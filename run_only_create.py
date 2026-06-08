import sys
import time
from pywinauto import Application
from src.sap_automator import SAPAutomator

def run_standalone_create():
    # 1. Khởi tạo automator
    automator = SAPAutomator()
    print("--- ĐANG KẾT NỐI VÀO PHIÊN SAP ĐANG MỞ ---")

    try:
        # 2. Kết nối vào ứng dụng SAP đang chạy bằng đường dẫn file thực thi
        print(f">>> Đang kết nối tới: {automator.config['app']['path']}")
        automator.app = Application(backend="win32").connect(path=automator.config['app']['path'], timeout=20)
        
        # Lấy cửa sổ top-level có tiêu đề chứa "SAP Business One"
        automator.win = automator.app.window(title_re=".*SAP Business One.*", found_index=0)
        automator.win.set_focus()
        print(">>> Đã kết nối thành công với SAP Business One.")

        # 3. Tìm cửa sổ "Sales Order Create"
        window_name = automator.config['windows']['create_window']
        print(f">>> Đang tìm cửa sổ: {window_name}...")
        
        # Thử tìm cửa sổ con (MDI Child)
        create_win = automator.win.child_window(title_re=f".*{window_name}.*", class_name="TMMDIChildClass")
        
        if not create_win.exists():
            print(f"[LỖI] Không tìm thấy cửa sổ '{window_name}'.")
            print("Vui lòng đảm bảo bạn đã mở sẵn màn hình này trong SAP trước khi chạy script.")
            return

        create_win.set_focus()
        print(">>> Đã tìm thấy cửa sổ. Bắt đầu thực thi logic tạo đơn...")

        # 4. Gọi riêng method execute_create_order
        # Method này sẽ tự chạy từ Bước 3 (Find) -> Bước 4 (Create)
        success = automator.execute_create_order(create_win)

        if success:
            print("\n[HOÀN THÀNH] Đã tạo đơn hàng thành công qua script riêng.")
        else:
            print("\n[THẤT BẠI] Script thực thi không thành công (có thể do lỗi dữ liệu hoặc timeout).")

    except Exception as e:
        print(f"\n[LỖI HỆ THỐNG] Không thể kết nối hoặc thực thi: {e}")
        print("Gợi ý: Hãy chắc chắn SAP đang mở và bạn đã đăng nhập.")

if __name__ == "__main__":
    run_standalone_create()
