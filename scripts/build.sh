#!/bin/bash
# scripts/build.sh

set -e

echo "=== Scriptor 构建脚本 ==="

# 检查 Conda 环境
echo "检查 Conda 环境..."
if ! conda info --envs | grep -q "ALLinALL"; then
    echo "错误: ALLinALL Conda 环境不存在"
    echo "请先创建环境: conda env create -f environment.yml"
    exit 1
fi

# 激活 Conda 环境
echo "激活 Conda 环境..."
eval "$(conda shell.bash hook)"
conda activate ALLinALL

# 安装 Python 依赖
echo "安装 Python 依赖..."
pip install -r requirements.txt

# 打包 Python 后端
echo "打包 Python 后端..."
python scripts/build_backend.py

# 安装前端依赖
echo "安装前端依赖..."
cd frontend
npm install

# 构建前端
echo "构建前端..."
npm run build

# 打包 Electron 应用
echo "打包 Electron 应用..."
npm run electron:build

echo "=== 构建完成 ==="
echo "输出目录: frontend/release"
