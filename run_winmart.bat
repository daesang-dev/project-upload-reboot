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

SET "PY_FILE=winmart_main.py"
SET "VENV_DIR=.venv"

echo [1/2] Dang kiem tra moi truong ao (.venv)...

:: Xác định đường dẫn trực tiếp đến file python.exe của thư mục .venv cùng cấp
SET "ENV_PYTHON_EXE=%~dp0%VENV_DIR%\Scripts\python.exe"

IF NOT EXIST "!ENV_PYTHON_EXE!" (
    echo [LOI] Khong the tim thay moi truong '.venv' tai: !ENV_PYTHON_EXE!
    echo Vui long dam bao ban da tao moi truong ao bang lenh: 
    echo python -m venv %VENV_DIR%
    echo Hoac dam bao file .bat nay dat dung canh thu muc %VENV_DIR%
    pause
    exit /b
)

echo [OK] Da tim thay .venv hop le.
echo [2/2] Dang chay script bang Python cua moi truong '.venv'...
echo ------------------------------------------------------------------

:: Chạy trực tiếp file python bằng đường dẫn tuyệt đối
"!ENV_PYTHON_EXE!" "%~dp0%PY_FILE%"

if %errorlevel% neq 0 (
    echo.
    echo ------------------------------------------------------------------
    echo [LOI] Co loi xay ra trong qua trinh thuc thi script Python (Ma loi: %errorlevel%).
) else (
    echo.
    echo ------------------------------------------------------------------
    echo [THANH CONG] Pipeline da hoan thanh xu ly.
)

ENDLOCAL
pause