<template>
  <div class="min-h-screen bg-gray-900 text-gray-100 flex flex-col overflow-hidden">
    <!-- 顶部标题栏 -->
    <header class="bg-gray-800 p-4 shadow-md flex justify-between items-center">
      <h1 class="text-xl font-bold">{{ title }}</h1>
      <div>
        <button 
          v-if="docxUrl" 
          @click="downloadDocx" 
          class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md transition-colors"
        >
          下载文档
        </button>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="flex-grow flex overflow-hidden">
      <!-- 左侧对话区域 -->
      <div class="w-2/3 flex flex-col p-4 overflow-hidden">
        <!-- 模型选择组件 -->
        <ModelManager class="mb-4" />
        <!-- 消息列表 -->
        <div class="flex-grow overflow-y-auto mb-4 space-y-4 pr-2" ref="messagesContainer">
          <div v-for="(message, index) in messages" :key="index" 
               :class="{'flex justify-end': message.sender === 'user'}">
            <div :class="{
              'bg-blue-600 text-white rounded-lg p-3 max-w-3/4': message.sender === 'user',
              'bg-gray-700 text-white rounded-lg p-3 max-w-3/4': message.sender === 'system'
            }">
              {{ message.content }}
            </div>
          </div>
        </div>

        <!-- 进度条 -->
        <div v-if="showProgress" class="mb-4">
          <div class="flex justify-between text-sm text-gray-400 mb-1">
            <span>处理进度</span>
            <span>{{ completedSteps }}/{{ totalSteps }}</span>
          </div>
          <div class="w-full bg-gray-700 rounded-full h-2.5">
            <div class="bg-blue-600 h-2.5 rounded-full" :style="{ width: `${progressPercentage}%` }"></div>
          </div>
          <div class="mt-2 space-y-1">
            <div v-for="step in executionSteps" :key="step.id" class="flex items-center">
              <div :class="{
                'w-4 h-4 mr-2 rounded-full': true,
                'bg-blue-600': step.status === 'completed',
                'bg-yellow-500 animate-pulse': step.status === 'in_progress',
                'bg-gray-600': step.status === 'pending',
                'bg-red-500': step.status === 'error'
              }"></div>
              <span>{{ step.text }}</span>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="flex space-x-2">
          <input 
            v-model="userInput" 
            @keyup.enter="sendMessage"
            placeholder="请输入消息..."
            class="flex-grow bg-gray-800 text-white px-4 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <label 
            v-if="!docxFile"
            class="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-md cursor-pointer transition-colors"
          >
            上传文件
            <input 
              type="file" 
              accept=".docx" 
              class="hidden" 
              @change="handleFileUpload"
            />
          </label>
          <button 
            @click="sendMessage" 
            class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md transition-colors"
          >
            发送
          </button>
          <button 
            @click="resetConversation" 
            class="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-md transition-colors"
          >
            重置
          </button>
        </div>
      </div>

      <!-- 右侧文档预览区域 -->
      <div class="w-1/3 bg-gray-800 p-4 overflow-hidden flex flex-col">
        <h2 class="text-lg font-semibold mb-4">文档预览</h2>
        <div class="flex-grow overflow-y-auto bg-white rounded-md pr-2">
          <vue-office-docx 
            v-if="docxContent" 
            :src="docxContent"
            @rendered="handleDocxRendered"
            @error="handleDocxError"
            class="w-full h-full"
          />
          <div v-else class="flex-grow flex items-center justify-center text-gray-500">
            <p>请上传DOCX文件以预览</p>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import axios from 'axios'
import { VueOfficeDocx } from '@vue-office/docx'
import '@vue-office/docx/lib/index.css'
import ModelManager from './components/ModelManager.vue'
// 状态变量
const title = ref('文档格式分析系统')
const messages = ref([])
const userInput = ref('')
const docxFile = ref(null)
const docxContent = ref(null)
const docxUrl = ref(null)
const executionSteps = ref([])
const messagesContainer = ref(null)
const showProgress = ref(false)

// 计算属性
const totalSteps = computed(() => executionSteps.value.length)
const completedSteps = computed(() => {
  return executionSteps.value.filter(step => step.status === 'completed').length
})
const progressPercentage = computed(() => {
  return (completedSteps.value / totalSteps.value) * 100
})

// 轮询进度的定时器
let progressTimer = null

