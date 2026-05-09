// frontend/electron/preload.js
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  selectFile: (options) => ipcRenderer.invoke('select-file', options),
  saveFile: (options) => ipcRenderer.invoke('save-file', options),
  platform: process.platform,
  isElectron: true
});
