# scripts/build_backend.py
"""用 PyInstaller 打包 Flask 后端（backend/app.py），产物供 Electron 外壳拉起。

用法（在对应平台执行即可得到该平台的可执行文件）:
    python scripts/build_backend.py
"""
import PyInstaller.__main__
import os

def build_backend():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_dir = os.path.join(project_root, 'backend')
    frontend_dist = os.path.join(project_root, 'frontend', 'dist')
    sep = ';' if os.name == 'nt' else ':'

    args = [
        os.path.join(backend_dir, 'app.py'),
        '--name=scriptor-backend',
        '--onedir',
        '--console',
        f'--distpath={os.path.join(project_root, "frontend", "resources", "backend")}',
        f'--workpath={os.path.join(project_root, "build", "backend")}',
        f'--specpath={os.path.join(project_root, "build")}',
        f'--add-data={os.path.join(backend_dir, "config.json")}{sep}.',
        f'--add-data={frontend_dist}{sep}frontend_dist',
        f'--paths={backend_dir}',
        '--hidden-import=preparation.pdf_to_docx',
        '--hidden-import=preparation.extractors.word_com_extractor',
        '--hidden-import=preparation.extractors.python_docx_extractor',
        '--hidden-import=preparation.extractors.pdf_extractor',
        '--clean',
        '--noconfirm'
    ]

    if os.name == 'nt':
        # Word COM 集成为可选能力，仅在 Windows 上随包
        args.append('--hidden-import=win32com.client')
        args.append('--hidden-import=pythoncom')

    # LLM 密钥随包（agents/setting.py 按 __file__ 相对路径解析，需落在 _internal/agents/ 下）
    keys_file = os.path.join(backend_dir, 'agents', 'keys.json')
    if os.path.exists(keys_file):
        args.append(f'--add-data={keys_file}{sep}agents')

    PyInstaller.__main__.run(args)

if __name__ == '__main__':
    build_backend()
