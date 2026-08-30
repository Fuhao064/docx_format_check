@echo off
chcp 65001 >nul
echo ====================================
echo   Scriptor 跨平台桌面应用打包 (Windows)
echo ====================================
echo.

REM 可选参数: /fast 跳过依赖安装
set FAST_MODE=0
if "%1"=="/fast" set FAST_MODE=1
if "%1"=="-f" set FAST_MODE=1

where python >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+ 并加入 PATH
    pause
    exit /b 1
)

if %FAST_MODE%==0 (
    echo [1/4] 安装 Python 依赖...
    python -m pip install -r requirements.txt pyinstaller || goto :fail
) else (
    echo [1/4] 快速模式: 跳过依赖安装
)

echo.
echo [2/4] 构建 React/Vue 前端...
cd /d "%~dp0frontend"
call npm install || goto :fail
call npm run build || goto :fail

echo.
echo [3/4] 用 PyInstaller 打包后端...
cd /d "%~dp0"
python scripts\build_backend.py || goto :fail

echo.
echo [4/4] 用 electron-builder 生成安装包...
cd /d "%~dp0frontend"
call npm run electron:build || goto :fail

echo.
echo ====================================
echo   打包成功!
echo ====================================
echo 安装包输出: frontend\release\
echo.
goto :eof

:fail
echo.
echo [错误] 打包失败，请检查上方日志
pause
exit /b 1
