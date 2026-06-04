from pathlib import Path

# Tạo đường dẫn input và output
def dir_maker(dir_paths: list):
    for path in dir_paths:
        file_path = Path(path)
        if not file_path.exists():
            file_path.mkdir(parents=True, exist_ok=True)

def file_cleaner(dir_path):
    for file in dir_path.iterdir():
        file.unlink()