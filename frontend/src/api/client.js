import axios from 'axios'
import { io } from 'socket.io-client'

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 请求拦截器
apiClient.interceptors.request.use(
  config => {
    // 添加请求 ID
    config.metadata = { startTime: new Date() }

    // 添加请求头
    config.headers = {
      ...config.headers,
      'Content-Type': config.headers?.['Content-Type'] || 'application/json'
    }

    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  response => {
    return response
  },
  error => {
    // 统一错误处理
    const config = error.config?.metadata

    if (error.response) {
      // 服务器响应错误
      const status = error.response.status
      const message = error.response.data?.message || '请求失败'

      console.error(`API Error [${status}]:`, message)

      // 401: 未授权
      if (status === 401) {
        console.warn('未授权，请登录')
      }
      // 403: 禁止访问
      else if (status === 403) {
        console.warn('禁止访问')
      }
      // 404: 资源不存在
      else if (status === 404) {
        console.warn('资源不存在')
      }
      // 500: 服务器错误
      else if (status === 500) {
        console.error('服务器内部错误')
      }
    } else if (error.request) {
      // 请求未发送
      console.error('网络错误：请求未发送')
    } else {
      // 其他错误
      console.error('未知错误:', error.message)
    }

    return Promise.reject(error)
  }
)

// WebSocket 客户端
const socketClient = io({
  reconnection: true,
  reconnectionAttempts: 5,
  reconnectionDelay: 1000,
  transports: ['websocket', 'polling']
})

// WebSocket 事件监听
socketClient.on('connect', () => {
  console.log('WebSocket 已连接')
})

socketClient.on('disconnect', () => {
  console.log('WebSocket 已断开')
})

socketClient.on('connect_error', (error) => {
  console.error('WebSocket 连接错误:', error)
})

// 上传进度事件
socketClient.on('upload_progress', (data) => {
  console.log('上传进度:', data)
  // 可以通过自定义事件分发
  window.dispatchEvent(new CustomEvent('upload-progress', { detail: data }))
})

// 分析进度事件
socketClient.on('analysis_progress', (data) => {
  console.log('分析进度:', data)
  window.dispatchEvent(new CustomEvent('analysis-progress', { detail: data }))
})

// LLM 进度事件
socketClient.on('llm_progress', (data) => {
  console.log('LLM 进度:', data)
  window.dispatchEvent(new CustomEvent('llm-progress', { detail: data }))
})

// 任务状态事件
socketClient.on('task_status', (data) => {
  console.log('任务状态:', data)
  window.dispatchEvent(new CustomEvent('task-status', { detail: data }))
})

// 通知事件
socketClient.on('notification', (data) => {
  console.log('通知:', data)
  window.dispatchEvent(new CustomEvent('notification', { detail: data }))
})

// 加入房间
export const joinRoom = (room) => {
  socketClient.emit('join_room', { room })
}

// 离开房间
export const leaveRoom = (room) => {
  socketClient.emit('leave_room', { room })
}

export { apiClient, socketClient }
