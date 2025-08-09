@echo off
chcp 65001
echo 正在检查运行环境...

REM 检查虚拟环境是否存在
if exist ".\.venv\Scripts\python.exe" (
    echo 检测到虚拟环境，使用虚拟环境运行...
    start /B .\.venv\Scripts\python.exe main.py
    exit /b
)

REM 检查系统Python是否可用
where python >nul 2>&1
if %errorlevel% equ 0 (
    echo 未检测到虚拟环境，使用系统Python运行...
    start /B python main.py
    exit /b
)

echo 未检测到Python环境
echo 是否要下载Python安装包？(Y/N)
set /p choice=
if /i "%choice%"=="y" (
    echo 正在下载Python安装包...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe' -OutFile 'python-installer.exe'"
    if exist "python-installer.exe" (
        echo 下载完成，请运行python-installer.exe安装Python
    ) else (
        echo 下载失败，请手动访问 https://www.python.org/downloads/ 下载安装
    )
) else (
    echo 请先安装Python环境后再运行本程序
)
pause