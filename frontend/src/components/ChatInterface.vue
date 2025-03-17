<template>
  <div class="flex flex-col h-full" :class="isDarkMode ? 'bg-zinc-900 text-zinc-100' : 'bg-white text-gray-900'">
    <!-- 文件上传区域 -->
    <div v-if="!hasUploadedFile" class="flex-1 flex flex-col items-center justify-center p-6">
      <div class="w-16 h-16 mb-4" :class="isDarkMode ? 'text-blue-400' : 'text-blue-700'">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
          <line x1="16" y1="13" x2="8" y2="13"></line>
          <line x1="16" y1="17" x2="8" y2="17"></line>
          <polyline points="10 9 9 9 8 9"></polyline>
        </svg>
      </div>
      <p class="text-lg font-medium">开始文档处理</p>
      <p class="text-sm mt-2 mb-6" :class="isDarkMode ? 'text-zinc-400' : 'text-gray-700'">请上传文档开始与Agent交互</p>
      
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
    
    <!-- 聊天界面 -->
    <div v-else class="flex-1 flex flex-col overflow-hidden">
      <!-- 消息区域 -->
      <div class="flex-1 overflow-y-auto p-4 space-y-4" ref="messagesContainer">
        <!-- 欢迎消息 -->
        <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full">
          <div class="text-center p-6 rounded-lg" :class="isDarkMode ? 'bg-zinc-800' : 'bg-gray-100'">
            <h3 class="text-lg font-medium mb-2">文档已上传成功</h3>
            <p class="mb-4" :class="isDarkMode ? 'text-zinc-400' : 'text-gray-600'">您可以开始与文档处理Agent交流，提出您的需求</p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
              <div 
                v-for="(suggestion, index) in suggestions" 
                :key="index"
                @click="sendMessage(suggestion)"
                class="p-2 rounded cursor-pointer text-left transition-colors"
                :class="isDarkMode ? 'bg-zinc-700 hover:bg-zinc-600' : 'bg-white hover:bg-gray-200 border border-gray-200'"
              >
                {{ suggestion }}
              </div>
            </div>
          </div>
        </div>
        
        <!-- 消息列表 -->
        <div 
          v-for="(message, index) in messages" 
          :key="index"
          :class="[
            'flex',
            message.sender === 'user' ? 'justify-end' : 'justify-start'
          ]"
        >
          <div 
            :class="[
              'max-w-3/4 rounded-lg p-3',
              message.sender === 'user' 
                ? isDarkMode ? 'bg-blue-600 text-white' : 'bg-blue-500 text-white' 
                : isDarkMode ? 'bg-zinc-800' : 'bg-gray-100'
            ]"
          >
            <div class="whitespace-pre-wrap" v-html="formatMessage(message.content)"></div>
          </div>
        </div>
        
        <!-- 加载指示器 -->
        <div v-if="isLoading" class="flex justify-start">
          <div class="flex items-center space-x-2 p-3 rounded-lg" :class="isDarkMode ? 'bg-zinc-800' : 'bg-gray-100'">
            <div class="flex space-x-1">
              <div class="w-2 h-2 rounded-full animate-bounce" :class="isDarkMode ? 'bg-zinc-400' : 'bg-gray-500'" style="animation-delay: 0s"></div>
              <div class="w-2 h-2 rounded-full animate-bounce" :class="isDarkMode ? 'bg-zinc-400' : 'bg-gray-500'" style="animation-delay: 0.2s"></div>
              <div class="w-2 h-2 rounded-full animate-bounce" :class="isDarkMode ? 'bg-zinc-400' : 'bg-gray-500'" style="animation-delay: 0.4s"></div>
            </div>
            <span class="text-sm" :class="isDarkMode ? 'text-zinc-400' : 'text-gray-500'">Agent正在思考...</span>
          </div>
        </div>
      </div>
      
      <!-- 输入区域 -->
      <div class="border-t p-4" :class="isDarkMode ? 'border-zinc-800' : 'border-gray-200'">
        <div class="flex space-x-2">
          <textarea 
            v-model="userInput" 
            @keydown.enter.prevent="handleEnterKey"
            placeholder="输入您的问题或需求..."
            class="flex-1 resize-none rounded-lg p-3 focus:outline-none focus:ring-1"
            :class="isDarkMode ? 'bg-zinc-800 text-zinc-100 focus:ring-zinc-700' : 'bg-gray-100 text-gray-900 focus:ring-blue-500'"
            rows="2"
          ></textarea>
          <button 
            @click="sendMessage()"
            :disabled="isLoading || !userInput.trim()"
            class="self-end p-3 rounded-lg transition-colors flex items-center justify-center"
            :class="[
              isDarkMode 
                ? isLoading || !userInput.trim() ? 'bg-zinc-800 text-zinc-600' : 'bg-blue-600 hover:bg-blue-700 text-white'
                : isLoading || !userInput.trim() ? 'bg-gray-200 text-gray-400' : 'bg-blue-500 hover:bg-blue-600 text-white'
            ]"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject, watch, nextTick } from 'vue'
