import { ref } from 'vue'
import axios from 'axios'

export function useFileUpload() {
  const uploadProgress = ref(0)
  const uploadHistory = ref([])
  const isUploading = ref(false)
  const currentFile = ref(null)

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

    const lastDotIndex = originalName.lastIndexOf('.')
    if (lastDotIndex === -1) {
      return `${originalName}_${timestamp}`
    }

    const baseName = originalName.slice(0, lastDotIndex)
    const ext = originalName.slice(lastDotIndex)
    return `${baseName}_${timestamp}${ext}`
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B'
    const units = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    const size = bytes / Math.pow(1024, i)
    return `${size.toFixed(2)} ${units[i]}`
  }

  const uploadFile = async (file, onProgress = null) => {
    if (!file) {
      throw new Error('No file provided')
    }

    isUploading.value = true
    currentFile.value = file

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post('/api/v2/documents', formData, {
        onUploadProgress: (progressEvent) => {
          if (!progressEvent.total) return
          const percent = Math.round((progressEvent.loaded / progressEvent.total) * 100)
          uploadProgress.value = percent

          if (onProgress) {
            onProgress({
              loaded: progressEvent.loaded,
              total: progressEvent.total,
              percent,
            })
          }
        },
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
      })

      if (!response.data?.success) {
        throw new Error(response.data?.message || 'Upload failed')
      }

      const uploadRecord = {
        id: Date.now().toString(),
        originalName: file.name,
        timestampedName: response.data.original_filename || file.name,
        size: file.size,
        uploadTime: new Date().toISOString(),
        status: 'completed',
        path: response.data.doc_path,
      }

      uploadHistory.value.unshift(uploadRecord)

      return {
        success: true,
        file: uploadRecord,
        response: response.data,
      }
    } catch (error) {
      const errorRecord = {
        id: Date.now().toString(),
        originalName: file.name,
        timestampedName: '',
        size: file.size,
        uploadTime: new Date().toISOString(),
        status: 'error',
        error: error.message,
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

  const getUploadHistory = (limit = 10) => uploadHistory.value.slice(0, limit)

  const clearUploadHistory = () => {
    uploadHistory.value = []
  }

  const removeUploadRecord = (id) => {
    const index = uploadHistory.value.findIndex((record) => record.id === id)
    if (index !== -1) {
      uploadHistory.value.splice(index, 1)
    }
  }

  const getStatusText = (status) => {
    const statusMap = {
      pending: 'Pending',
      uploading: 'Uploading',
      completed: 'Completed',
      error: 'Failed',
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
    getStatusText,
  }
}
