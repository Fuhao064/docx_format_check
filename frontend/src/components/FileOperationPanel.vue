<template>
  <div class="file-operation-panel p-6 overflow-y-auto">
    <h1 class="text-2xl font-bold mb-6 text-[hsl(var(--foreground))]">文件管理</h1>

    <!-- 文件上传区 -->
    <div class="bg-[hsl(var(--card))] rounded-lg border border-[hsl(var(--border))] p-6 mb-6">
      <h2 class="text-lg font-semibold mb-4 text-[hsl(var(--foreground))]">上传文件</h2>
      <div
        class="upload-zone border-2 border-dashed border-[hsl(var(--border))] rounded-lg p-8
               text-center cursor-pointer transition-colors
               hover:border-[hsl(var(--primary))] hover:bg-[hsl(var(--secondary)/0.3)]"
        @click="triggerFileUpload"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="handleDrop"
        :class="{ 'border-[hsl(var(--primary))] bg-[hsl(var(--secondary)/0.3)]': isDragging }"
      >
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="1.5" class="mx-auto mb-4 text-[hsl(var(--primary))]">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="17 8 12 3 7 8"></polyline>
          <line x1="12" y1="3" x2="12" y2="15"></line>
        </svg>
        <p class="text-lg font-medium text-[hsl(var(--foreground))] mb-2">
          点击上传或拖拽文件到此处
        </p>
        <p class="text-sm text-[hsl(var(--muted-foreground))]">
          支持 .docx 格式文档
        </p>
      </div>

      <!-- 上传进度 -->
      <div v-if="uploadProgress > 0 && uploadProgress < 100" class="mt-4">
        <div class="flex justify-between text-sm mb-1">
          <span class="text-[hsl(var(--foreground))]">上传中...</span>
          <span class="text-[hsl(var(--primary))]">{{ uploadProgress }}%</span>
        </div>
        <div class="w-full bg-[hsl(var(--secondary))] rounded-full h-2">
          <div
            class="bg-[hsl(var(--primary))] h-full rounded-full transition-all duration-300"
            :style="{ width: uploadProgress + '%' }"
          ></div>
        </div>
      </div>
    </div>

    <!-- 上传历史 -->
    <div class="bg-[hsl(var(--card))] rounded-lg border border-[hsl(var(--border))] p-6">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-lg font-semibold text-[hsl(var(--foreground))]">上传历史</h2>
        <button
          @click="clearHistory"
          class="text-sm text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--destructive))] transition-colors"
        >
          清空历史
        </button>
      </div>

      <div v-if="uploadHistory.length === 0" class="text-center py-8 text-[hsl(var(--muted-foreground))]">
        暂无上传历史
      </div>

      <div v-else class="space-y-2">
        <div
          v-for="(file, index) in uploadHistory"
          :key="index"
          class="flex items-center justify-between p-3 rounded-lg
                 hover:bg-[hsl(var(--secondary))] transition-colors"
        >
          <div class="flex items-center gap-3">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
              stroke-width="2" class="text-[hsl(var(--primary))]">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
            </svg>
            <div>
              <p class="text-[hsl(var(--foreground))]">{{ file.originalName }}</p>
              <p class="text-xs text-[hsl(var(--muted-foreground))]">
                {{ formatTimestamp(file.timestamp) }}
              </p>
            </div>
          </div>
          <span
            class="px-2 py-1 rounded text-xs"
            :class="{
              'bg-[hsl(var(--success)/0.15)] text-[hsl(var(--success))]': file.status === 'completed',
              'bg-[hsl(var(--warning)/0.15)] text-[hsl(var(--warning))]': file.status === 'uploading',
              'bg-[hsl(var(--destructive)/0.15)] text-[hsl(var(--destructive))]': file.status === 'error'
            }"
          >
            {{ getStatusText(file.status) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { inject } from 'vue'

const uploadProgress = ref(0)
const uploadHistory = ref([])
const isDragging = ref(false)
const showNotification = inject('showNotification', null)

onMounted(async () => {
  await loadUploadHistory()
})

function triggerFileUpload() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.docx'
  input.onchange = handleFileSelect
  input.click()
}

async function handleFileSelect(event) {
  const file = event.target.files[0]
  if (!file) return

  await uploadFile(file)
}

async function handleDrop(event) {
  isDragging.value = false
  const file = event.dataTransfer.files[0]
  if (!file) return

  if (!file.name.endsWith('.docx')) {
    showNotification('error', '文件格式错误', '只支持 .docx 格式文档', 3000)
    return
  }

  await uploadFile(file)
}

async function uploadFile(file) {
  const formData = new FormData()
  formData.append('file', file)

  uploadProgress.value = 0

  try {
    const response = await axios.post('/api/upload-files', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total) {
          uploadProgress.value = Math.round((progressEvent.loaded / progressEvent.total) * 100)
        }
      }
    })

    if (response.data.success) {
      uploadProgress.value = 100

      const timestampedName = response.data.file.filename || file.name

      uploadHistory.value.unshift({
        originalName: file.name,
        timestampedName: timestampedName,
        size: file.size,
        timestamp: new Date().toISOString(),
        status: 'completed',
        path: response.data.file.path || response.data.file_path
      })

      // 保存到IndexedDB
      saveToIndexedDB(uploadHistory.value[0])

      showNotification('success', '上传成功', `文件 "${file.name}" 已成功上传`, 3000)
    } else {
      throw new Error(response.data.message || '上传失败')
    }
  } catch (error) {
    console.error('上传文件失败:', error)
    showNotification('error', '上传失败', error.message || '上传文件时出错', 3000)

    uploadHistory.value.unshift({
      originalName: file.name,
      timestampedName: '',
      size: file.size,
      timestamp: new Date().toISOString(),
      status: 'error',
      path: ''
    })
  } finally {
    setTimeout(() => {
      uploadProgress.value = 0
    }, 2000)
  }
}

function formatTimestamp(timestamp) {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

function getStatusText(status) {
  const statusMap = {
    'pending': '等待中',
    'uploading': '上传中',
    'completed': '已完成',
    'error': '失败'
  }
  return statusMap[status] || status
}

async function saveToIndexedDB(fileInfo) {
  try {
    // 这里可以扩展为保存到IndexedDB
    console.log('保存文件信息:', fileInfo)
  } catch (error) {
    console.error('保存到IndexedDB失败:', error)
  }
}

async function loadUploadHistory() {
  try {
    // 这里可以从IndexedDB加载历史记录
    console.log('加载上传历史')
  } catch (error) {
    console.error('加载上传历史失败:', error)
  }
}

async function clearHistory() {
  if (!confirm('确定要清空上传历史吗？')) {
    return
  }

  uploadHistory.value = []
  showNotification('success', '历史已清空', '上传历史已清空', 2000)
}
</script>

<style scoped>
.file-operation-panel {
  height: 100%;
}

.upload-zone {
  min-height: 200px;
}
</style>
