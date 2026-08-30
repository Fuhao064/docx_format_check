// frontend/electron/main.js
// 跨平台桌面外壳：拉起本地后端（打包后为 PyInstaller 产物，开发时为 python app.py），
// 等待健康检查通过后以同源方式加载页面，保证相对路径 /api 与 WebSocket 正常工作。
const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const http = require('http');
const { spawn } = require('child_process');

let mainWindow = null;
let backendProcess = null;
let backendPort = Number(process.env.SCRIPTOR_PORT) || 8080;
const DEV_URL = process.env.ELECTRON_START_URL || 'http://localhost:3000';

const gotSingleInstanceLock = app.requestSingleInstanceLock();
if (!gotSingleInstanceLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });
}

function createWindow(url) {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    },
    title: 'Scriptor - 智能文档格式检查器'
  });

  mainWindow.loadURL(url);

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function backendBinaryPath() {
  const exeName = process.platform === 'win32' ? 'scriptor-backend.exe' : 'scriptor-backend';
  // PyInstaller --onedir 产物: resources/backend/scriptor-backend/<binary>
  return path.join(process.resourcesPath, 'backend', 'scriptor-backend', exeName);
}

function startPythonBackend(port) {
  const env = {
    ...process.env,
    SCRIPTOR_PORT: String(port),
    SCRIPTOR_HOST: '127.0.0.1',
    SCRIPTOR_DATA_DIR: app.getPath('userData'),
    PYTHONUNBUFFERED: '1'
  };

  if (app.isPackaged) {
    const binary = backendBinaryPath();
    backendProcess = spawn(binary, [], {
      cwd: path.dirname(binary),
      env,
      windowsHide: true
    });
  } else {
    const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
    const entry = path.join(__dirname, '..', '..', 'backend', 'app.py');
    backendProcess = spawn(pythonCmd, [entry], {
      cwd: path.dirname(entry),
      env
    });
  }

  backendProcess.stdout.on('data', (data) => {
    console.log(`[backend] ${data}`);
  });

  backendProcess.stderr.on('data', (data) => {
    console.error(`[backend] ${data}`);
  });

  backendProcess.on('error', (err) => {
    console.error('Failed to start Python backend:', err);
    dialog.showErrorBox(
      'Backend Error',
      `Failed to start the local backend: ${err.message}`
    );
  });
}

function isBackendUp(port) {
  return new Promise((resolve) => {
    const req = http.get({ host: '127.0.0.1', port, path: '/api/health', timeout: 1500 }, (res) => {
      res.resume();
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.on('timeout', () => {
      req.destroy();
      resolve(false);
    });
  });
}

async function waitForBackend(port, timeoutMs = 60000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await isBackendUp(port)) return true;
    await new Promise((r) => setTimeout(r, 500));
  }
  return false;
}

async function findFreePort(start) {
  const net = require('net');
  for (let port = start; port < start + 50; port += 1) {
    const free = await new Promise((resolve) => {
      const server = net.createServer();
      server.once('error', () => resolve(false));
      server.once('listening', () => server.close(() => resolve(true)));
      server.listen(port, '127.0.0.1');
    });
    if (free) return port;
  }
  return start;
}

app.whenReady().then(async () => {
  if (!app.isPackaged) {
    // 开发模式：后端随 vite 代理约定固定 8080，页面走 vite 热更新
    startPythonBackend(8080);
    createWindow(DEV_URL);
    return;
  }

  backendPort = await findFreePort(backendPort);
  startPythonBackend(backendPort);

  const up = await waitForBackend(backendPort);
  if (!up) {
    dialog.showErrorBox(
      'Backend Error',
      `Local backend did not start on port ${backendPort}. Please restart the application.`
    );
    app.quit();
    return;
  }
  createWindow(`http://127.0.0.1:${backendPort}`);

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow(`http://127.0.0.1:${backendPort}`);
    }
  });
});

function stopBackend() {
  if (backendProcess && backendProcess.pid) {
    try {
      backendProcess.kill();
    } catch (err) {
      console.error('Failed to stop backend:', err);
    }
    backendProcess = null;
  }
}

app.on('before-quit', stopBackend);

app.on('window-all-closed', () => {
  stopBackend();
  app.quit();
});
