<template>
  <div class="flex flex-col h-full">
    <!-- 流程式处理区域 -->
    <div class="flex-1 flex overflow-hidden">
      <!-- 主内容区域 -->
      <div class="flex-1 flex flex-col overflow-hidden p-4" :class="isDarkMode ? 'bg-zinc-900' : 'bg-gray-50'">
        <div class="flex-1 overflow-y-auto scrollbar-thin mb-4">
          <div v-if="currentStep === 0" class="h-full flex flex-col items-center justify-center">
            <div class="w-16 h-16 mb-4" :class="isDarkMode ? 'text-blue-400' : 'text-blue-700'">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
              </svg>
            </div>
            <p class="text-lg font-medium" :class="isDarkMode ? 'text-zinc-100' : 'text-gray-900'">开始文档格式处理</p>
            <p class="text-sm mt-2 mb-6" :class="isDarkMode ? 'text-zinc-400' : 'text-gray-700'">请上传文档开始处理</p>
            
            <!-- 上传按钮 -->
            <button 
              @click="triggerFileUpload"
              class="flex items-center justify-center gap-2 px-4 py-2 rounded-md transition-colors"
              :class="isDarkMode ? 'bg-blue-600 hover:bg-blue-700 text-white' : 'bg-blue-600 hover:bg-blue-700 text-white'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="17 8 12 3 7 8"></polyline>
                <line x1="12" y1="3" x2="12" y2="15"></line>
              </svg>
              <span>上传文档</span>
            </button>
          </div>
          
          <!-- 步骤2：上传格式要求 -->
          <div v-else-if="currentStep === 1" class="h-full flex flex-col items-center justify-center">
            <div class="w-16 h-16 mb-4" :class="isDarkMode ? 'text-blue-400' : 'text-blue-700'">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
              </svg>
            </div>
            <p class="text-lg font-medium" :class="isDarkMode ? 'text-zinc-100' : 'text-gray-900'">上传格式要求</p>
            <p class="text-sm mt-2 mb-6" :class="isDarkMode ? 'text-zinc-400' : 'text-gray-700'">请上传格式要求文档或JSON文件</p>
            
            <div class="flex gap-4">
              <!-- 上传格式文档按钮 -->
              <button 
                @click="triggerFormatFileUpload"
                class="flex items-center justify-center gap-2 px-4 py-2 rounded-md transition-colors"
                :class="isDarkMode ? 'bg-blue-600 hover:bg-blue-700 text-white' : 'bg-blue-600 hover:bg-blue-700 text-white'"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                </svg>
                <span>上传格式文档</span>
              </button>
              
              <!-- 使用默认格式按钮 -->
              <button 
                @click="useDefaultFormat"
                class="flex items-center justify-center gap-2 px-4 py-2 rounded-md transition-colors"
                :class="isDarkMode ? 'bg-zinc-700 hover:bg-zinc-600 text-white' : 'bg-gray-200 hover:bg-gray-300 text-gray-900'"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="7 10 12 15 17 10"></polyline>
                  <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                <span>使用默认格式</span>
              </button>
            </div>
          </div>
          
          <!-- 处理步骤显示 -->
          <div v-else-if="currentStep >= 2" class="h-full flex flex-col">
            <h2 class="text-xl font-semibold mb-6" :class="isDarkMode ? 'text-zinc-100' : 'text-gray-900'">文档处理进度</h2>
            
            <!-- 处理步骤UI -->
            <div class="flex flex-col space-y-4 mb-8">
              <div v-for="(step, index) in processingSteps" :key="index" 
                class="flex items-center p-3 rounded-lg" 
                :class="[
                  step.status === 'completed' 
                    ? isDarkMode ? 'bg-green-900/20' : 'bg-green-50' 
                    : step.status === 'in_progress'
                      ? isDarkMode ? 'bg-blue-900/20' : 'bg-blue-50'
                      : step.status === 'error'
                        ? isDarkMode ? 'bg-red-900/20' : 'bg-red-50'
                        : isDarkMode ? 'bg-zinc-800/50' : 'bg-gray-100'
                ]"
              >
                <div class="w-8 h-8 rounded-full flex items-center justify-center mr-3"
                  :class="[
                    step.status === 'completed' 
                      ? isDarkMode ? 'bg-green-600 text-white' : 'bg-green-600 text-white'
                      : step.status === 'in_progress'
                        ? isDarkMode ? 'bg-blue-600 text-white' : 'bg-blue-600 text-white'
                        : step.status === 'error'
                          ? isDarkMode ? 'bg-red-600 text-white' : 'bg-red-600 text-white'
                          : isDarkMode ? 'bg-zinc-700 text-zinc-400' : 'bg-gray-300 text-gray-700'
                  ]"
                >
                  <svg v-if="step.status === 'completed'" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                  <svg v-else-if="step.status === 'in_progress'" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12 6 12 12 16 14"></polyline>
                  </svg>
                  <svg v-else-if="step.status === 'error'" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                  </svg>
                  <span v-else>{{ index + 1 }}</span>
                </div>
                <div class="flex-1">
                  <p class="font-medium" :class="isDarkMode ? 'text-zinc-100' : 'text-gray-900'">{{ step.title }}</p>
                  <p class="text-sm" :class="isDarkMode ? 'text-zinc-400' : 'text-gray-700'">{{ step.description }}</p>
                </div>
                <div class="ml-4">
                  <span class="text-sm font-medium"
                    :class="[
                      step.status === 'completed' 
                        ? isDarkMode ? 'text-green-400' : 'text-green-700'
                        : step.status === 'in_progress'
                          ? isDarkMode ? 'text-blue-400' : 'text-blue-700'
                          : step.status === 'error'
                            ? isDarkMode ? 'text-red-400' : 'text-red-700'
                            : isDarkMode ? 'text-zinc-500' : 'text-gray-600'
                    ]"
                  >
                    {{ 
                      step.status === 'completed' ? '已完成' :
                      step.status === 'in_progress' ? '处理中' :
                      step.status === 'error' ? '错误' : '等待中'
                    }}
                  </span>
                </div>
              </div>
            </div>
            
            <!-- 错误信息显示 -->
            <div v-if="formatErrors.length > 0" class="mt-4 mb-8">
              <h3 class="text-lg font-medium mb-3" :class="isDarkMode ? 'text-zinc-100' : 'text-gray-900'">格式检查结果</h3>
              <div class="rounded-lg overflow-hidden shadow-sm border" :class="isDarkMode ? 'bg-red-900/20 border-red-800/30' : 'bg-red-50 border-red-200'">
                <div class="p-4">
                  <h4 class="font-medium mb-2" :class="isDarkMode ? 'text-red-400' : 'text-red-700'">发现以下格式问题：</h4>
                  <ul class="list-disc pl-5 space-y-2">
                    <li v-for="(error, index) in formatErrors" :key="index" 
                      class="text-sm p-2 rounded-md" 
                      :class="isDarkMode ? 'bg-red-900/30 text-zinc-300' : 'bg-red-100 text-gray-900'"
                    >
                      {{ error.message }}
                    </li>
                  </ul>
                </div>
              </div>
            </div>
            
            <!-- 完成后的操作按钮 -->
            <div v-if="processingComplete" class="mt-auto flex justify-end space-x-3 pt-4">
              <button 
                @click="downloadReport"
                class="flex items-center justify-center gap-2 px-4 py-2 rounded-md transition-colors"
                :class="isDarkMode ? 'bg-blue-600 hover:bg-blue-700 text-white' : 'bg-blue-600 hover:bg-blue-700 text-white'"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="7 10 12 15 17 10"></polyline>
                  <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                <span>下载报告</span>
              </button>
              <button 
                @click="resetProcess"
                class="flex items-center justify-center gap-2 px-4 py-2 rounded-md transition-colors"
                :class="isDarkMode ? 'bg-zinc-700 hover:bg-zinc-600 text-white' : 'bg-gray-200 hover:bg-gray-300 text-gray-900'"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M3 2v6h6"></path>
                  <path d="M21 12A9 9 0 0 0 6 5.3L3 8"></path>
                  <path d="M21 22v-6h-6"></path>
                  <path d="M3 12a9 9 0 0 0 15 6.7l3-2.7"></path>
                </svg>
                <span>重新开始</span>
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 文档预览区域 -->
      <div 
        v-if="showDocPreview" 
        class="w-1/2 border-l flex flex-col overflow-hidden"
        :class="isDarkMode ? 'border-zinc-800 bg-zinc-900' : 'border-gray-200 bg-white'"
      >
        <div class="flex items-center justify-between p-3 border-b" :class="isDarkMode ? 'border-zinc-800' : 'border-gray-200'">
          <h3 class="font-medium" :class="isDarkMode ? 'text-zinc-100' : 'text-gray-900'">{{ uploadedFileName || '文档预览' }}</h3>
          <button 
            @click="showDocPreview = false"
            class="p-1 rounded-md transition-colors"
            :class="isDarkMode ? 'hover:bg-zinc-800 text-zinc-400 hover:text-zinc-100' : 'hover:bg-gray-200 text-gray-500 hover:text-gray-700'"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        
        <div class="flex-1 overflow-hidden">
          <DocxPreview :file-path="uploadedFile" />
        </div>
      </div>
    </div>
    
    <!-- 隐藏的文件上传输入 -->
    <input 
      type="file" 
      ref="fileInput" 
      @change="handleFileUpload" 
      accept=".docx" 
      class="hidden"
    />
    
    <!-- 隐藏的格式文件上传输入 -->
    <input 
      type="file" 
      ref="formatFileInput" 
      @change="handleFormatFileUpload" 
      accept=".docx,.json" 
      class="hidden"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject, watch } from 'vue'
