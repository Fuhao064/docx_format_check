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

// 升级数据库以支持多任务管理
db.version(3).stores({
  appState: 'id, lastUpdated, currentTaskId',
  tasks: 'id, title, createdAt, lastUpdated',
  taskState: 'id, taskId, hasUploadedFile, hasUploadedFormat, uploadedFileName, formattedFilePath, currentDocumentPath, currentConfigPath, currentStep, processingComplete, lastUpdated',
  files: 'id, taskId, name, path, type, lastUpdated',
  messages: '++id, taskId, content, sender, timestamp',
  formatErrors: '++id, taskId, message, location, timestamp'
}).upgrade(async tx => {
  console.log('升级到数据库版本3，支持多任务管理');
  
  // 获取当前应用状态
  const oldAppState = await tx.appState.get(1);
  
  if (oldAppState) {
    // 创建默认任务
    const defaultTaskId = Date.now().toString();
    
    // 保存默认任务
    await tx.tasks.add({
      id: defaultTaskId,
      title: oldAppState.uploadedFileName || '默认任务',
      createdAt: new Date(),
      lastUpdated: new Date()
    });
    
    // 将原有状态迁移到任务状态
    await tx.taskState.add({
      id: Date.now().toString(),
      taskId: defaultTaskId,
      hasUploadedFile: oldAppState.hasUploadedFile || false,
      hasUploadedFormat: oldAppState.hasUploadedFormat || false,
      uploadedFileName: oldAppState.uploadedFileName || '',
      formattedFilePath: oldAppState.formattedFilePath || '',
      currentDocumentPath: oldAppState.currentDocumentPath || '',
      currentConfigPath: oldAppState.currentConfigPath || '',
      currentStep: oldAppState.currentStep || 0,
      processingComplete: oldAppState.processingComplete || false,
      lastUpdated: new Date()
    });
    
    // 更新应用状态，记录当前活动的任务ID
    await tx.appState.update(1, {
      ...oldAppState,
      currentTaskId: defaultTaskId,
      lastUpdated: new Date()
    });
    
    // 将消息关联到默认任务
    const messages = await tx.messages.toArray();
    for (const message of messages) {
      await tx.messages.update(message.id, {
        ...message,
        taskId: defaultTaskId
      });
    }
    
    // 将格式错误关联到默认任务
    const errors = await tx.formatErrors.toArray();
    for (const error of errors) {
      await tx.formatErrors.update(error.id, {
        ...error,
        taskId: defaultTaskId
      });
    }
    
    // 将文件关联到默认任务
    const files = await tx.files.toArray();
    for (const file of files) {
      await tx.files.update(file.id, {
        ...file,
        taskId: defaultTaskId
      });
    }
  }
});

