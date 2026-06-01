import pandas as pd
import sys, warnings
from src.database_handler import DatabaseHandler
from pathlib import Path
from src.conf.column_config import INPUT_CONFIG, ORDER_CONFIG


# Ignore specific openpyxl data validation warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

# Thiết lập đường dẫn
try:
    BASE_DIR = Path(__file__).cwd()
except:
    BASE_DIR = Path.cwd()

DATA_FOLDER = Path(BASE_DIR / "data")
INPUT_FILE = Path(DATA_FOLDER / "input_winmart.xlsx")
ORDER_FOLDER = Path(DATA_FOLDER / "raw_order")

SQL_SCRIPT = Path(BASE_DIR / "sql")
CREATE_SQL_SCRIPT = Path(SQL_SCRIPT / "create")
EXEC_SQL_SCRIPT = Path(SQL_SCRIPT / "exec")
DB_FILE = Path(BASE_DIR / "database.db")

OUTPUT_FOLDER = Path(BASE_DIR / "output")
ERR_REPORT_FILE = Path(OUTPUT_FOLDER / "Báo cáo.xlsx")
UPL_SAP_FILE = Path(OUTPUT_FOLDER / "SAP Upload File.xlsx")

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

debug_views = ['view_overlapped_promotions', 'view_duplicated_promotions', 'view_failed_price',
               'view_failed_moq', 'view_missing_barcode', 'view_missing_location_code']

# Kiểm tra xem có view debug nào trả lỗi không, nếu không thì tiếp tục import dữ liệu từ file order
has_error = False
error_sheet = {}
for view in debug_views:
    df, df_len = creator.fetch_data(view)
    if df_len > 0:
        error_sheet[view] = df
        has_error = True

with pd.ExcelWriter(ERR_REPORT_FILE) as w:
    if has_error:
        for view, df in error_sheet.items():
            df.to_excel(w, sheet_name=view[:30], index=False)
        sys.exit()
    else:
        creator.sql_executioner(EXEC_SQL_SCRIPT / "copy_transactions_table.sql")
        df = creator.fetch_data("view_data_result")
        df[0].to_excel(w, sheet_name="view_data_result", index=False)

# Sau khi import thành công dữ liệu đơn hàng vào bảng chính thì tạo file upload từ các view Header và line
upload_views = ['view_upload_header', 'view_upload_line']
with pd.ExcelWriter(UPL_SAP_FILE) as w:
    for view in upload_views:
        df = creator.fetch_data(view)
        if 'header' in view:
            df[0].to_excel(w, sheet_name="Header", index=False)
        else:
            df[0].to_excel(w, sheet_name="Line", index=False)

if UPL_SAP_FILE.is_file():
    print("Tạo file upload thành công")