import axios from 'axios'
import { io } from 'socket.io-client'

// 获取主题模式
const isDarkMode = inject('isDarkMode')

// 获取通知函数
const showNotification = inject('showNotification', null)

// 文件上传相关
const fileInput = ref(null)
const hasUploadedFile = ref(false)
const uploadedFile = ref(null)
const uploadedFileName = ref('')

// 检查是否有已上传的文件（从localStorage恢复状态）
onMounted(() => {
  // 初始化时确保hasUploadedFile为false，除非有明确的上传文件记录
  console.log('ChatInterface mounted, checking uploaded file status');
  if (uploadedFile.value) {
    hasUploadedFile.value = true;
  } else {
    hasUploadedFile.value = false;
  }
})
// 聊天相关
const userInput = ref('')
const messages = ref([])
const isLoading = ref(false)
const messagesContainer = ref(null)

// 建议问题
const suggestions = [
  "请检查我的文档格式是否符合要求",
  "这篇文档有哪些格式问题？",
  "帮我修改文档中的格式错误",
  "分析一下文档的内容并提供修改建议"
]

// 触发文件上传
function triggerFileUpload() {
  fileInput.value.click()
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
      hasUploadedFile.value = true
      console.log('文件上传成功，hasUploadedFile:', hasUploadedFile.value);
      
      // 显示成功通知
      if (showNotification) {
        showNotification('success', '上传成功', `文件 "${file.name}" 已成功上传`, 3000)
      }
      
      // 通知父组件文件已上传
      const onFileUploaded = inject('onFileUploaded', null)
      if (onFileUploaded) {
        onFileUploaded(response.data.file_path, file.name)
      }
      
      // 添加系统欢迎消息
      messages.value.push({
        sender: 'system',
        content: `您好，我是文档处理助手。我已成功接收到您上传的文档 "${file.name}"。我可以帮您检查文档格式、提供内容修改建议，以及应用这些修改。请告诉我您需要什么帮助？`,
        timestamp: new Date().toISOString()
      })
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
}

// 发送消息
async function sendMessage(suggestionText) {
  const messageText = suggestionText || userInput.value.trim()
  if (!messageText || isLoading.value) return
  
  // 添加用户消息到列表
  messages.value.push({
    sender: 'user',
    content: messageText,
    timestamp: new Date().toISOString()
  })
  
  // 清空输入框
  userInput.value = ''
  
  // 滚动到底部
  await nextTick()
  scrollToBottom()
  
  // 设置加载状态
  isLoading.value = true
  
  try {
    // 发送消息到服务器
    const response = await axios.post('/api/send-message', {
      message: messageText,
      file_path: uploadedFile.value,
      timestamp: new Date().toISOString()
    })
    
    // 添加系统回复到列表
    messages.value.push({
      sender: 'system',
      content: response.data.reply,
      timestamp: response.data.timestamp
    })
    
    // 滚动到底部
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('发送消息时出错:', error)
    
    // 显示错误通知
    if (showNotification) {
      showNotification('error', '发送失败', `发送消息时出错: ${error.message}`, 5000)
    }
    
    // 添加错误消息
    messages.value.push({
      sender: 'system',
      content: '抱歉，发送消息时出现错误，请稍后再试。',
      timestamp: new Date().toISOString()
    })
  } finally {
    // 取消加载状态
    isLoading.value = false
    
    // 滚动到底部
    await nextTick()
    scrollToBottom()
  }
}

// 处理回车键
function handleEnterKey(event) {
  // 如果按下Shift+Enter，则插入换行
  if (event.shiftKey) {
    return
  }
  
  // 否则发送消息
  sendMessage()
}

// 格式化消息内容（支持简单的Markdown语法）
function formatMessage(content) {
  if (!content) return ''
  
  // 替换链接
  content = content.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" class="text-blue-400 hover:underline">$1</a>')
  
  // 替换粗体
  content = content.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  
  // 替换斜体
  content = content.replace(/\*([^*]+)\*/g, '<em>$1</em>')
  
  // 替换代码
  content = content.replace(/`([^`]+)`/g, '<code class="px-1 py-0.5 rounded bg-opacity-20 ' + (isDarkMode.value ? 'bg-zinc-700' : 'bg-gray-200') + '">$1</code>')
  
  // 替换换行符
  content = content.replace(/\n/g, '<br>')
  
  return content
}

// 滚动到底部
function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 监听消息变化，自动滚动到底部
watch(
  () => messages.value.length,
  () => nextTick(scrollToBottom)
)

// 组件挂载后初始化
onMounted(() => {
  // 初始化WebSocket连接
  const socket = io()
  console.log('WebSocket 连接状态:', socket.connected);
  
  // 监听消息事件
  socket.on('message', (message) => {
    console.log('接收到消息:', message);
    // 如果收到系统消息且不是当前用户发送的，则添加到消息列表
    if (message.sender === 'system') {
      messages.value.push(message)
      nextTick(scrollToBottom)
    }
  })
})
</script>