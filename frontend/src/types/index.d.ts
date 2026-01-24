// 文件上传相关
export interface UploadProgress {
  loaded: number
  total: number
  percent: number
}

export interface FileMetadata {
  id: string
  originalName: string
  timestampedName: string
  size: number
  uploadTime: string
  status: 'pending' | 'uploading' | 'completed' | 'error'
  path?: string
}

// 文档分析相关
export interface ParagraphMeta {
  [key: string]: any
}

export interface Paragraph {
  id: string
  type: string
  content: string
  meta: ParagraphMeta
}

export interface FormatError {
  message: string
  location?: string
  severity?: 'error' | 'warning' | 'info'
}

export interface AnalysisResult {
  success: boolean
  message: string
  errors: FormatError[]
  para_manager?: any
}

// 任务相关
export interface Task {
  id: string
  title: string
  status: 'pending' | 'in_progress' | 'completed' | 'error'
  progress: number
  createdAt: string
  lastUpdated: string
}

export interface TaskStatus {
  task_id: string
  status: string
  progress: number
  message?: string
  result?: any
  error?: string
}

// WebSocket 事件
export type SocketEvent =
  | 'upload_progress'
  | 'analysis_progress'
  | 'llm_progress'
  | 'task_status'
  | 'notification'

export interface SocketMessage<T> {
  event: SocketEvent
  data: T
}

export interface UploadProgressData {
  task_id: string
  filename: string
  loaded: number
  total: number
  percent: number
  timestamp: string
}

export interface AnalysisProgressData {
  task_id: string
  stage: string
  message: string
  progress: number
  timestamp: string
}

export interface LLMProgressData {
  task_id: string
  model: string
  current: number
  total: number
  percent: number
  timestamp: string
}

export interface NotificationData {
  level: 'success' | 'warning' | 'error' | 'info'
  title: string
  message: string
  data?: Record<string, any>
  timestamp: string
}

// LLM 相关
export interface LLMModel {
  model_key: string
  model_name: string
  base_url?: string
}

export interface AgentConfig {
  format_agent?: string
  editor_agent?: string
  advice_agent?: string
  communicate_agent?: string
}

// 配置相关
export interface FormatConfig {
  page_settings?: PageSettings
  paragraph_formats?: ParagraphFormats
  font_settings?: FontSettings
  heading_formats?: HeadingFormats
  citation_styles?: CitationStyles
}

export interface PageSettings {
  margin_top?: number
  margin_bottom?: number
  margin_left?: number
  margin_right?: number
}

export interface ParagraphFormats {
  [key: string]: {
    font_name?: string
    font_size?: number
    line_spacing?: number
    space_before?: number
    space_after?: number
  }
}

export interface FontSettings {
  [key: string]: string
}

export interface HeadingFormats {
  [key: string]: {
    font_name?: string
    font_size?: number
    bold?: boolean
  }
}

export interface CitationStyles {
  [key: string]: any
}

// API 响应
export interface ApiResponse<T = any> {
  success: boolean
  message: string
  data?: T
}

export interface ApiError {
  success: false
  message: string
  error?: string
}

// 工作台状态
export interface WorkspaceState {
  id: number
  layout: {
    sidebarCollapsed: boolean
    activeTab: string
  }
  preferences: {
    theme: string
    language: string
  }
  lastOpenedFiles: string[]
}

// IndexedDB 表结构
export interface DBAppState {
  id: number
  currentTaskId?: string
  lastUpdated?: Date
}

export interface DBTask {
  id: string
  title: string
  createdAt: Date
  lastUpdated: Date
}

export interface DBTaskState {
  id: string
  taskId: string
  hasUploadedFile: boolean
  hasUploadedFormat: boolean
  uploadedFileName: string
  formattedFilePath: string
  currentDocumentPath: string
  currentConfigPath: string
  currentStep: number
  processingComplete: boolean
  lastUpdated: Date
}

export interface DBFile {
  id: string
  taskId: string
  name: string
  path: string
  type: string
  lastUpdated: Date
}

export interface DBMessage {
  id?: number
  taskId: string
  content: string
  sender: 'user' | 'assistant'
  timestamp: Date
}

export interface DBFormatError {
  id?: number
  taskId: string
  message: string
  location: string | null
  timestamp: Date
}

export interface DBParagraphManager {
  id: string
  taskId: string
  docPath: string
  data: string
  lastUpdated: Date
}

export interface DBWorkspaceState {
  id: number
  layout: WorkspaceState['layout']
  preferences: WorkspaceState['preferences']
  lastOpenedFiles: string[]
}

export interface DBTaskQueue {
  id: string
  taskId: string
  status: 'pending' | 'in_progress' | 'completed' | 'error'
  progress: number
  result: any | null
  error: string | null
  timestamp: string
}

export interface DBFileMetadata {
  id: string
  originalName: string
  timestampedName: string
  size: number
  uploadTime: string
  status: string
}

export interface DBSyncLog {
  id: string
  type: string
  timestamp: string
  data: Record<string, any>
}