import axios from 'axios'
import DocxPreview from '../components/DocxPreview.vue'

// 获取主题模式
const isDarkMode = inject('isDarkMode')

// 获取通知函数
const showNotification = inject('showNotification', null)

// 文件上传相关
const fileInput = ref(null)
const formatFileInput = ref(null)
const uploadedFile = ref(null)
const uploadedFormatFile = ref(null)
const uploadedFileName = ref('')
const uploadedFormatFileName = ref('')
const showDocPreview = ref(false)

// 处理步骤
const currentStep = ref(0)
const processingSteps = ref([
  {
    id: 1,
    title: '上传文档',
    description: '上传需要检查格式的文档',
    status: 'pending'
  },
  {
    id: 2,
    title: '上传格式要求',
    description: '上传格式要求文档或使用默认格式',
    status: 'pending'
  },
  {
    id: 3,
    title: '解析文档结构',
    description: '分析文档的段落和结构',
    status: 'pending'
  },
  {
    id: 4,
    title: '检查格式规范',
    description: '根据格式要求检查文档格式',
    status: 'pending'
  },
  {
    id: 5,
    title: '生成分析报告',
    description: '生成格式检查报告',
    status: 'pending'
  }
])

// 格式错误信息
const formatErrors = ref([])
const processingComplete = ref(false)

