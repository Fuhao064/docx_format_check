<template>
  <div class="docx-preview" :class="isDarkMode ? 'bg-zinc-900' : 'bg-white'">
    <div v-if="loading" class="h-full flex flex-col items-center justify-center" :class="isDarkMode ? 'text-zinc-500' : 'text-gray-600'">
      <svg class="animate-spin -ml-1 mr-3 h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <span class="mt-3">加载文档中...</span>
    </div>
    <div v-else-if="error" class="h-full flex flex-col items-center justify-center p-4">
      <div class="p-4 rounded-lg text-center max-w-md" :class="isDarkMode ? 'bg-red-900/20 text-red-400 border border-red-800/30' : 'bg-red-50 text-red-700 border border-red-200'">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <p class="font-medium mb-2">文档加载失败</p>
        <p class="text-sm" :class="isDarkMode ? 'text-zinc-300' : 'text-gray-800'">{{ error }}</p>
      </div>
    </div>
    <vue-office-docx 
      v-else
      :src="docxContent"
      class="docx-content"
      :class="isDarkMode ? 'text-zinc-100 dark-theme' : 'text-gray-900'"
      @rendered="onDocRendered"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, inject, watch } from 'vue'
import axios from 'axios'
import VueOfficeDocx from '@vue-office/docx'
import '@vue-office/docx/lib/index.css'

const props = defineProps({
  filePath: {
    type: String,
    required: true
  }
})

const isDarkMode = inject('isDarkMode')
const loading = ref(true)
const error = ref(null)
const docxContent = ref(null)

// 监听文件路径变化，重新加载文档
watch(() => props.filePath, loadDocument)

onMounted(loadDocument)

async function loadDocument() {
  if (!props.filePath) return
  
  loading.value = true
  error.value = null
  
  try {
    // 获取docx文件内容
    const response = await axios.get(`/api/get-docx-content?file_path=${encodeURIComponent(props.filePath)}`, {
      responseType: 'arraybuffer'
    })
    
    // 使用vue-office-docx渲染文档
    docxContent.value = response.data
  } catch (err) {
    error.value = '加载文档失败：' + err.message
  } finally {
    loading.value = false
  }
}

function onDocRendered() {
  console.log("文档渲染完成")
  
  // 应用自定义样式
  applyCustomStyles()
}

function applyCustomStyles() {
  // 移除之前的样式（如果有）
  const existingStyle = document.getElementById('docx-preview-styles')
  if (existingStyle) {
    existingStyle.remove()
  }
  
  // 创建新样式
  const style = document.createElement('style')
  style.id = 'docx-preview-styles'
  style.textContent = `
    .docx-content {
      font-family: "Microsoft YaHei", -apple-system, BlinkMacSystemFont, sans-serif;
      line-height: 1.6;
    }
    .dark-theme .docx-viewer-wrapper {
      background-color: #18181b !important;
      color: #f1f5f9 !important;
    }
    .docx-viewer-wrapper {
      height: 100%;
    }
    .dark-theme .docx-viewer * {
      color: #e4e4e7;
    }
    .dark-theme .docx-viewer h1,
    .dark-theme .docx-viewer h2,
    .dark-theme .docx-viewer h3,
    .dark-theme .docx-viewer h4,
    .dark-theme .docx-viewer h5,
    .dark-theme .docx-viewer h6 {
      color: #f1f5f9;
    }
    .dark-theme .docx-viewer a {
      color: #60a5fa;
    }
    .dark-theme .docx-viewer table {
      border-color: #3f3f46;
    }
    .dark-theme .docx-viewer td,
    .dark-theme .docx-viewer th {
      border-color: #3f3f46;
    }
    .dark-theme .docx-viewer th {
      background-color: #27272a;
    }
    .dark-theme .docx-viewer blockquote {
      color: #9ca3af;
      border-color: #4b5563;
    }
  `
  document.head.appendChild(style)
}
</script>

<style scoped>
.docx-preview {
  height: 100%;
  overflow-y: auto;
}

.docx-content {
  height: 100%;
}

/* 自定义滚动条样式 */
.docx-preview::-webkit-scrollbar {
  width: 6px;
}

.docx-preview::-webkit-scrollbar-track {
  background: transparent;
}

.docx-preview::-webkit-scrollbar-thumb {
  background-color: v-bind('isDarkMode ? "#3f3f46" : "#d1d5db"');
  border-radius: 3px;
}

.docx-preview::-webkit-scrollbar-thumb:hover {
  background-color: v-bind('isDarkMode ? "#52525b" : "#9ca3af"');
}
</style>