// 生命周期钩子
onMounted(async () => {
  try {
    // 获取页面标题
    const titleResponse = await axios.get('/api/get-title')
    title.value = titleResponse.data.title
    
    // 获取执行步骤
    const stepsResponse = await axios.get('/api/get-execution-steps')
    executionSteps.value = stepsResponse.data.steps
    
    // 获取历史消息
    const messagesResponse = await axios.get('/api/get-messages')
    messages.value = messagesResponse.data.messages
    
    // 滚动到最新消息
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('初始化数据失败:', error)
    addSystemMessage('系统初始化失败，请刷新页面重试。')
  }
})

// 开始轮询进度
function startPollingProgress(taskId) {
  if (progressTimer) clearInterval(progressTimer)
  
  progressTimer = setInterval(async () => {
    try {
      const response = await axios.get(`/api/task-progress/${taskId}`)
      const { steps, completed } = response.data
      
      // 更新步骤状态
      executionSteps.value = steps
      
      if (completed) {
        clearInterval(progressTimer)
        progressTimer = null
        showProgress.value = false
      }
    } catch (error) {
      console.error('获取进度失败:', error)
      clearInterval(progressTimer)
      progressTimer = null
    }
  }, 1000) // 每秒轮询一次
}

// 方法
function addUserMessage(content) {
  messages.value.push({
    sender: 'user',
    content,
    timestamp: new Date().toISOString()
  })
  nextTick(() => scrollToBottom())
}

function addSystemMessage(content) {
  messages.value.push({
    sender: 'system',
    content,
    timestamp: new Date().toISOString()
  })
  nextTick(() => scrollToBottom())
}

async function sendMessage() {
  if (!userInput.value.trim()) return
  
  const message = userInput.value
  addUserMessage(message)
  userInput.value = ''
  
  try {
    const response = await axios.post('/api/send-message', {
      message,
      timestamp: new Date().toISOString()
    })
    
    // 添加系统回复
    if (response.data.reply) {
      addSystemMessage(response.data.reply)
    }
    
    // 如果返回了任务ID，开始轮询进度
    if (response.data.taskId) {
      showProgress.value = true
      startPollingProgress(response.data.taskId)
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    addSystemMessage('消息发送失败，请重试。')
  }
}

async function handleFileUpload(event) {
  const file = event.target.files[0]
  if (!file) return
  
  docxFile.value = file
  addUserMessage(`我上传了文件: ${file.name}`)
  
  // 创建FormData对象
  const formData = new FormData()
  formData.append('docx_file', file)
  
  try {
    // 显示进度条
    showProgress.value = true
    
    // 读取文件内容用于预览
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        docxContent.value = e.target.result
        docxUrl.value = URL.createObjectURL(file)
      } catch (error) {
        console.error('文件读取失败:', error)
        addSystemMessage('文件读取失败，请重试')
      }
    }
    reader.onerror = (error) => {
      console.error('文件读取错误:', error)
      addSystemMessage('文件读取错误，请重试')
    }
    reader.readAsArrayBuffer(file)
    
    // 上传文件
    const uploadResponse = await axios.post('/api/upload-files', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    addSystemMessage('文件上传成功，正在分析文档格式...')
    
    // 开始文档分析
    const analyzeResponse = await axios.post('/api/analyze-document', {
      file_path: uploadResponse.data.file_path
    })
    
    addSystemMessage('文档分析完成！')
    
    if (analyzeResponse.data.errors && analyzeResponse.data.errors.length > 0) {
      addSystemMessage(`发现 ${analyzeResponse.data.errors.length} 个格式问题：`)
      analyzeResponse.data.errors.forEach(error => {
        addSystemMessage(`- ${error}`)
      })
    } else {
      addSystemMessage('文档格式符合要求！')
    }
  } catch (error) {
    console.error('文件处理失败:', error)
    addSystemMessage(`文件处理失败: ${error.response?.data?.detail || error.message}`)
  }
}

function downloadDocx() {
  if (docxFile.value) {
    const url = URL.createObjectURL(docxFile.value)
    const a = document.createElement('a')
    a.href = url
    a.download = docxFile.value.name
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }
}

function resetConversation() {
  // 清除轮询定时器
  if (progressTimer) {
    clearInterval(progressTimer)
    progressTimer = null
  }
  
  messages.value = []
  docxFile.value = null
  docxContent.value = null
  showProgress.value = false
  executionSteps.value.forEach(step => {
    step.status = 'pending'
  })
  addSystemMessage('对话已重置，您可以开始新的对话。')
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

function handleDocxRendered() {
  console.log('文档渲染成功')
}

function handleDocxError(error) {
  console.error('文档渲染失败:', error)
  addSystemMessage('文档预览加载失败，请检查文件格式。')
}
</script>

<style>
/* 自定义滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: #2d3748;
}

::-webkit-scrollbar-thumb {
  background-color: #4a5568;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background-color: #718096;
}
</style>