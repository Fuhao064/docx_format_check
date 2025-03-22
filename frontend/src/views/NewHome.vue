<template>
  <div class="flex flex-col h-screen">
    <div
      class="h-16 fixed top-0 right-0 z-40 flex items-center justify-between transition-colors duration-200"
      :class="[
        sidebarCollapsed ? 'left-12' : 'left-64',
        isDarkMode
          ? 'bg-gradient-to-b from-zinc-900 via-zinc-900 via-80% to-transparent'
          : 'bg-gradient-to-b from-white via-white via-80% to-transparent',
      ]"
    >
      <div class="flex items-center h-full px-5">
        <div class="flex items-center">
          <h1 class="text-xl font-semibold truncate font-serif italic items-center text-zinc-900 dark:text-zinc-100">
            Scriptor
          </h1>
        </div>
      </div>
      <div class="flex items-center gap-2 px-5">
        <button
          class="p-2 rounded-full hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-600 dark:text-zinc-300"
          @click="resetProcess"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            class="stroke-[2] text-zinc-600 dark:text-zinc-300"
          >
            <path d="M3 2v6h6" stroke="currentColor" />
            <path d="M3 13a9 9 0 1 0 3-7.7L3 8" stroke="currentColor" />
          </svg>
        </button>
        <button class="p-2 rounded-full hover:bg-zinc-200 dark:hover:bg-zinc-700" @click="toggleTheme">
          <svg
            v-if="isDarkMode"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            class="text-zinc-600 dark:text-zinc-300"
          >
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
          </svg>
          <svg
            v-else
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            class="text-zinc-600 dark:text-zinc-300"
          >
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
        </button>
      </div>
    </div>

    <main
      class="flex-1 flex flex-col overflow-hidden"
      :class="isDarkMode ? 'bg-zinc-950 text-zinc-100' : 'bg-white text-zinc-900'"
    >
      <div
        class="flex-1 flex flex-col items-center h-full overflow-y-auto scrollbar-thin pt-20 pb-16 px-5"
        ref="messagesContainer"
      >
        <div v-if="formatErrors.length > 0" class="w-full max-w-3xl mb-6">
          <div
            class="rounded-3xl bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800/40 p-5 shadow-md"
          >
            <div class="flex items-center mb-3">
              <svg class="w-5 h-5 text-red-600 dark:text-red-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
              </svg>
              <h4 class="font-medium text-red-700 dark:text-red-400">发现以下格式问题：</h4>
            </div>
            <ul class="space-y-2">
              <li
                v-for="(error, index) in formatErrors"
                :key="index"
                class="text-sm text-red-700 dark:text-red-300 bg-red-100 dark:bg-red-800/40 rounded-lg p-2.5 transition-colors hover:bg-red-200 dark:hover:bg-red-700/40"
              >
                {{ error.message }}
                <div v-if="error.location" class="text-xs mt-1 text-zinc-600 dark:text-zinc-400">
                  位置: {{ error.location }}
                </div>
              </li>
            </ul>
          </div>
        </div>

        <div v-if="!hasUploadedFile" class="flex-1 flex flex-col items-center justify-center w-full max-w-3xl p-6">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="64"
            height="64"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.5"
            class="mb-6 text-brand dark:text-brand"
          >
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
            <polyline points="10 9 9 9 8 9"></polyline>
          </svg>
          <p class="text-xl font-medium text-zinc-900 dark:text-zinc-100">开始文档处理</p>
          <p class="text-sm mt-2 mb-6 text-zinc-600 dark:text-zinc-400">请上传文档开始与Agent交互</p>
          <button
            @click="triggerFileUpload"
            class="flex items-center gap-2 px-5 py-2.5 rounded-full bg-brand hover:bg-brand-dark text-white transition-colors"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            上传文档
          </button>
        </div>

        <div v-if="hasUploadedFile && !hasUploadedFormat"
          class="flex-1 flex flex-col items-center justify-center w-full max-w-3xl p-6">
          <p class="text-xl font-medium text-zinc-900 dark:text-zinc-100">上传格式要求</p>
          <p class="text-sm mt-2 mb-6 text-zinc-600 dark:text-zinc-400">请上传格式要求文档以继续处理</p>
          <button
            @click="triggerFormatUpload"
            class="flex items-center gap-2 px-5 py-2.5 rounded-full bg-brand hover:bg-brand-dark text-white transition-colors"
          >
            上传格式要求
          </button>
          <button
            @click="useDefaultFormat"
            class="mt-4 px-5 py-2.5 rounded-full bg-zinc-200 dark:bg-zinc-700 hover:bg-zinc-300 dark:hover:bg-zinc-600 text-zinc-900 dark:text-white transition-colors"
          >
            使用默认格式
          </button>
        </div>

        <div v-else class="w-full max-w-3xl flex-1 flex flex-col">
          <div v-if="currentStep >= 0 && currentStep < 5" class="mb-6">
            <div class="rounded-3xl shadow-md overflow-hidden transition-shadow hover:shadow-lg border border-blue-100 dark:border-zinc-700">
              <div
                class="px-5 py-3.5 bg-gradient-to-r from-blue-500 to-blue-700 dark:from-zinc-800 dark:to-zinc-800 text-white"
              >
                <div class="flex items-center">
                  <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
                  </svg>
                  <h2 class="text-lg font-bold">文档处理进度</h2>
                </div>
              </div>
              <div class="space-y-3 p-4 bg-white dark:bg-zinc-900">
                <div
                  v-for="(step, index) in processingSteps"
                  :key="index"
                  class="flex items-center gap-3 p-3 rounded-lg transition-colors"
                  :class="[
                    step.status === 'completed' ? (isDarkMode ? 'bg-green-900/20 border border-green-800/30' : 'bg-green-50 border border-green-200') :
                    step.status === 'in_progress' ? (isDarkMode ? 'bg-blue-900/20 border border-blue-800/30' : 'bg-blue-50 border border-blue-200') :
                    step.status === 'error' ? (isDarkMode ? 'bg-red-900/20 border border-red-800/30' : 'bg-red-50 border border-red-200') :
                    'bg-zinc-100 dark:bg-zinc-800/50 border border-zinc-200 dark:border-zinc-700/30',
                  ]"
                >
                  <div class="w-8 h-8 rounded-full flex items-center justify-center bg-white dark:bg-zinc-700 shadow">
                    <div
                      :class="[
                        step.status === 'completed' ? 'text-green-600 dark:text-green-400' :
                        step.status === 'in_progress' ? 'text-blue-600 dark:text-blue-400 animate-pulse' :
                        step.status === 'error' ? 'text-red-600 dark:text-red-400' :
                        'text-zinc-500 dark:text-zinc-400',
                      ]"
                    >
                      <svg v-if="step.status === 'completed'" class="w-4 h-4" fill="none" stroke="currentColor"
                        viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M5 13l4 4L19 7"></path>
                      </svg>
                      <svg v-else-if="step.status === 'in_progress'" class="w-4 h-4 animate-spin" fill="none"
                        stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M12 4v16m8-8H4"></path>
                      </svg>
                      <svg v-else-if="step.status === 'error'" class="w-4 h-4" fill="none" stroke="currentColor"
                        viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M12 9v3m0 0v3m0-3h3m-3 0H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                      </svg>
                      <span v-else class="text-xs">{{ index + 1 }}</span>
                    </div>
                  </div>
                  <div class="flex-1 space-y-0.5">
                    <p class="text-base font-medium text-zinc-900 dark:text-zinc-100">{{ step.title }}</p>
                    <p class="text-xs text-zinc-600 dark:text-zinc-400">{{ step.description }}</p>
                    <div v-if="step.status === 'in_progress'"
                      class="w-full bg-gray-200 dark:bg-zinc-600 rounded-full h-1 overflow-hidden mt-1">
                      <div class="bg-blue-500 dark:bg-blue-400 h-full animate-pulse" style="width: 60%;"></div>
                    </div>
                  </div>
                  <div class="text-xs font-medium whitespace-nowrap" :class="[
                    step.status === 'completed' ? 'text-green-600 dark:text-green-400' :
                    step.status === 'in_progress' ? 'text-blue-600 dark:text-blue-400' :
                    step.status === 'error' ? 'text-red-600 dark:text-red-400' :
                    'text-zinc-500 dark:text-zinc-400',
                  ]">
                    {{ step.status === 'completed' ? '已完成' :
                    step.status === 'in_progress' ? '进行中' :
                    step.status === 'error' ? '错误' : '等待' }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 底部输入框区域 -->
    <div v-if="currentStep >= 5" class="fixed bottom-0 left-0 right-0 flex justify-center items-center bg-transparent py-4 transition-colors duration-200 z-30">
      <div class="flex flex-row gap-2 justify-center w-full max-w-3xl py-3 px-4">
        <div class="query-bar group bg-white dark:bg-zinc-800/95 duration-100 relative w-full ring-1 ring-zinc-300 dark:ring-zinc-700 ring-inset overflow-hidden hover:ring-zinc-400 dark:hover:ring-zinc-600 focus-within:ring-1 focus-within:ring-brand hover:focus-within:ring-brand pb-12 px-2 rounded-3xl shadow-md backdrop-blur-sm">
          <div class="relative z-10">
            <span class="absolute px-3 py-5 text-zinc-500 dark:text-zinc-400 pointer-events-none" 
                  v-if="!userInput.length">输入您的问题...</span>
            <textarea 
              dir="auto" 
              v-model="userInput"
              @keydown.enter.prevent="handleEnterKey($event)"
              class="w-full px-3 bg-transparent focus:outline-none text-zinc-900 dark:text-zinc-100 align-bottom min-h-14 pt-5 my-0 mb-5 resize-none scrollbar-thin"
              rows="1"
            ></textarea>
          </div>
          <div class="flex gap-1.5 absolute inset-x-0 bottom-0 border-2 border-transparent p-2 max-w-full">
            <button 
              class="inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm font-medium leading-[normal] cursor-pointer focus-visible:outline-none h-9 rounded-full py-2 relative px-2 transition-all duration-150 bg-transparent border w-9 aspect-square border-zinc-300 dark:border-zinc-600 hover:border-zinc-400 dark:hover:border-zinc-500 text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-700" 
              type="button" 
              aria-label="重置" 
              @click="resetProcess"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="stroke-[2]">
                <path d="M3 2v6h6" stroke="currentColor" />
                <path d="M3 13a9 9 0 1 0 3-7.7L3 8" stroke="currentColor" />
              </svg>
            </button>
            <div class="flex grow gap-1.5 max-w-full">
              <div class="grow flex gap-1.5 max-w-full">
                <button 
                  v-if="processingComplete"
                  @click="downloadReport" 
                  class="inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm font-medium leading-[normal] cursor-pointer focus-visible:outline-none text-zinc-700 dark:text-zinc-200 h-9 rounded-full px-3.5 py-2 transition-colors duration-100 relative overflow-hidden border bg-transparent border-zinc-300 dark:border-zinc-600 hover:border-zinc-400 dark:hover:border-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-700"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="stroke-[2]">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" />
                    <path d="M7 10l5 5 5-5" stroke="currentColor" />
                    <path d="M12 15V3" stroke="currentColor" />
                  </svg>
                  <span>下载报告</span>
                </button>
                <button 
                  v-if="processingComplete"
                  @click="downloadMarkedDocument" 
                  class="inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm font-medium leading-[normal] cursor-pointer focus-visible:outline-none text-zinc-700 dark:text-zinc-200 h-9 rounded-full px-3.5 py-2 transition-colors duration-100 relative overflow-hidden border bg-transparent border-zinc-300 dark:border-zinc-600 hover:border-zinc-400 dark:hover:border-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-700"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="stroke-[2]">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" />
                    <path d="M14 2v6h6" stroke="currentColor" />
                    <path d="M16 13H8" stroke="currentColor" />
                    <path d="M16 17H8" stroke="currentColor" />
                    <path d="M10 9H9H8" stroke="currentColor" />
                  </svg>
                  <span>标记文档</span>
                </button>
              </div>
            </div>
            <div class="ml-auto flex flex-row items-end gap-1">
              <button 
                class="group flex flex-col justify-center rounded-full focus:outline-none" 
                type="button" 
                @click="sendMessage" 
                :disabled="!userInput.trim().length"
                :class="userInput.trim().length ? 'opacity-100' : 'opacity-50 cursor-default'"
              >
                <div class="h-9 relative aspect-square flex flex-col items-center justify-center rounded-full ring-inset before:absolute before:inset-0 before:rounded-full before:bg-brand before:ring-0 before:transition-all duration-500 bg-zinc-100 dark:bg-zinc-700 text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="stroke-[2] relative">
                    <path d="M5 11L12 4M12 4L19 11M12 4V21" stroke="currentColor"></path>
                  </svg>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <input type="file" ref="fileInput" @change="handleFileUpload" accept=".docx" class="hidden" />
    <input type="file" ref="formatInput" @change="handleFormatUpload" accept=".json" class="hidden" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'

// 获取主题模式和通知函数
const isDarkMode = inject('isDarkMode', ref(true))
const showNotification = inject('showNotification', null)
const sidebarCollapsed = inject('sidebarCollapsed', ref(true)) // 注入侧边栏状态

// 切换主题函数
const toggleTheme = inject('toggleTheme', () => {
  isDarkMode.value = !isDarkMode.value

})

// 路由
const router = useRouter()
const route = useRoute()

// 文件上传相关
const fileInput = ref(null)
const formatInput = ref(null)
const hasUploadedFile = ref(false)
const hasUploadedFormat = ref(false)
const uploadedFile = ref(null)
const uploadedFileName = ref('')

// 对话相关
const messagesContainer = ref(null)
const userInput = ref('')
const messages = ref([])
const currentDocumentPath = ref('')
const currentConfigPath = ref('')
const currentStep = ref(0)
const processingComplete = ref(false)
const processingSteps = ref([
  { id: 1, title: '上传文档', description: '上传需要检查格式的文档', status: 'pending' },
  { id: 2, title: '上传格式要求', description: '上传格式要求文档或使用默认格式', status: 'pending' },
  { id: 3, title: '检查格式规范', description: '根据格式要求检查文档格式', status: 'pending' },
  { id: 4, title: '生成分析报告', description: '生成格式检查报告', status: 'pending' }
])

// 格式错误信息
const formatErrors = ref([])

// 对话建议
const suggestions = [
  '请分析文档中的格式问题',
  '如何修复文档中的格式错误？',
  '生成格式修正报告',
  '帮我优化文档的整体格式'
]

// 监听消息变化，自动滚动到底部
watch(messages,() => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}, { deep: true })

