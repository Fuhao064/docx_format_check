@echo off
chcp 65001 >nul
echo ====================================
echo   Scriptor 打包脚本
echo ====================================
echo.

REM 检查是否为快速模式
set FAST_MODE=0
if "%1"=="fast" set FAST_MODE=1
if "%1"=="-f" set FAST_MODE=1

if %FAST_MODE%==1 (
    echo [快速模式] 跳过检查、清理和依赖验证
    echo.
    goto FAST_BUILD
)

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [1/6] 检查依赖...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo 正在安装 PyInstaller...
    pip install pyinstaller
)

pip show PyQt6 >nul 2>&1
if errorlevel 1 (
    echo 正在安装 PyQt6...
    pip install PyQt6
)

echo.
echo [2/6] 更新 requirements.txt...
(
echo flask==3.0.0
echo flask-cors==4.0.0
echo flask-socketio==5.3.6
echo pywin32>=305; sys_platform == "win32"
echo pandas
echo openpyxl
echo python-multipart
echo pydantic
echo python-dotenv
echo PyQt6>=6.0.0
echo pyinstaller>=6.0.0
) > requirements.txt

echo.
echo [3/6] 检查前端构建...
if exist "frontend\dist" (
    echo 前端构建已存在
) else (
    echo 警告: 未找到前端构建 (frontend/dist)
    echo 如需包含前端，请先在 frontend 目录运行: npm install ^&^& npm run build
)

echo.
echo [4/6] 清理旧的构建...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo.
echo [5/6] 开始打包...
pyinstaller --clean Scriptor.spec

goto BUILD_COMPLETE

:FAST_BUILD
echo [快速模式] 开始打包 (保留缓存)...
pyinstaller Scriptor.spec

:BUILD_COMPLETE
if errorlevel 1 (
    echo.
    echo [错误] 打包失败!
    pause
    exit /b 1
)

echo.
echo [6/6] 打包完成!
echo.
echo 可执行文件位置: dist\Scriptor.exe
echo.
echo ====================================
echo   打包成功!
echo ====================================
echo.
echo 使用提示:
echo   - 首次打包或发布时: build.bat
echo   - 开发调试快速打包: build.bat fast
echo.
pause
