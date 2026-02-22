import { apiClient } from './client.js'

export const fileService = {
  uploadDocument: (file, onUploadProgress = null) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post('/v2/documents', formData, {
      onUploadProgress,
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  uploadFormat: (file, onUploadProgress = null) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post('/v2/formats', formData, {
      onUploadProgress,
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  getDefaultFormat: () => apiClient.get('/v2/formats/default')
}

export const contextService = {
  prepare: (documentId, formatId) => apiClient.post('/v2/contexts/prepare', {
    document_id: documentId,
    format_id: formatId
  }),
  chat: (contextId, message) => apiClient.post(`/v2/contexts/${contextId}/chat`, { message }),
  analyzeParagraph: (contextId, paraIndex, contextRange = 2) => apiClient.post(`/v2/contexts/${contextId}/paragraph-analysis`, {
    para_index: paraIndex,
    context_range: contextRange
  }),
  enhanceParagraphs: (contextId, paraIndices) => apiClient.post(`/v2/contexts/${contextId}/paragraph-enhance`, {
    para_indices: paraIndices
  }),
  createReports: (contextId, payload = {}) => apiClient.post(`/v2/contexts/${contextId}/reports`, payload),
  applyFormat: (contextId, payload = {}) => apiClient.post(`/v2/contexts/${contextId}/format-apply`, payload, {
    responseType: 'blob'
  }),
  getDocumentContent: (contextId) => apiClient.get(`/v2/contexts/${contextId}/document-content`, {
    responseType: 'arraybuffer'
  }),
  // LaTeX 导出
  exportLatex: (contextId, payload = {}) => apiClient.post(`/v2/contexts/${contextId}/latex-export`, payload),
  // 自动修复
  autoFix: (contextId, payload = {}) => apiClient.post(`/v2/contexts/${contextId}/auto-fix`, payload),
  getFixReport: (contextId) => apiClient.get(`/v2/contexts/${contextId}/fix-report`),
  getRepairHistory: (contextId) => apiClient.get(`/v2/contexts/${contextId}/repair-history`),
  // 文档对比
  compare: (contextId, otherContextId) => apiClient.post(`/v2/contexts/${contextId}/compare`, {
    other_context_id: otherContextId
  })
}

export const downloadService = {
  report: (reportId) => apiClient.get(`/v2/reports/${reportId}`, { responseType: 'blob' }),
  markedDocument: (markedDocId) => apiClient.get(`/v2/marked-documents/${markedDocId}`, { responseType: 'blob' }),
  latex: (exportId) => apiClient.get(`/v2/latex-exports/${exportId}`, { responseType: 'blob' }),
  fixedDocument: (repairId) => apiClient.get(`/v2/repairs/${repairId}/document`, { responseType: 'blob' })
}

export const comparisonService = {
  getComparison: (diffId) => apiClient.get(`/v2/comparisons/${diffId}`),
  getComparisonHtml: (diffId) => apiClient.get(`/v2/comparisons/${diffId}/html`, {
    responseType: 'text'
  })
}

export const llmService = {
  getModels: () => apiClient.get('/models'),
  addModel: (data) => apiClient.post('/add-model', data),
  deleteModel: (modelName) => apiClient.delete(`/delete-model/${modelName}`),
  setAgentModel: (data) => apiClient.post('/set-agent-model', data),
  sendMessage: (data) => apiClient.post('/send-message', data)
}

export const configService = {
  getConfig: () => apiClient.get('/get-config'),
  getConfigExample: () => apiClient.get('/get-config-example'),
  setConfig: (data) => apiClient.post('/set-config', data)
}

export default {
  fileService,
  contextService,
  downloadService,
  comparisonService,
  llmService,
  configService
}
