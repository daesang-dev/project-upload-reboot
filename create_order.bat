@echo off
SETLOCAL EnableDelayedExpansion

:: Kiểm tra quyền Administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :run_script
) else (
    echo [INFO] Dang yeu cau quyen Administrator...
    powershell -Command "Start-Process cmd -ArgumentList '/k \"""%~f0\"""' -Verb RunAs"
    exit /b
)

:run_script
:: Chuyển về đúng thư mục chứa file .bat này
cd /d "%~dp0"

SET "PY_FILE=run_only_create.py"

echo [1/2] Dang kiem tra cong cu UV...
:: Kiểm tra xem UV đã được cài đặt trên máy chưa
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [LOI] Khong tim thay 'uv' tren he thong.
    echo Vui long cai dat uv bang lenh: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    pause
    exit /b
)

echo [OK] Da tim thay UV.
echo [2/2] Dang chay script bang UV...
echo ------------------------------------------------------------------

:: Lệnh 'uv run' sẽ tự động kích hoạt/tạo môi trường ảo và chạy file python
uv run python "%~dp0%PY_FILE%"

if %errorlevel% neq 0 (
    echo.
    echo ------------------------------------------------------------------
    echo [LOI] Co loi xay ra trong qua trinh thuc thi bằng UV (Ma loi: %errorlevel%).
) else (
    echo.
    echo ------------------------------------------------------------------
    echo [THANH CONG] Pipeline da hoan thanh xu ly bang UV.
)

ENDLOCAL
pause