// 触发文件上传
function triggerFileUpload() {
  fileInput.value.click()
}

// 触发格式文件上传
function triggerFormatFileUpload() {
  formatFileInput.value.click()
}

// 处理文件上传
async function handleFileUpload(event) {
  const file = event.target.files[0]
  if (!file) return
  
  uploadedFileName.value = file.name
  
  // 创建FormData对象
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    // 显示上传中通知
    if (showNotification) {
      showNotification('info', '文件上传中', '正在上传文档，请稍候...', 0)
    }
    
    // 上传文件到服务器
    const response = await axios.post('/api/upload-files', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (response.data.success) {
      uploadedFile.value = response.data.file_path
      showDocPreview.value = true
      
      // 更新步骤状态
      processingSteps.value[0].status = 'completed'
      
      // 进入下一步
      currentStep.value = 1
      
      // 显示成功通知
      if (showNotification) {
        showNotification('success', '上传成功', `文件 "${file.name}" 已成功上传`, 3000)
      }
    } else {
      // 显示错误通知
      if (showNotification) {
        showNotification('error', '上传失败', response.data.message || '文件上传失败', 5000)
      }
    }
  } catch (error) {
    console.error('上传文件时出错:', error)
    
    // 显示错误通知
    if (showNotification) {
      showNotification('error', '上传失败', `上传文件时出错: ${error.message}`, 5000)
    }
  }
  
  // 清空文件输入，允许重新选择同一文件
  event.target.value = ''
}

