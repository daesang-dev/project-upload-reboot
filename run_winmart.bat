@echo off
SETLOCAL EnableDelayedExpansion

:: Kiểm tra quyền Administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :run_script
) else (
    echo [INFO] Dang yeu cau quyen Administrator...
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

:run_script
:: Chuyển về đúng thư mục chứa file .bat này (Rất quan trọng khi chạy quyền Admin)
cd /d "%~dp0"

SET "ENV_NAME=pydata"
SET "PY_FILE=winmart_main.py"

:: Danh sach cac duong dan Conda pho bien
SET "CONDA_PATHS[0]=%USERPROFILE%\miniconda3"
SET "CONDA_PATHS[1]=C:\Users\Admin\miniconda3"
SET "CONDA_PATHS[2]=%USERPROFILE%\anaconda3"
SET "CONDA_PATHS[3]=C:\miniconda3"
SET "CONDA_PATHS[4]=C:\anaconda3"
SET "CONDA_PATHS[5]=%ALLUSERSPROFILE%\miniconda3"
SET "CONDA_PATHS[6]=%ALLUSERSPROFILE%\anaconda3"

SET "CONDA_BASE_PATH="

echo [1/3] Dang tim kiem Conda trong he thong...
FOR /L %%i IN (0,1,6) do (
    SET "TEST_PATH=!CONDA_PATHS[%%i]!"
    IF EXIST "!TEST_PATH!\Scripts\activate.bat" (
        SET "CONDA_BASE_PATH=!TEST_PATH!"
        echo [OK] Da tim thay Conda tai: !CONDA_BASE_PATH!
        GOTO FOUND
    )
)

:NOT_FOUND
echo [LOI] Khong tim thay Conda trong cac thu muc mac dinh.
echo Hay kiem tra lai duong dan cai dat Conda cua ban hoac cap nhat file .bat nay.
pause
exit /b

:FOUND
echo [2/3] Dang kiem tra moi truong: %ENV_NAME%

:: Xác định đường dẫn trực tiếp đến file python.exe của môi trường
SET "ENV_PYTHON_EXE=!CONDA_BASE_PATH!\envs\%ENV_NAME%\python.exe"

:: Trường hợp nếu môi trường cần kiểm tra là môi trường 'base'
if "%ENV_NAME%"=="base" (
    SET "ENV_PYTHON_EXE=!CONDA_BASE_PATH!\python.exe"
)

IF NOT EXIST "!ENV_PYTHON_EXE!" (
    echo [LOI] Khong the tim thay moi truong '%ENV_NAME%' tai: !ENV_PYTHON_EXE!
    echo Vui long dam bao ban da tao moi truong bang lenh: 
    echo conda env create -f env/upload_project.yml
    pause
    exit /b
)

echo [3/3] Dang chay script bang Python cua moi truong '%ENV_NAME%'...
echo ------------------------------------------------------------------

:: Chạy trực tiếp file python của môi trường, bỏ qua bước 'call activate' loằng ngoằng
"!ENV_PYTHON_EXE!" "%PY_FILE%"

if %errorlevel% neq 0 (
    echo.
    echo ------------------------------------------------------------------
    echo [LOI] Co loi xay ra trong qua trinh thuc thi script Python (Mã loi: %errorlevel%).
) else (
    echo.
    echo ------------------------------------------------------------------
    echo [THANH CONG] Pipeline da hoan thanh xu ly.
)

ENDLOCAL
pause