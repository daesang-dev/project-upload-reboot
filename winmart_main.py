import sys, warnings, os, questionary
from pathlib import Path
import pandas as pd

from src.conf.column_config import INPUT_CONFIG, ORDER_CONFIG
from src.utils.dir_handler import file_cleaner, dir_maker
from src.database_handler import DatabaseHandler
from src.sap_automator import SAPAutomator


# Ignore specific openpyxl data validation warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

# Thiết lập đường dẫn
try:
    BASE_DIR = Path(__file__).cwd()
except:
    BASE_DIR = Path.cwd()

DATA_FOLDER = Path(BASE_DIR / "data")
INPUT_FILE = Path(DATA_FOLDER / "input_winmart.xlsx")
ORDER_FOLDER = Path(DATA_FOLDER / "order")

SQL_SCRIPT = Path(BASE_DIR / "sql")
CREATE_SQL_SCRIPT = Path(SQL_SCRIPT / "create")
EXEC_SQL_SCRIPT = Path(SQL_SCRIPT / "exec")
DB_FILE = Path(BASE_DIR / "database.db")

OUTPUT_FOLDER = Path(BASE_DIR / "output")


# Tạo đường dẫn input và output
dir_create = [OUTPUT_FOLDER, ORDER_FOLDER]
dir_maker(dir_create)
        
# Khởi tạo
creator = DatabaseHandler(order_path=ORDER_FOLDER, input_path=INPUT_FILE, db_path=DB_FILE)

# Tạo Database mới
creator.db_creator()

# Tạo schema và các view
creator.sql_executioner(CREATE_SQL_SCRIPT / "create_staging_tables.sql")
creator.sql_executioner(CREATE_SQL_SCRIPT / "create_main_tables.sql")
creator.sql_executioner(CREATE_SQL_SCRIPT / "create_result_views.sql")
creator.sql_executioner(CREATE_SQL_SCRIPT / "create_debug_views.sql")

# Đọc dữ liệu từ file input và import vào các bảng staging
for stg_table in INPUT_CONFIG.keys():
    try:
        creator.input_importer(
            stg_table,
            INPUT_CONFIG,
        )
    except Exception as e:
        print(e)

# Import dữ liệu từ các bảng staging sang bảng dimension
creator.sql_executioner(EXEC_SQL_SCRIPT / "copy_dim_tables.sql")

# Import dữ liệu từ file order vào stg_staging để các view debug trả về dữ liệu lỗi
creator.order_importer(config=ORDER_CONFIG)

# Tạo list các sheet chứa thông tin lỗi 
debug_views = ['view_overlapped_promotions', 'view_duplicated_promotions', 'view_missing_barcode', 'view_missing_location_code']

error_data = {}
has_error = False
for view in debug_views:
    df, df_len = creator.fetch_data(view)
    if df_len > 0:
        error_data[view] = df
        has_error = True

# Tạo file báo cáo
with pd.ExcelWriter(OUTPUT_FOLDER / "Báo cáo.xlsx") as w:
    # Nếu có lỗi thì ghi các view debug và dữ liệu của chúng ra file (chỉ những view nào có len > 0)
    if has_error and len(error_data) > 0:
        print("Phát hiện thông tin bị thiếu đang ghi vào file kết quả")
        for view, df in error_data.items():
            df.to_excel(w, sheet_name=view[:30], index=False)

    # Nếu không có các lỗi trên thì tiếp tục kiểm tra mối quan hệ giữa các bảng 
    else:
        table_violated = []
        print("Không phát hiện dữ liệu bị thiếu, đang copy dữ liệu đơn hàng từ bảng staging")
        foreign_key_violated, table_violated = creator.sql_executioner(EXEC_SQL_SCRIPT / "copy_transactions_table.sql")

        if foreign_key_violated:
            print(f"Mối quan hệ bị hỏng tại các bảng sau: {', '.join(table_violated)}")

            df_fk_errors = pd.DataFrame({"Bảng bị lỗi liên kết": table_violated})
            df_fk_errors.to_excel(w, sheet_name="FK_Violations", index=False)

        else:
            print("Các mối quan hệ trong database đều ổn, đang ghi kết quả vào file...")

            # Tạo list các sheet chứa kết quả
            result_views = ['view_failed_price', 'view_failed_moq', 'view_data_result']

            # Fetch dữ liệu từ các view kết quả 
            result_data = {}
            for view in result_views:
                df, df_len = creator.fetch_data(view)
                if df_len > 0:
                    result_data[view] = df

            for view, df in result_data.items():
                df.to_excel(w, sheet_name=view[:30], index=False)

if has_error or foreign_key_violated:
    print("\n[LỖI] Phát hiện lỗi dữ liệu! Vui lòng kiểm tra báo cáo.")
    answer = questionary.select(
        "Bạn muốn làm gì?",
        choices=['Xem báo cáo lỗi', 'Thoát']
    ).ask()
    
    if answer == 'Xem báo cáo lỗi':
        os.startfile(OUTPUT_FOLDER / "Báo cáo.xlsx")
    sys.exit()

# Sau khi import thành công dữ liệu đơn hàng vào bảng chính thì tạo file upload từ các view Header và line

upload_views = ['view_upload_header', 'view_upload_line']
with pd.ExcelWriter(OUTPUT_FOLDER / "SAP Upload File.xlsx") as w:
    for view in upload_views:
        df = creator.fetch_data(view)
        if 'header' in view:
            df[0].to_excel(w, sheet_name="Header", index=False)
        else:
            df[0].to_excel(w, sheet_name="Line", index=False)

sap_upload_file = OUTPUT_FOLDER / "SAP Upload File.xlsx"

def sap_upload():
    automator = SAPAutomator()
    if automator.start_sap():
        if automator.upload_excel(str(sap_upload_file.absolute())):
            automator.create_sales_order()
            file_cleaner(OUTPUT_FOLDER)
            
        else:
            print("[LỖI] Không thể upload file lên SAP.")
    else:
        print("[LỖI] Không thể khởi động hoặc đăng nhập SAP.")

    return None

if sap_upload_file.is_file():
    print("Tạo file upload thành công")
    
    # Lựa chọn bước tiếp theo
    choice = questionary.select(
        "Bạn muốn làm gì tiếp theo?",
        choices=['Xem báo cáo', 'Tiếp tục upload', 'Thoát']
    ).ask()

    if choice == 'Xem báo cáo':
        print(f"Đang mở file báo cáo: {OUTPUT_FOLDER / 'Báo cáo.xlsx'}")
        os.startfile(OUTPUT_FOLDER / "Báo cáo.xlsx")

        upload_choice = questionary.select(
            "Bạn có muốn upload luôn không?",
            choices=['Có', 'Không']
        ).ask()

        if upload_choice == "Có":
            file_cleaner(ORDER_FOLDER)
            sap_upload()
        else:
            sys.exit()

    elif choice == "Tiếp tục upload":
        file_cleaner(ORDER_FOLDER)
        sap_upload()

    else:
        sys.exit()
    
    # Tích hợp tự động hóa SAP
    print("\n Đang khởi động quy trình tự động hóa SAP")