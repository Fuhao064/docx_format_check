<template>
  <div class="flex flex-col h-screen overflow-hidden" :class="isDarkMode ? 'bg-zinc-900 text-zinc-100' : 'bg-white text-gray-900'">
    <!-- 顶部标题栏 -->
    <div class="flex items-center justify-between p-4 border-b" :class="isDarkMode ? 'border-zinc-800' : 'border-gray-200'">
      <h1 class="text-xl font-semibold">多Agent文档处理系统</h1>
      <div class="flex items-center space-x-2">
        <button 
          @click="toggleDocPreview"
          class="p-2 rounded-md transition-colors"
          :class="isDarkMode ? 'hover:bg-zinc-800 text-zinc-400 hover:text-zinc-100' : 'hover:bg-gray-200 text-gray-500 hover:text-gray-700'"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
            <polyline points="10 9 9 9 8 9"></polyline>
          </svg>
        </button>
        <button 
          @click="toggleDarkMode"
          class="p-2 rounded-md transition-colors"
          :class="isDarkMode ? 'hover:bg-zinc-800 text-zinc-400 hover:text-zinc-100' : 'hover:bg-gray-200 text-gray-500 hover:text-gray-700'"
        >
          <svg v-if="isDarkMode" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="5"></circle>
            <line x1="12" y1="1" x2="12" y2="3"></line>
            <line x1="12" y1="21" x2="12" y2="23"></line>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
            <line x1="1" y1="12" x2="3" y2="12"></line>
            <line x1="21" y1="12" x2="23" y2="12"></line>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
          </svg>
        </button>
      </div>
    </div>
    
    <!-- 主内容区域 -->
    <div class="flex-1 flex overflow-hidden">
      <!-- 聊天界面 -->
      <div :class="['flex-1 flex flex-col overflow-hidden', showDocPreview ? 'w-1/2' : 'w-full']">
        <ChatInterface />
      </div>
      
      <!-- 文档预览区域 -->
      <div 
        v-if="showDocPreview && uploadedFile"
        class="w-1/2 border-l flex flex-col overflow-hidden"
        :class="isDarkMode ? 'border-zinc-800' : 'border-gray-200'"
      >
        <div class="flex items-center justify-between p-3 border-b" :class="isDarkMode ? 'border-zinc-800' : 'border-gray-200'">
          <h3 class="font-medium truncate" :class="isDarkMode ? 'text-zinc-100' : 'text-gray-900'">
            {{ uploadedFileName || '文档预览' }}
          </h3>
          <button 
            @click="toggleDocPreview"
            class="p-1 rounded-md transition-colors"
            :class="isDarkMode ? 'hover:bg-zinc-800 text-zinc-400 hover:text-zinc-100' : 'hover:bg-gray-200 text-gray-500 hover:text-gray-700'"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m15 18-6-6 6-6"></path>
            </svg>
          </button>
        </div>
        
        <div class="flex-1 overflow-hidden">
          <DocxPreview :file-path="uploadedFile" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, provide } from 'vue'
import ChatInterface from '../components/ChatInterface.vue'
import DocxPreview from '../components/DocxPreview.vue'

// 获取主题模式
const isDarkMode = inject('isDarkMode', ref(true))

// 提供给子组件
provide('isDarkMode', isDarkMode)

// 文档预览状态
const showDocPreview = ref(true)
const uploadedFile = ref(null)
const uploadedFileName = ref('')

// 切换文档预览
function toggleDocPreview() {
  showDocPreview.value = !showDocPreview.value
}

// 切换暗黑模式
function toggleDarkMode() {
  isDarkMode.value = !isDarkMode.value
}

// 监听文件上传事件
provide('onFileUploaded', (filePath, fileName) => {
  uploadedFile.value = filePath
  uploadedFileName.value = fileName
  showDocPreview.value = true
})
</script>