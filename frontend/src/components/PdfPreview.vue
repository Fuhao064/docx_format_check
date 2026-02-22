<template>
  <div class="pdf-preview-container" :class="{ 'active': isVisible }">
    <div class="pdf-preview-header transition-colors duration-[--transition-speed]"
         :class="isDarkMode ? 'bg-[hsl(var(--background))]' : 'bg-[hsl(var(--background))]'">
      <div class="flex items-center justify-between px-4 py-3 border-b border-[hsl(var(--border))]">
        <h3 class="text-lg font-medium text-[hsl(var(--foreground))]">
          {{ fileName || 'PDF 预览' }}
        </h3>
        <button @click="closePreview"
                class="p-1.5 rounded-full hover:bg-[hsl(var(--secondary))] transition-colors">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="2" class="text-[hsl(var(--muted-foreground))]">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>
    </div>
    <div class="pdf-preview-wrapper">
      <div v-if="loading" class="loading-container">
        <svg class="animate-spin -ml-1 mr-3 h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span class="mt-3">加载 PDF 中...</span>
      </div>
      <div v-else-if="!pdfPath || pdfPath === ''" class="empty-container">
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="1.5" class="mb-6 text-[hsl(var(--muted-foreground))]">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
          <line x1="16" y1="13" x2="8" y2="13"></line>
          <line x1="16" y1="17" x2="8" y2="17"></line>
          <polyline points="10 9 9 9 8 9"></polyline>
        </svg>
        <p class="text-xl font-medium text-[hsl(var(--foreground))]">尚未上传文档</p>
        <p class="text-sm mt-2 mb-6 text-[hsl(var(--muted-foreground))]">请先上传 PDF 文档后查看预览</p>
      </div>
      <div v-else-if="error" class="error-container">
        <div class="p-4 rounded-lg text-center max-w-md"
             :class="isDarkMode ? 'bg-[hsl(var(--destructive)/0.2)] text-[hsl(var(--destructive))] border border-[hsl(var(--destructive)/0.3)]' : 'bg-[hsl(var(--destructive)/0.1)] text-[hsl(var(--destructive))] border border-[hsl(var(--destructive)/0.3)]'">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p class="font-medium mb-2">PDF 加载失败</p>
          <p class="text-sm text-[hsl(var(--muted-foreground))]">{{ error }}</p>
        </div>
      </div>
      <div v-else class="pdf-content">
        <iframe
          :src="pdfUrl"
          class="pdf-iframe"
          title="PDF Preview"
          @load="onPdfLoaded"
          @error="onPdfError"
        ></iframe>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, inject, watch, computed, nextTick } from 'vue'
import axios from 'axios'

const props = defineProps({
  pdfPath: {
    type: String,
    required: true
  },
  originalFileName: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['close'])

const isDarkMode = inject('isDarkMode')
const loading = ref(true)
const error = ref(null)
const pdfUrl = ref('')
const isVisible = ref(false)

const fileName = computed(() => {
  if (props.originalFileName) return props.originalFileName
  if (!props.pdfPath) return 'PDF 预览'
  return props.pdfPath.split('/').pop() || 'PDF 预览'
})

onMounted(() => {
  nextTick(() => {
    setTimeout(() => {
      isVisible.value = true
    }, 50)
  })
})

function closePreview() {
  isVisible.value = false
  setTimeout(() => {
    emit('close')
  }, 400)
}

watch(() => props.pdfPath, loadPdf)
onMounted(loadPdf)

async function loadPdf() {
  if (!props.pdfPath) return

  loading.value = true
  error.value = null

  try {
    const contextId = extractContextIdFromPath(props.pdfPath)
    if (contextId) {
      pdfUrl.value = `/api/v2/contexts/${contextId}/document-content`
    } else {
      pdfUrl.value = `/api/get-docx-content?file_path=${encodeURIComponent(props.pdfPath)}`
    }
  } catch (err) {
    error.value = '加载 PDF 失败：' + (err.message || '未知错误')
  } finally {
    loading.value = false
  }
}

function extractContextIdFromPath(path) {
  return null
}

function onPdfLoaded() {
  console.log('PDF 渲染完成')
  loading.value = false
}

function onPdfError() {
  error.value = 'PDF 渲染失败，请确认文件格式正确'
  loading.value = false
}
</script>

<style scoped>
.pdf-preview-container {
  position: fixed;
  top: 0;
  right: 0;
  width: clamp(350px, 45%, 900px);
  height: 100vh;
  z-index: 50;
  display: flex;
  flex-direction: column;
  border-left: 1px solid hsl(var(--border));
  box-shadow: -5px 0 15px rgba(0, 0, 0, 0.1);
  transform: translateX(100%);
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  background-color: hsl(var(--background));
  will-change: transform;
  overflow: hidden;
}

.pdf-preview-container.active {
  transform: translateX(0);
}

.pdf-preview-wrapper {
  flex: 1 1 auto;
  overflow: hidden;
  position: relative;
  background-color: hsl(var(--background));
  transition: background-color var(--transition-speed);
}

.pdf-content {
  height: 100%;
  width: 100%;
  overflow: hidden;
  box-sizing: border-box;
}

.pdf-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.loading-container,
.empty-container,
.error-container {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  box-sizing: border-box;
  color: hsl(var(--muted-foreground));
}

@media (max-width: 768px) {
  .pdf-preview-container {
    width: 100%;
    max-width: none;
  }
}
</style>
