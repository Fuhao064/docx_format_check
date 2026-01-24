import { ref } from 'vue'
import axios from 'axios'

/**
 * 文件上传 Composable
 *
 * 提供文件上传、进度跟踪、时间戳命名等功能
 */
export function useFileUpload() {
  const uploadProgress = ref(0)
  const uploadHistory = ref([])
  const isUploading = ref(false)
  const currentFile = ref(null)

  /**
   * 生成时间戳文件名
   * 格式: 原文件名_YYYYMMDD_HHmmss_SSS.扩展名
   *
   * @param {string} originalName - 原始文件名
   * @returns {string} 时间戳文件名
   */
  const generateTimestampName = (originalName) => {
    const now = new Date()
    const year = now.getFullYear()
    const month = String(now.getMonth() + 1).padStart(2, '0')
    const day = String(now.getDate()).padStart(2, '0')
    const hours = String(now.getHours()).padStart(2, '0')
    const minutes = String(now.getMinutes()).padStart(2, '0')
    const seconds = String(now.getSeconds()).padStart(2, '0')
    const milliseconds = String(now.getMilliseconds()).padStart(3, '0')

    const timestamp = `${year}${month}${day}_${hours}${minutes}${seconds}_${milliseconds}`

    // 提取文件扩展名
    const lastDotIndex = originalName.lastIndexOf('.')
    if (lastDotIndex === -1) {
      return `${originalName}_${timestamp}`
    }

    const baseName = originalName.slice(0, lastDotIndex)
    const ext = originalName.slice(lastDotIndex)

    return `${baseName}_${timestamp}${ext}`
  }

  /**
   * 格式化文件大小
   *
   * @param {number} bytes - 字节数
   * @returns {string} 格式化后的文件大小
   */
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B'

    const units = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    const size = bytes / Math.pow(1024, i)

    return `${size.toFixed(2)} ${units[i]}`
  }

  /**
   * 上传文件（带进度）
   *
   * @param {File} file - 要上传的文件
   * @param {Function} onProgress - 进度回调函数
   * @returns {Promise} 上传结果
   */
  const uploadFile = async (file, onProgress = null) => {
    if (!file) {
      throw new Error('未提供文件')
    }

    isUploading.value = true
    currentFile.value = file

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post('/api/upload-files', {
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percent = Math.round((progressEvent.loaded / progressEvent.total) * 100)
            uploadProgress.value = percent

            if (onProgress) {
              onProgress({
                loaded: progressEvent.loaded,
                total: progressEvent.total,
                percent: percent
              })
            }
          }
        }
      }, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000 // 2分钟超时
      })

      if (response.data.success) {
        const uploadRecord = {
          id: Date.now().toString(),
          originalName: file.name,
          timestampedName: response.data.file.filename || file.name,
          size: file.size,
          uploadTime: new Date().toISOString(),
          status: 'completed',
          path: response.data.file.path || response.data.file_path
        }

        uploadHistory.value.unshift(uploadRecord)

        return {
          success: true,
          file: uploadRecord,
          response: response.data
        }
      } else {
        throw new Error(response.data.message || '上传失败')
      }
    } catch (error) {
      const errorRecord = {
        id: Date.now().toString(),
        originalName: file.name,
        timestampedName: '',
        size: file.size,
        uploadTime: new Date().toISOString(),
        status: 'error',
        error: error.message
      }

      uploadHistory.value.unshift(errorRecord)
      throw error
    } finally {
      isUploading.value = false
      currentFile.value = null
      setTimeout(() => {
        uploadProgress.value = 0
      }, 1000)
    }
  }

  /**
   * 获取上传历史记录
   *
   * @param {number} limit - 返回的最大记录数
   * @returns {Array} 上传历史记录
   */
  const getUploadHistory = (limit = 10) => {
    return uploadHistory.value.slice(0, limit)
  }

  /**
   * 清空上传历史
   */
  const clearUploadHistory = () => {
    uploadHistory.value = []
  }

  /**
   * 删除上传历史记录
   *
   * @param {string} id - 记录ID
   */
  const removeUploadRecord = (id) => {
    const index = uploadHistory.value.findIndex(record => record.id === id)
    if (index !== -1) {
      uploadHistory.value.splice(index, 1)
    }
  }

  /**
   * 获取状态文本
   *
   * @param {string} status - 状态值
   * @returns {string} 状态文本
   */
  const getStatusText = (status) => {
    const statusMap = {
      'pending': '等待中',
      'uploading': '上传中',
      'completed': '已完成',
      'error': '失败'
    }
    return statusMap[status] || status
  }

  return {
    uploadProgress,
    uploadHistory,
    isUploading,
    currentFile,
    generateTimestampName,
    formatFileSize,
    uploadFile,
    getUploadHistory,
    clearUploadHistory,
    removeUploadRecord,
    getStatusText
  }
}
