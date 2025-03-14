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
    <div v-else class="docx-content p-6" :class="isDarkMode ? 'text-zinc-100' : 'text-gray-900'" v-html="content"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, inject, watch } from 'vue'
import mammoth from 'mammoth'
import axios from 'axios'

const props = defineProps({
  filePath: {
    type: String,
    required: true
  }
})

const isDarkMode = inject('isDarkMode')
const loading = ref(true)
const error = ref(null)
const content = ref('')

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
    
    // 使用mammoth.js转换docx为HTML
    const result = await mammoth.convertToHtml({ 
      arrayBuffer: response.data,
      styleMap: [
        "p[style-name='Heading 1'] => h1:fresh",
        "p[style-name='Heading 2'] => h2:fresh",
        "p[style-name='Heading 3'] => h3:fresh",
        "p[style-name='Heading 4'] => h4:fresh",
        "p[style-name='Heading 5'] => h5:fresh",
        "p[style-name='Heading 6'] => h6:fresh"
      ]
    })
    
    // 设置转换后的HTML内容
    content.value = result.value
    
    // 添加自定义样式
    applyCustomStyles()
  } catch (err) {
    error.value = '加载文档失败：' + err.message
  } finally {
    loading.value = false
  }
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
      color: ${isDarkMode.value ? '#f1f5f9' : '#111827'};
    }
    .docx-content h1 {
      font-size: 1.8rem;
      font-weight: 600;
      margin: 1.5rem 0 1rem;
      padding-bottom: 0.5rem;
      border-bottom: 1px solid ${isDarkMode.value ? '#3f3f46' : '#e5e7eb'};
      color: ${isDarkMode.value ? '#f1f5f9' : '#111827'};
    }
    .docx-content h2 {
      font-size: 1.5rem;
      font-weight: 600;
      margin: 1.4rem 0 0.8rem;
      color: ${isDarkMode.value ? '#f1f5f9' : '#111827'};
    }
    .docx-content h3 {
      font-size: 1.3rem;
      font-weight: 600;
      margin: 1.2rem 0 0.7rem;
      color: ${isDarkMode.value ? '#f1f5f9' : '#111827'};
    }
    .docx-content h4, .docx-content h5, .docx-content h6 {
      font-size: 1.1rem;
      font-weight: 600;
      margin: 1rem 0 0.6rem;
      color: ${isDarkMode.value ? '#f1f5f9' : '#111827'};
    }
    .docx-content p {
      margin-bottom: 1em;
      color: ${isDarkMode.value ? '#e4e4e7' : '#1f2937'};
    }
    .docx-content table {
      border-collapse: collapse;
      width: 100%;
      margin-bottom: 1.5em;
      border: 1px solid ${isDarkMode.value ? '#3f3f46' : '#e5e7eb'};
    }
    .docx-content td, .docx-content th {
      border: 1px solid ${isDarkMode.value ? '#3f3f46' : '#e5e7eb'};
      padding: 8px 12px;
      color: ${isDarkMode.value ? '#e4e4e7' : '#1f2937'};
    }
    .docx-content th {
      background-color: ${isDarkMode.value ? '#27272a' : '#f9fafb'};
      font-weight: 600;
      color: ${isDarkMode.value ? '#f1f5f9' : '#111827'};
    }
    .docx-content img {
      max-width: 100%;
      height: auto;
      margin: 1em 0;
    }
    .docx-content ul, .docx-content ol {
      margin-bottom: 1em;
      padding-left: 2em;
      color: ${isDarkMode.value ? '#e4e4e7' : '#1f2937'};
    }
    .docx-content li {
      margin-bottom: 0.5em;
    }
    .docx-content a {
      color: ${isDarkMode.value ? '#60a5fa' : '#2563eb'};
      text-decoration: none;
    }
    .docx-content a:hover {
      text-decoration: underline;
    }
    .docx-content blockquote {
      border-left: 4px solid ${isDarkMode.value ? '#4b5563' : '#e5e7eb'};
      padding-left: 1em;
      margin-left: 0;
      margin-right: 0;
      font-style: italic;
      color: ${isDarkMode.value ? '#9ca3af' : '#4b5563'};
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