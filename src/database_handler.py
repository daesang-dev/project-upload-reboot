import pandas as pd
from pathlib import Path
import sqlite3, warnings, traceback


# Tắt warning datavalidation khi đọc file Excel
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


class DatabaseHandler :
    def __init__(self, order_path, input_path, db_path):
        self.order_path = Path(order_path)
        self.input_path = Path(input_path)
        self.db_path = Path(db_path)

    def order_importer(self, config,):
        """
        Hàm này lặp qua tất cả các file trong thư mục chứa đơn hàng và trả về 1 dataframe
        """

        if not self.order_path.exists():
            return None

        excel_files = [f for f in self.order_path.glob("*.xlsx") if f.is_file()]
        if not excel_files:
            return None

        dfs = []
        rename_dict = {v['keywords'][0]: k for k, v in config.items() if v.get('use') == True}

        for f in excel_files:
            try:
                df = pd.read_excel(f, dtype="string")

                df_rename = df.rename(columns=rename_dict)

                existing_cols = [col for col in rename_dict.values() if col in df_rename.columns]
                df_select = df_rename[existing_cols].copy()

                dfs.append(df_select)
            except Exception as e:
                print(f"Lỗi khi xử lý file {f.name}: {e}")

        if not dfs:
            print("Không có dữ liệu hợp lệ để gộp.")
            return None

        combined_df = pd.concat(dfs, ignore_index=True)

        combined_df = combined_df.dropna(subset=["order_code"])

        dtype_map = {k: v["dtype"] for k, v in config.items() if v.get("use") and "dtype" in v}

        for col, dtype in dtype_map.items():
            if col in combined_df.columns:
                if dtype == "date":
                    combined_df[col] = pd.to_datetime(combined_df[col], errors='raise')
                elif dtype == "decimal":
                    combined_df[col] = pd.to_numeric(combined_df[col], errors='coerce')
                else:
                    combined_df[col] = combined_df[col].astype("string")
                    combined_df[col] = combined_df[col].str.replace(r"\.0$", "", regex=True)

        try:
            with sqlite3.connect(self.db_path) as conn:
                combined_df.to_sql(
                    name="stg_transactions",
                    con=conn,
                    if_exists="append",
                    index=False
                )
            print(f"Tải đơn hàng vào bảng staging thành công")
        except Exception as e:
            print(f"Lỗi khi tải đơn hàng vào bảng staging: {e}")

        return None

    def db_creator(self):
        """
        Mặc định luôn tạo mới lại schema khi chạy code
        """
        print("Đang đóng các kết nối hiện có")
        global conn
        try:
            conn.close()
        except:
            pass

        try:
            del conn
        except:
            pass

        if self.db_path.exists():
            print("Phát hiện database đã tồn tại, đang xoá...")
            self.db_path.unlink()

    def sql_executioner(self, init_db_script):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_key = ON")
            try:
                with open(init_db_script, "r", encoding="utf-8") as f:
                    sql = f.read()

                conn.executescript(sql)
                conn.commit()

                print(f"Thực thi file {init_db_script.stem} thành công")

            except Exception as e:

                print(f"Thông báo lỗi gốc: {e}")

                if hasattr(e, "orig"):
                    print(f"Lỗi chi tiết từ Database: {e.orig}")

                print("Vị trí dòng code bị crash (Traceback):")

                traceback.print_exc()

                print("-" * 50 + "\n")


    def input_importer(self, target_stg: str, config_dict: dict):
        """Sử dụng cấu hình từ input_config để đọc, chuẩn hóa dữ liệu và nạp vào

        SQLite.
        :param target_stg: Tên bảng staging cần xử lý (ví dụ: 'stg_product',
        'stg_promotion')
        :param config_dict: Toàn bộ dict 'input_config' chứa cấu hình
        """
        try:
            table_config = config_dict.get(target_stg)
            if not table_config:
                return

            sheet_name = table_config["sheet_name"]
            conf = table_config["conf"]

            df_raw = pd.read_excel(self.input_path, sheet_name=sheet_name)

            rename_mapping = {
                old_col: info["rename"] for old_col, info in conf.items()
            }

            df_rename = df_raw[list(rename_mapping.keys())].rename(
                columns=rename_mapping
            )

            for old_col, info in conf.items():
                new_col = info["rename"]
                dtype = info.get("dtype")

                if dtype == "date":
                    df_rename[new_col] = pd.to_datetime(
                        df_rename[new_col], errors="coerce", dayfirst=True
                    )
                elif dtype == "decimal":
                    df_rename[new_col] = pd.to_numeric(
                        df_rename[new_col], errors="coerce"
                    )
                else:
                    df_rename[new_col] = df_rename[new_col].astype("string")
                    df_rename[new_col] = df_rename[new_col].str.replace(".0", "", regex=False)

            with sqlite3.connect(database=self.db_path) as conn:
                cur = conn.cursor()
                print(f"Đang xoá dữ liệu cũ của bảng {target_stg}...")
                cur.execute(f"DELETE FROM {target_stg}")

                print(f"Đang import dữ liệu mới vào bảng {target_stg}...")
                df_rename.to_sql(
                    target_stg, index=False, con=conn, if_exists="append"
                )
                conn.commit()
                print(f"Import thành công bảng {target_stg}!\n")

        except Exception as e:

            print(f"LỖI TẠI BẢNG: {target_stg}")

            print(f"Thông báo lỗi gốc: {e}")

            if hasattr(e, "orig"):
                print(f"Lỗi chi tiết từ Database: {e.orig}")

            print("Vị trí dòng code bị crash (Traceback):")

            traceback.print_exc()