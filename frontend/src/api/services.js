import { apiClient } from './client.js'

export const fileService = {
  /**
   * 上传文件
   * @param {File} file - 要上传的文件
   * @param {Function} onUploadProgress - 进度回调
   * @returns {Promise} 上传结果
   */
  upload: (file, onUploadProgress = null) => {
    const formData = new FormData()
    formData.append('file', file)

    return apiClient.post('/upload-files', formData, {
      onUploadProgress,
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  /**
   * 获取文件元数据
   * @param {string} fileId - 文件ID
   * @returns {Promise} 文件元数据
   */
  getMetadata: (fileId) => apiClient.get(`/file-metadata/${fileId}`),

  /**
   * 获取上传历史
   * @param {Object} params - 查询参数
   * @returns {Promise} 上传历史记录
   */
  getHistory: (params = {}) => apiClient.get('/file-history', { params })
}

export const documentService = {
  /**
   * 检查文档格式
   * @param {Object} data - 请求数据
   * @returns {Promise} 检查结果
   */
  checkFormat: (data) => apiClient.post('/check-format', data),

  /**
   * 应用格式修复
   * @param {Object} data - 请求数据
   * @returns {Promise} 修复后的文档（blob）
   */
  applyFormat: (data) => apiClient.post('/apply-format', data, {
    responseType: 'blob'
  }),

  /**
   * 生成报告
   * @param {Object} data - 请求数据
   * @returns {Promise} 报告文件（blob）
   */
  generateReport: (data) => apiClient.post('/generate-report', data, {
    responseType: 'blob'
  })
}

export const taskService = {
  /**
   * 获取任务列表
   * @param {Object} params - 查询参数
   * @returns {Promise} 任务列表
   */
  list: (params = {}) => apiClient.get('/tasks', { params }),

  /**
   * 创建任务
   * @param {Object} data - 任务数据
   * @returns {Promise} 创建结果
   */
  create: (data) => apiClient.post('/tasks', data),

  /**
   * 更新任务
   * @param {string} taskId - 任务ID
   * @param {Object} data - 更新数据
   * @returns {Promise} 更新结果
   */
  update: (taskId, data) => apiClient.put(`/tasks/${taskId}`, data),

  /**
   * 删除任务
   * @param {string} taskId - 任务ID
   * @returns {Promise} 删除结果
   */
  delete: (taskId) => apiClient.delete(`/tasks/${taskId}`),

  /**
   * 获取任务状态
   * @param {string} taskId - 任务ID
   * @returns {Promise} 任务状态
   */
  getStatus: (taskId) => apiClient.get(`/tasks/${taskId}/status`)
}

export const llmService = {
  /**
   * 获取可用模型列表
   * @returns {Promise} 模型列表
   */
  getModels: () => apiClient.get('/models'),

  /**
   * 添加模型
   * @param {Object} data - 模型配置
   * @returns {Promise} 添加结果
   */
  addModel: (data) => apiClient.post('/add-model', data),

  /**
   * 删除模型
   * @param {string} modelName - 模型名称
   * @returns {Promise} 删除结果
   */
  deleteModel: (modelName) => apiClient.delete(`/delete-model/${modelName}`),

  /**
   * 设置代理模型
   * @param {Object} data - 代理模型配置
   * @returns {Promise} 设置结果
   */
  setAgentModel: (data) => apiClient.post('/set-agent-model', data),

  /**
   * 发送消息
   * @param {Object} data - 消息数据
   * @returns {Promise} 响应
   */
  sendMessage: (data) => api {
    return apiClient.post('/send-message', data)
  },

  /**
   * 分析段落
   * @param {Object} data - 分析数据
   * @returns {Promise} 分析结果
   */
  analyzeParagraph: (data) => apiClient.post('/analyze-paragraph', data),

  /**
   * 增强段落
   * @param {Object} data - 增强数据
   * @returns {Promise} 增强结果
   */
  enhanceParagraphs: (data) => apiClient.post('/enhance-paragraphs', data)
}

export const configService = {
  /**
   * 获取当前配置
   * @returns {Promise} 配置数据
   */
  getConfig: () => apiClient.get('/get-config'),

  /**
   * 设置配置
   * @param {Object} data - 配置数据
   * @returns {Promise} 设置结果
   */
  setConfig: (data) => apiClient.post('/set-config', data),

  /**
   * 创建配置
   * @param {Object} data - 配置数据
   * @returns {Promise} 创建结果
   */
  createConfig: (data) => apiClient.post('/create-config', data)
}

export default {
  fileService,
  documentService,
  taskService,
  llmService,
  configService
}