//触发文件上传
function triggerFileUpload() {
  fileInput.value.click()
}

// 触发格式要求上传
function triggerFormatUpload() {
  formatInput.value.click()
}

// 处理文件上传
async function handleFileUpload(event) {
  const file = event.target.files[0]
  if (!file) return

  uploadedFileName.value = file.name
  const formData = new FormData()
  formData.append('file', file)

  try {
    showNotification('info', '文件上传中', '正在上传文档，请稍候...', 0)
    const response = await axios.post('/api/upload-files', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    if (response.data.success) {
      uploadedFile.value = file
      hasUploadedFile.value = true
      processingSteps.value[0].status = 'completed'
      currentStep.value = 1
      currentDocumentPath.value = response.data.file_path || response.data.file.path
      showNotification('success', '上传成功', `文件 "${file.name}" 已成功上传`, 3000)
    } else {
      throw new Error(response.data.message || '上传失败')
    }
  } catch (error) {
    console.error('上传文件时出错:', error)
    showNotification('error', '上传失败', `上传文件时出错: ${error.message || error}`, 5000)
    processingSteps.value[0].status = 'error'
  }

  event.target.value = ''
}

// 处理格式文件上传
async function handleFormatUpload(event) {
  const file = event.target.files[0]
  if (!file) return

  const formData = new FormData()
  formData.append('format_file', file)

  try {
    showNotification('info', '格式要求上传中', '正在上传格式要求，请稍候...', 0)
    const response = await axios.post('/api/upload-format', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    if (response.data.success) {
      hasUploadedFormat.value = true
      currentConfigPath.value = response.data.file_path || response.data.config_path
      processingSteps.value[1].status = 'completed'
      currentStep.value = 2
      showNotification('success', '上传成功', `格式要求 "${file.name}" 已成功上传`, 3000)
      processDocument()
    } else {
      throw new Error(response.data.message || '上传失败')
    }
  } catch (error) {
    console.error('上传格式文件时出错:', error)
    showNotification('error', '上传失败', `上传格式文件时出错: ${error.message || error}`, 5000)
    processingSteps.value[1].status = 'error'
  }

  event.target.value = ''
}

// 处理文档格式检查
async function processDocument() {
  try {
    showNotification('info', '文档处理中', '正在检查文档格式，请稍候...', 0)
    processingSteps.value[2].status = 'in_progress'
    const response = await axios.post('/api/check-format', {
      doc_path: currentDocumentPath.value,
      config_path: currentConfigPath.value
    })

    if (response.data.success) {
      formatErrors.value = response.data.errors || []
      processingSteps.value[2].status = 'completed'
      currentStep.value = 3
      generateReport()
    } else {
      throw new Error(response.data.message || '格式检查失败')
    }
  } catch (error) {
    console.error('处理文档时出错:', error)
    showNotification('error', '处理失败', `格式检查时出错: ${error.message || error}`, 5000)
    processingSteps.value[2].status = 'error'
  }
}

// 生成报告
async function generateReport() {
  try {
    showNotification('info', '生成报告中', '正在生成格式分析报告，请稍候...', 0)
    processingSteps.value[3].status = 'in_progress'
    const response = await axios.post('/api/generate-report', {
      doc_path: currentDocumentPath.value,
      errors: formatErrors.value
    })

    if (response.data.success) {
      processingSteps.value[3].status = 'completed'
      processingComplete.value = true
      currentStep.value = 5
      messages.value.push({
        content: '文档格式分析已完成，我发现了' + (formatErrors.value ? formatErrors.value.length : '一些') +
          '个格式问题。您可以询问我关于文档格式的任何问题，或者请我帮您修复这些问题。',
        sender: 'system',
        timestamp: new Date()
      })
      showNotification('success', '处理完成', '文档格式分析已完成', 3000)
    } else {
      throw new Error(response.data.message || '生成报告失败')
    }
  } catch (error) {
    console.error('生成报告时出错:', error)
    showNotification('error', '处理失败', `生成报告时出错: ${error.message || error}`, 5000)
    processingSteps.value[3].status = 'error'
  }
}

// 使用默认格式
async function useDefaultFormat() {
  try {
    showNotification('info', '使用默认格式', '正在应用默认格式...', 0)
    const response = await axios.get('/api/use-default-format')
    if (response.data.success) {
      hasUploadedFormat.value = true
      currentConfigPath.value = response.data.config_path
      processingSteps.value[1].status = 'completed'
      currentStep.value = 2
      showNotification('success', '使用默认格式', '已应用默认格式进行处理', 3000)
      processDocument()
    } else {
      throw new Error(response.data.message || '应用默认格式失败')
    }
  } catch (error) {
    console.error('应用默认格式时出错:', error)
    showNotification('error', '处理失败', `应用默认格式时出错: ${error.message || error}`, 5000)
    processingSteps.value[1].status = 'error'
  }
}

// 下载报告
async function downloadReport() {
  try {
    showNotification('info', '下载中', '正在准备下载报告...', 3000)
    const response = await axios.get('/api/download-report', {
      params: { doc_path: currentDocumentPath.value },
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `${uploadedFileName.value.split('.')[0]}_report.docx`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    showNotification('success', '下载完成', '报告已成功下载', 3000)
  } catch (error) {
    console.error('下载报告时出错:', error)
    showNotification('error', '下载失败', `下载报告时出错: ${error.message || error}`, 5000)
  }
}

// 下载修正文档
async function downloadMarkedDocument() {
  try {
    showNotification('info', '下载中', '正在准备下载标记错误的文档...', 3000)
    const response = await axios.get('/api/download-marked-document', {
      params: { doc_path: currentDocumentPath.value },
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `marked_${uploadedFileName.value}`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    showNotification('success', '下载完成', '标记错误的文档已成功下载', 3000)
  } catch (error) {
    console.error('下载标记文档时出错:', error)
    showNotification('error', '下载失败', `下载标记文档时出错: ${error.message || error}`, 5000)
  }
}

function sendMessage() {
  //向后端Agent发送消息

}

// 处理回车键
function handleEnterKey(e) {
  if (!e.shiftKey) {
    sendMessage()
  }
}


// 重置处理流程
function resetProcess() {
  currentStep.value = 0
  uploadedFile.value = null
  hasUploadedFile.value = false
  uploadedFileName.value = ''
  messages.value = []
  formatErrors.value = []
  processingComplete.value = false
  processingSteps.value.forEach(step => step.status = 'pending')
  showNotification('info', '已重置', '处理流程已重置，您可以上传新的文档', 3000)
}
</script>

<style scoped>
/* 自定义滚动条样式 */
.scrollbar-thin::-webkit-scrollbar {
  width: 4px;
}

.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}

.scrollbar-thin::-webkit-scrollbar-thumb {
  background-color: rgba(59, 130, 246, 0.5);
  border-radius: 2px;
}

.scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background-color: rgba(59, 130, 246, 0.8);
}

/* 自定义颜色 */
:root {
  --brand: #3b82f6;
  --brand-dark: #2563eb;
  --background: #f9fafb;
}

.dark {
  --brand: #60a5fa;
  --brand-dark: #3b82f6;
  --background: #18181b;
}
</style>
