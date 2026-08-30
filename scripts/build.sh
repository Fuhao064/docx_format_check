#!/bin/bash
# scripts/build.sh — macOS / Linux 桌面应用构建
# 产物: frontend/release/ 下的 .dmg / .AppImage
set -e

cd "$(dirname "$0")/.."
PROJECT_ROOT="$(pwd)"

echo "=== Scriptor 跨平台桌面应用构建 ($(uname -s)) ==="

# 优先使用 conda 环境（可选），否则使用当前 Python
if command -v conda >/dev/null 2>&1 && conda env list | grep -q "ALLinALL"; then
    echo "激活 Conda 环境 ALLinALL..."
    eval "$(conda shell.bash hook)"
    conda activate ALLinALL
fi

PYTHON="${PYTHON:-python3}"
echo "使用 Python: $($PYTHON --version 2>&1)"

echo "[1/4] 安装 Python 依赖..."
$PYTHON -m pip install -r requirements.txt pyinstaller

echo "[2/4] 构建前端..."
cd "$PROJECT_ROOT/frontend"
npm install
npm run build

echo "[3/4] 打包后端 (PyInstaller)..."
cd "$PROJECT_ROOT"
$PYTHON scripts/build_backend.py

echo "[4/4] 打包桌面应用 (electron-builder)..."
cd "$PROJECT_ROOT/frontend"
npm run electron:build

echo ""
echo "=== 构建完成 ==="
echo "输出目录: $PROJECT_ROOT/frontend/release"