// 初始化数据库
const initializeDB = async () => {
  const appStateCount = await db.appState.count();
  if (appStateCount === 0) {
    // 创建默认任务
    const defaultTaskId = Date.now().toString();
    
    // 创建应用状态
    await db.appState.put({
      id: 1,
      currentTaskId: defaultTaskId,
      lastUpdated: new Date()
    });
    
    // 创建默认任务
    await db.tasks.put({
      id: defaultTaskId,
      title: '默认任务',
      createdAt: new Date(),
      lastUpdated: new Date()
    });
    
    // 创建任务状态
    await db.taskState.put({
      id: Date.now().toString(),
      taskId: defaultTaskId,
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

// 获取当前任务ID
const getCurrentTaskId = async () => {
  const appState = await getAppState();
  return appState.currentTaskId;
};

// 切换当前任务
const switchTask = async (taskId) => {
  await updateAppState({ currentTaskId: taskId });
  return await getTaskState(taskId);
};

// 获取所有任务
const getAllTasks = async () => {
  return await db.tasks.toArray();
};

// 创建新任务
const createTask = async (title = '新任务') => {
  const taskId = Date.now().toString();
  
  // 创建任务
  await db.tasks.put({
    id: taskId,
    title: title,
    createdAt: new Date(),
    lastUpdated: new Date()
  });
  
  // 创建任务状态
  await db.taskState.put({
    id: Date.now().toString(),
    taskId: taskId,
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
  
  // 切换到新任务
  await switchTask(taskId);
  
  return taskId;
};

// 删除任务
const deleteTask = async (taskId) => {
  // 获取当前应用状态
  const appState = await getAppState();
  
  // 删除任务相关数据
  await db.taskState.where('taskId').equals(taskId).delete();
  await db.messages.where('taskId').equals(taskId).delete();
  await db.formatErrors.where('taskId').equals(taskId).delete();
  await db.files.where('taskId').equals(taskId).delete();
  await db.tasks.delete(taskId);
  
  // 如果删除的是当前任务，切换到其他任务
  if (appState.currentTaskId === taskId) {
    // 获取剩余任务
    const remainingTasks = await getAllTasks();
    
    if (remainingTasks.length > 0) {
      // 切换到第一个可用任务
      await switchTask(remainingTasks[0].id);
    } else {
      // 没有任务了，创建新任务
      await createTask();
    }
  }
  
  return true;
};

// 获取任务信息
const getTask = async (taskId) => {
  return await db.tasks.get(taskId);
};

// 更新任务信息
const updateTask = async (taskId, taskData) => {
  const task = await getTask(taskId);
  if (!task) return null;
  
  await db.tasks.update(taskId, {
    ...task,
    ...taskData,
    lastUpdated: new Date()
  });
  
  return await getTask(taskId);
};

// 获取当前任务状态
const getCurrentTaskState = async () => {
  const taskId = await getCurrentTaskId();
  return await getTaskState(taskId);
};

// 获取指定任务状态
const getTaskState = async (taskId) => {
  const taskState = await db.taskState.where('taskId').equals(taskId).first();
  
  if (!taskState) {
    // 如果找不到任务状态，创建默认状态
    const newTaskState = {
      id: Date.now().toString(),
      taskId: taskId,
      hasUploadedFile: false,
      hasUploadedFormat: false,
      uploadedFileName: '',
      formattedFilePath: '',
      currentDocumentPath: '',
      currentConfigPath: '',
      currentStep: 0,
      processingComplete: false,
      lastUpdated: new Date()
    };
    
    await db.taskState.put(newTaskState);
    return newTaskState;
  }
  
  return taskState;
};

// 更新任务状态
const updateTaskState = async (taskId, stateData) => {
  const current = await getTaskState(taskId);
  
  await db.taskState.update(current.id, {
    ...current,
    ...stateData,
    lastUpdated: new Date()
  });
  
  return await getTaskState(taskId);
};

// 更新当前任务状态
const updateCurrentTaskState = async (stateData) => {
  const taskId = await getCurrentTaskId();
  return await updateTaskState(taskId, stateData);
};

// 重置任务状态
const resetTaskState = async (taskId) => {
  const current = await getTaskState(taskId);
  
  await db.taskState.update(current.id, {
    taskId: current.taskId,
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
  
  return await getTaskState(taskId);
};

// 重置当前任务状态
const resetCurrentTaskState = async () => {
  const taskId = await getCurrentTaskId();
  return await resetTaskState(taskId);
};

// 保存上传的文件信息
const saveFileInfo = async (fileInfo) => {
  const taskId = await getCurrentTaskId();
  const id = Date.now().toString();
  
  await db.files.put({
    id,
    taskId,
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
  const taskId = await getCurrentTaskId();
  
  const id = await db.messages.add({
    ...message,
    taskId,
    timestamp: message.timestamp || new Date()
  });
  
  return id;
};

// 批量保存消息
const saveMessages = async (messages) => {
  const taskId = await getCurrentTaskId();
  
  // 使用事务确保原子性操作
  return await db.transaction('rw', db.messages, async () => {
    // 先清空当前任务的所有消息
    await db.messages.where('taskId').equals(taskId).delete();
    
    // 然后添加新消息
    return await db.messages.bulkAdd(messages.map(msg => ({
      ...msg,
      taskId,
      timestamp: msg.timestamp || new Date()
    })));
  });
};

// 获取当前任务的所有消息
const getAllMessages = async () => {
  const taskId = await getCurrentTaskId();
  return await db.messages.where('taskId').equals(taskId).toArray();
};

// 获取指定任务的所有消息
const getTaskMessages = async (taskId) => {
  return await db.messages.where('taskId').equals(taskId).toArray();
};

// 清空当前任务的所有消息
const clearAllMessages = async () => {
  const taskId = await getCurrentTaskId();
  await db.messages.where('taskId').equals(taskId).delete();
};

// 删除消息
const deleteMessage = async (id) => {
  await db.messages.delete(id);
};

// 保存格式错误信息
const saveFormatErrors = async (errors) => {
  try {
    const taskId = await getCurrentTaskId();
    
    // 使用事务确保原子性操作
    await db.transaction('rw', db.formatErrors, async () => {
      // 清空当前任务的现有错误
      await db.formatErrors.where('taskId').equals(taskId).delete();
      
      // 没有错误时直接返回
      if (!errors || errors.length === 0) return;
      
      // 将错误存储为单独的记录
      const simplifiedErrors = errors.map(err => ({
        taskId,
        message: String(err.message || '未知错误'),
        location: err.location ? String(err.location) : null,
        timestamp: new Date()
      }));
      
      // 批量添加错误
      await db.formatErrors.bulkAdd(simplifiedErrors);
    });
  } catch (error) {
    console.error('保存格式错误时出错:', error);
  }
};

// 获取当前任务的格式错误信息
const getFormatErrors = async () => {
  try {
    const taskId = await getCurrentTaskId();
    return await db.formatErrors.where('taskId').equals(taskId).toArray();
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
  getCurrentTaskId,
  switchTask,
  getAllTasks,
  createTask,
  deleteTask,
  getTask,
  updateTask,
  getCurrentTaskState,
  getTaskState,
  updateTaskState,
  updateCurrentTaskState,
  resetTaskState,
  resetCurrentTaskState,
  saveFileInfo,
  getFileInfo,
  deleteFileInfo,
  updateFileInfo,
  saveMessage,
  saveMessages,
  getAllMessages,
  getTaskMessages,
  clearAllMessages,
  deleteMessage,
  saveFormatErrors,
  getFormatErrors
};
