@echo off
chcp 65001
echo 正在准备安装项目依赖...

REM 检查虚拟环境
if exist ".\.venv\Scripts\python.exe" (
    echo 检测到虚拟环境，将在虚拟环境中安装依赖...
    set PYTHON_CMD=.\.venv\Scripts\python.exe
) else (
    echo 未检测到虚拟环境，将在系统Python中安装依赖...
    where python >nul 2>&1
    if %errorlevel% neq 0 (
        echo 错误：未检测到Python环境
        echo 请先安装Python或创建虚拟环境
        pause
        exit /b 1
    )
    set PYTHON_CMD=python
)

REM 检查requirements.txt
if exist "requirements.txt" (
    echo 检测到requirements.txt，正在安装所有依赖...
    %PYTHON_CMD% -m pip install -r requirements.txt --upgrade
    if %errorlevel% neq 0 (
        echo 依赖安装失败
        pause
        exit /b 1
    )
    
    echo.
    echo 依赖安装完成
    echo 已从requirements.txt安装所有依赖
    pause
    exit /b
)

REM 如果没有requirements.txt，使用原有逻辑
echo 未找到requirements.txt，将安装核心依赖...

echo 正在安装核心依赖 (PySide6和Pillow)...
%PYTHON_CMD% -m pip install PySide6 Pillow --upgrade
if %errorlevel% neq 0 (
    echo 核心依赖安装失败
    pause
    exit /b 1
)

echo.
echo 是否要安装可选依赖OpenCV? (Y/N)
set /p choice=
if /i "%choice%"=="y" (
    echo 正在安装OpenCV...
    %PYTHON_CMD% -m pip install opencv-python
    if %errorlevel% neq 0 (
        echo OpenCV安装失败
    )
)

echo.
echo 依赖安装完成
echo 主要依赖已安装:
echo - PySide6
echo - Pillow
if "%choice%"=="y" echo - OpenCV
pause