// 处理格式文件上传
async function handleFormatFileUpload(event) {
  const file = event.target.files[0]
  if (!file) return
  
  uploadedFormatFileName.value = file.name
  
  // 创建FormData对象
  const formData = new FormData()
  formData.append('file', file)
  formData.append('type', 'format')
  
  try {
    // 显示上传中通知
    if (showNotification) {
      showNotification('info', '格式文件上传中', '正在上传格式要求文档，请稍候...', 0)
    }
    
    // 上传文件到服务器
    const response = await axios.post('/api/upload-format', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (response.data.success) {
      uploadedFormatFile.value = response.data.file_path
      
      // 更新步骤状态
      processingSteps.value[1].status = 'completed'
      
      // 开始处理文档
      startProcessing()
      
      // 显示成功通知
      if (showNotification) {
        showNotification('success', '上传成功', `格式文件 "${file.name}" 已成功上传`, 3000)
      }
    } else {
      // 显示错误通知
      if (showNotification) {
        showNotification('error', '上传失败', response.data.message || '格式文件上传失败', 5000)
      }
    }
  } catch (error) {
    console.error('上传格式文件时出错:', error)
    
    // 显示错误通知
    if (showNotification) {
      showNotification('error', '上传失败', `上传格式文件时出错: ${error.message}`, 5000)
    }
  }
  
  // 清空文件输入，允许重新选择同一文件
  event.target.value = ''
}

// 使用默认格式
function useDefaultFormat() {
  // 更新步骤状态
  processingSteps.value[1].status = 'completed'
  
  // 开始处理文档
  startProcessing()
  
  // 显示通知
  if (showNotification) {
    showNotification('info', '使用默认格式', '将使用系统默认格式进行检查', 3000)
  }
}

// 开始处理文档
async function startProcessing() {
  // 进入处理步骤
  currentStep.value = 2
  
  try {
    // 更新步骤状态 - 解析文档结构
    processingSteps.value[2].status = 'in_progress'
    
    // 发送分析请求
    const response = await axios.post('/api/check-format', {
      doc_path: uploadedFile.value,
      format_path: uploadedFormatFile.value || 'default'
    })
    
    // 更新步骤状态
    processingSteps.value[2].status = 'completed'
    processingSteps.value[3].status = 'in_progress'
    
    // 检查格式规范
    const formatResponse = await axios.post('/api/check-format', {
      doc_path: uploadedFile.value,
      format_path: uploadedFormatFile.value || 'default'
    })
    
    // 更新步骤状态
    processingSteps.value[3].status = 'completed'
    processingSteps.value[4].status = 'in_progress'
    
    // 生成分析报告
    const reportResponse = await axios.post('/api/generate-report', {
      doc_path: uploadedFile.value,
      format_path: uploadedFormatFile.value || 'default'
    })
    
    // 更新步骤状态
    processingSteps.value[4].status = 'completed'
    
    // 设置格式错误信息
    formatErrors.value = formatResponse.data.errors || []
    
    // 设置处理完成
    processingComplete.value = true
    
    // 显示成功通知
    if (showNotification) {
      showNotification('success', '处理完成', '文档格式分析已完成', 3000)
    }
  } catch (error) {
    console.error('处理文档时出错:', error)
    
    // 更新当前正在进行的步骤状态为错误
    for (const step of processingSteps.value) {
      if (step.status === 'in_progress') {
        step.status = 'error'
        break
      }
    }
    
    // 显示错误通知
    if (showNotification) {
      showNotification('error', '处理失败', `处理文档时出错: ${error.message}`, 5000)
    }
  }
}

// 下载报告
function downloadReport() {
  // 实现下载报告的逻辑
  window.location.href = '/api/download-report?doc_path=' + encodeURIComponent(uploadedFile.value)
}

// 重置处理流程
function resetProcess() {
  currentStep.value = 0
  uploadedFile.value = null
  uploadedFormatFile.value = null
  uploadedFileName.value = ''
  uploadedFormatFileName.value = ''
  showDocPreview.value = false
  formatErrors.value = []
  processingComplete.value = false
  
  // 重置所有步骤状态
  processingSteps.value.forEach(step => {
    step.status = 'pending'
  })
}

// 组件挂载时
onMounted(() => {
  // 可以在这里添加初始化逻辑
})
</script>

<style scoped>
/* 自定义滚动条样式 */
.scrollbar-thin::-webkit-scrollbar {
  width: 4px;
}

.scrollbar-thin::-webkit-scrollbar-track {
  background: v-bind('isDarkMode ? "#18181b" : "#f9fafb"');
}

.scrollbar-thin::-webkit-scrollbar-thumb {
  background-color: v-bind('isDarkMode ? "#3f3f46" : "#94a3b8"');
  border-radius: 2px;
}

.scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background-color: v-bind('isDarkMode ? "#52525b" : "#64748b"');
}

/* 消息动画 */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.flex-1 > div {
  animation: fadeIn 0.3s ease-out forwards;
}
</style>
