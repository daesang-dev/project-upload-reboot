from src.database_handler import DatabaseHandler
from pathlib import Path
from src.conf.column_config import INPUT_CONFIG, ORDER_CONFIG


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

# Khởi tạo
creator = DatabaseHandler(order_path=ORDER_FOLDER, input_path=INPUT_FILE, db_path=DB_FILE)

# Tạo Database mới
creator.db_creator()

# Tạo schema và các view
creator.sql_executioner(init_db_script=CREATE_SQL_SCRIPT / "create_staging_tables.sql")
creator.sql_executioner(init_db_script=CREATE_SQL_SCRIPT / "create_main_tables.sql")
creator.sql_executioner(init_db_script=CREATE_SQL_SCRIPT / "create_result_views.sql")
creator.sql_executioner(init_db_script=CREATE_SQL_SCRIPT / "create_debug_views.sql")

# Đọc dữ liệu từ file input và import vào các bảng staging
for stg_table in INPUT_CONFIG.keys():
    try:
        creator.input_importer(
            stg_table,
            INPUT_CONFIG,
        )
    except Exception as e:
        print(e)

# Đọc dữ liệu từ đơn hàng và import vào staging
order_df = creator.order_importer(config=ORDER_CONFIG)

# Import dữ liệu từ các bảng staging sang bảng dimension
creator.sql_executioner(EXEC_SQL_SCRIPT / "staging_to_main.sql")