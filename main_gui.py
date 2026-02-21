# -*- coding: utf-8 -*-
"""
Scriptor GUI 启动入口
"""

import sys
import os
from pathlib import Path

# 确保项目根目录在路径中
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def check_dependencies():
    """检查依赖是否安装"""
    missing_deps = []

    try:
        import PyQt6
    except ImportError:
        missing_deps.append("PyQt6")

    try:
        import flask
    except ImportError:
        missing_deps.append("flask")

    try:
        import win32com
    except ImportError:
        if sys.platform == "win32":
            missing_deps.append("pywin32")

    return missing_deps


def main():
    """主函数"""
    # 检查依赖
    missing = check_dependencies()
    if missing:
        print(f"缺少依赖: {', '.join(missing)}")
        print("请运行: pip install PyQt6 flask pywin32")
        if sys.platform != "win32":
            print("(注: pywin32 仅在 Windows 上需要)")

    # 导入并启动 GUI
    try:
        from gui.main_window import main
        main()
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")


if __name__ == "__main__":
    main()
