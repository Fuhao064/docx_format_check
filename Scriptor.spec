# -*- mode: python ; coding: utf-8 -*-
"""
Scriptor PyInstaller 配置文件
用于打包为 Windows 可执行文件
"""

import os
import sys

block_cipher = None

# 项目根目录 - 使用 spec 文件所在目录
spec_dir = os.path.dirname(os.path.abspath(SPEC))

# 收集数据文件
datas = [
    (os.path.join(spec_dir, 'backend', 'utils', 'config.json'), 'backend/utils'),
    (os.path.join(spec_dir, 'backend', 'standards', 'official_config.json'), 'backend/standards'),
]

# 如果存在前端构建文件，也添加
frontend_dist = os.path.join(spec_dir, 'frontend', 'dist')
if os.path.exists(frontend_dist):
    datas.append((frontend_dist, 'frontend/dist'))

# 隐藏导入
hiddenimports = [
    'win32com',
    'win32com.client',
    'pywintypes',
    'pythoncom',
    'flask',
    'flask_cors',
    'flask_socketio',
    'pydantic',
    'pandas',
    'openpyxl',
]

# 排除不需要的模块以加快打包速度
excludes = [
    'tkinter',
    'matplotlib',
    'unittest',
    'email',
    'http.server',
    'socketserver',
    'pydoc',
    'pdb',
    'doctest',
    'optparse',
    'pickletools',
    'setuptools',
    'pytest',
    'hypothesis',
    'xmlrpc',
    'multiprocessing',
]

a = Analysis(
    ['main_gui.py'],
    pathex=[spec_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Scriptor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,           # 启用符号剥离以减小体积
    upx=False,            # 禁用 UPX 压缩以加快打包速度
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
