// frontend/electron/main.js
const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;

function createWindow() {
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

  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startPythonBackend() {
  const pythonPath = app.isPackaged
    ? path.join(process.resourcesPath, 'backend', 'app_v2.exe')
    : path.join(__dirname, '../../backend/app_v2.py');

  if (app.isPackaged) {
    pythonProcess = spawn(pythonPath, [], {
      cwd: path.dirname(pythonPath)
    });
  } else {
    pythonProcess = spawn('python', [pythonPath], {
      cwd: path.join(__dirname, '../../backend')
    });
  }

  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python: ${data}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python Error: ${data}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`Python exited with code ${code}`);
  });

  pythonProcess.on('error', (err) => {
    console.error('Failed to start Python backend:', err);
    dialog.showErrorBox(
      'Backend Error',
      `Failed to start the Python backend: ${err.message}`
    );
  });
}

// IPC 处理
ipcMain.handle('select-file', async (event, options) => {
  if (!mainWindow) return undefined;
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: options?.filters || [
      { name: 'Documents', extensions: ['docx', 'pdf'] }
    ]
  });
  return result.filePaths[0];
});

ipcMain.handle('save-file', async (event, options) => {
  if (!mainWindow) return undefined;
  const result = await dialog.showSaveDialog(mainWindow, {
    filters: options?.filters || [
      { name: 'Documents', extensions: ['docx'] }
    ]
  });
  return result.filePath;
});

// 应用生命周期
app.whenReady().then(() => {
  startPythonBackend();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    if (pythonProcess) {
      pythonProcess.kill();
    }
    app.quit();
  }
});
