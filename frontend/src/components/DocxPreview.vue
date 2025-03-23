<template>
  <div class="docx-preview-container" :class="{ 'active': isVisible }">
    <div class="docx-preview-header transition-colors duration-[--transition-speed]" 
         :class="isDarkMode ? 'bg-[hsl(var(--background))]' : 'bg-[hsl(var(--background))]'">
      <div class="flex items-center justify-between px-4 py-3 border-b border-[hsl(var(--border))]">
        <h3 class="text-lg font-medium text-[hsl(var(--foreground))]">
          {{ fileName || '文档预览' }}
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
    <div class="docx-preview-wrapper">
      <div v-if="loading" class="loading-container">
        <svg class="animate-spin -ml-1 mr-3 h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span class="mt-3">加载文档中...</span>
      </div>
      <div v-else-if="!docPath || docPath === ''" class="empty-container">
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="1.5" class="mb-6 text-[hsl(var(--muted-foreground))]">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
          <line x1="16" y1="13" x2="8" y2="13"></line>
          <line x1="16" y1="17" x2="8" y2="17"></line>
          <polyline points="10 9 9 9 8 9"></polyline>
        </svg>
        <p class="text-xl font-medium text-[hsl(var(--foreground))]">尚未上传文档</p>
        <p class="text-sm mt-2 mb-6 text-[hsl(var(--muted-foreground))]">请先上传文档后查看预览</p>
      </div>
      <div v-else-if="error" class="error-container">
        <div class="p-4 rounded-lg text-center max-w-md" 
             :class="isDarkMode ? 'bg-[hsl(var(--destructive)/0.2)] text-[hsl(var(--destructive))] border border-[hsl(var(--destructive)/0.3)]' : 'bg-[hsl(var(--destructive)/0.1)] text-[hsl(var(--destructive))] border border-[hsl(var(--destructive)/0.3)]'">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p class="font-medium mb-2">文档加载失败</p>
          <p class="text-sm text-[hsl(var(--muted-foreground))]">{{ error }}</p>
        </div>
      </div>
      <vue-office-docx
        v-else
        :src="docxContent"
        class="docx-content"
        :class="{ 'dark-theme': isDarkMode }"
        @rendered="onDocRendered"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, inject, watch, computed, nextTick } from 'vue'
import axios from 'axios'
import VueOfficeDocx from '@vue-office/docx'
import '@vue-office/docx/lib/index.css'

const props = defineProps({
  docPath: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['close'])

const isDarkMode = inject('isDarkMode')
const loading = ref(true)
const error = ref(null)
const docxContent = ref(null)
const isVisible = ref(false)

const fileName = computed(() => {
  if (!props.docPath) return ''
  return props.docPath.split('/').pop() || '文档预览'
})

// 显示动画处理
onMounted(() => {
  nextTick(() => {
    setTimeout(() => {
      isVisible.value = true
    }, 50)
  })
})

// 关闭预览
function closePreview() {
  isVisible.value = false
  setTimeout(() => {
    emit('close')
  }, 400) // 匹配CSS过渡时间
}

watch(() => props.docPath, loadDocument)
onMounted(loadDocument)

async function loadDocument() {
  if (!props.docPath) return

  loading.value = true
  error.value = null

  try {
    const response = await axios.get(`/api/get-docx-content?file_path=${encodeURIComponent(props.docPath)}`, {
      responseType: 'arraybuffer'
    })
    docxContent.value = response.data
  } catch (err) {
    error.value = '加载文档失败：' + (err.message || '未知错误')
  } finally {
    loading.value = false
  }
}

function onDocRendered() {
  console.log("文档渲染完成")
}
</script>

<style scoped>
.docx-preview-container {
  position: fixed;
  top: 0;
  right: 0;
  width: clamp(350px, 45%, 900px); /* 增加宽度 */
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
}

.docx-preview-container.active {
  transform: translateX(0);
}

.docx-preview-wrapper {
  flex: 1 1 auto;
  overflow: hidden;
  position: relative;
  background-color: hsl(var(--background));
  transition: background-color var(--transition-speed);
}

.docx-content {
  height: 100%;
  width: 100%;
  overflow-y: auto;
  padding: 1.5rem;
  box-sizing: border-box;
}

/* 状态容器样式 */
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

/* 自适应调整 */
@media (max-width: 768px) {
  .docx-preview-container {
    width: 100%;
    max-width: none;
  }
  
  .docx-content {
    padding: 1rem;
  }
}

/* 自定义滚动条样式 */
.docx-content::-webkit-scrollbar {
  width: 8px;
}

.docx-content::-webkit-scrollbar-track {
  background: transparent;
}

.docx-content::-webkit-scrollbar-thumb {
  background-color: hsl(var(--border));
  border-radius: 4px;
}

.docx-content::-webkit-scrollbar-thumb:hover {
  background-color: hsl(var(--muted-foreground));
}
</style>