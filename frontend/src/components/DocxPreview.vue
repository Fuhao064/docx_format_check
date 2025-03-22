<template>
  <div class="docx-preview transition-colors duration-[--transition-speed]" :class="isDarkMode ? 'bg-[hsl(var(--background))]' : 'bg-[hsl(var(--background))]'">
    <div v-if="loading" class="h-full flex flex-col items-center justify-center text-[hsl(var(--muted-foreground))]">
      <svg class="animate-spin -ml-1 mr-3 h-8 w-8" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <span class="mt-3">加载文档中...</span>
    </div>
    <div v-else-if="error" class="h-full flex flex-col items-center justify-center p-4">
      <div class="p-4 rounded-lg text-center max-w-md" :class="isDarkMode ? 'bg-[hsl(var(--destructive)/0.2)] text-[hsl(var(--destructive))] border border-[hsl(var(--destructive)/0.3)]' : 'bg-[hsl(var(--destructive)/0.1)] text-[hsl(var(--destructive))] border border-[hsl(var(--destructive)/0.3)]'">
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
      :class="{'dark-theme': isDarkMode}"
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

}

</script>

<style scoped>
.docx-preview {
  height: 100%;
  overflow-y: auto; /* Scrollbar on the outer container */
}


/* 自定义滚动条样式 */
.docx-preview::-webkit-scrollbar {
  width: 6px;
}

.docx-preview::-webkit-scrollbar-track {
  background: transparent;
}

.docx-preview::-webkit-scrollbar-thumb {
  background-color: hsl(var(--border));
  border-radius: 3px;
}

.docx-preview::-webkit-scrollbar-thumb:hover {
  background-color: hsl(var(--muted-foreground));
}

</style>