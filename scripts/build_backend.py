# scripts/build_backend.py
import PyInstaller.__main__
import os
import sys

def build_backend():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_dir = os.path.join(project_root, 'backend')

    args = [
        'app_v2.py',
        '--name=scriptor-backend',
        '--onedir',
        '--console',
        f'--distpath={os.path.join(project_root, "frontend", "resources", "backend")}',
        f'--workpath={os.path.join(project_root, "build", "backend")}',
        f'--specpath={os.path.join(project_root, "build")}',
        f'--add-data={os.path.join(backend_dir, "config.json")};.',
        '--hidden-import=uvicorn',
        '--hidden-import=uvicorn.logging',
        '--hidden-import=uvicorn.loops',
        '--hidden-import=uvicorn.loops.auto',
        '--hidden-import=uvicorn.protocols',
        '--hidden-import=uvicorn.protocols.http',
        '--hidden-import=uvicorn.protocols.http.auto',
        '--hidden-import=uvicorn.protocols.websockets',
        '--hidden-import=uvicorn.protocols.websockets.auto',
        '--hidden-import=uvicorn.lifespan',
        '--hidden-import=uvicorn.lifespan.on',
        '--clean',
        '--noconfirm'
    ]

    PyInstaller.__main__.run(args)

if __name__ == '__main__':
    build_backend()
