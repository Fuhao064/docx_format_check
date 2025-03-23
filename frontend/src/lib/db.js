import Dexie from 'dexie';

// 创建数据库及表结构
const db = new Dexie('scriptorDB');

// 定义数据库结构
db.version(1).stores({
  appState: 'id, lastUpdated',
  files: 'id, name, path, type, lastUpdated',
  messages: '++id, content, sender, timestamp'
});

// 升级数据库以添加formatErrors表
db.version(2).stores({
  appState: 'id, lastUpdated',
  files: 'id, name, path, type, lastUpdated',
  messages: '++id, content, sender, timestamp',
  formatErrors: '++id, message, location, timestamp'
}).upgrade(tx => {
  console.log('升级到数据库版本2，添加formatErrors表');
});

// 初始化一个默认记录作为应用状态存储
const initializeDB = async () => {
  const appStateCount = await db.appState.count();
  if (appStateCount === 0) {
    await db.appState.put({
      id: 1,
      hasUploadedFile: false,
      hasUploadedFormat: false,
      uploadedFileName: '',
      formattedFilePath: '',
      currentDocumentPath: '',
      currentConfigPath: '',
      currentStep: 0,
      processingComplete: false,
      lastUpdated: new Date()
    });
  }
};

// 获取应用状态
const getAppState = async () => {
  await initializeDB();
  return await db.appState.get(1);
};

// 更新应用状态
const updateAppState = async (stateData) => {
  const current = await getAppState();
  await db.appState.update(1, {
    ...current,
    ...stateData,
    lastUpdated: new Date()
  });
  return await getAppState();
};

// 重置应用状态
const resetAppState = async () => {
  await db.appState.update(1, {
    hasUploadedFile: false,
    hasUploadedFormat: false,
    uploadedFileName: '',
    formattedFilePath: '',
    currentDocumentPath: '',
    currentConfigPath: '',
    currentStep: 0,
    processingComplete: false,
    lastUpdated: new Date()
  });
  return await getAppState();
};

// 保存上传的文件信息
const saveFileInfo = async (fileInfo) => {
  const id = Date.now().toString();
  await db.files.put({
    id,
    ...fileInfo,
    lastUpdated: new Date()
  });
  return id;
};

// 获取文件信息
const getFileInfo = async (id) => {
  return await db.files.get(id);
};

// 删除文件信息
const deleteFileInfo = async (id) => {
  await db.files.delete(id);
};

// 更新文件信息
const updateFileInfo = async (id, fileInfo) => {
  const current = await getFileInfo(id);
  if (!current) return null;
  
  await db.files.update(id, {
    ...current,
    ...fileInfo,
    lastUpdated: new Date()
  });
  return await getFileInfo(id);
};

// 保存消息
const saveMessage = async (message) => {
  const id = await db.messages.add({
    ...message,
    timestamp: message.timestamp || new Date()
  });
  return id;
};

// 批量保存消息
const saveMessages = async (messages) => {
  return await db.messages.bulkAdd(messages.map(msg => ({
    ...msg,
    timestamp: msg.timestamp || new Date()
  })));
};

// 获取所有消息
const getAllMessages = async () => {
  return await db.messages.toArray();
};

// 清空所有消息
const clearAllMessages = async () => {
  await db.messages.clear();
};

// 删除消息
const deleteMessage = async (id) => {
  await db.messages.delete(id);
};

// 保存格式错误信息
const saveFormatErrors = async (errors) => {
  try {
    // 清空现有错误
    await db.formatErrors.clear();
    
    // 没有错误时直接返回
    if (!errors || errors.length === 0) return;
    
    // 将错误存储为单独的记录
    const simplifiedErrors = errors.map(err => ({
      message: String(err.message || '未知错误'),
      location: err.location ? String(err.location) : null,
      timestamp: new Date()
    }));
    
    // 批量添加错误
    await db.formatErrors.bulkAdd(simplifiedErrors);
  } catch (error) {
    console.error('保存格式错误时出错:', error);
  }
};

// 获取格式错误信息
const getFormatErrors = async () => {
  try {
    return await db.formatErrors.toArray();
  } catch (error) {
    console.error('获取格式错误时出错:', error);
    return [];
  }
};

export {
  db,
  initializeDB,
  getAppState,
  updateAppState,
  resetAppState,
  saveFileInfo,
  getFileInfo,
  deleteFileInfo,
  updateFileInfo,
  saveMessage,
  saveMessages,
  getAllMessages,
  clearAllMessages,
  deleteMessage,
  saveFormatErrors,
  getFormatErrors
};
