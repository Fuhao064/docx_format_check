<template>
  <div class="flex flex-col h-full">
    <!-- 对话区域 -->
    <div class="flex-1 flex overflow-hidden">
      <!-- 对话内容区域 -->
      <div class="flex-1 flex flex-col overflow-hidden p-4">
        <div class="flex-1 overflow-y-auto scrollbar-thin mb-4 space-y-6">
          <div v-if="messages.length === 0" class="h-full flex flex-col items-center justify-center text-zinc-500">
            <div class="w-16 h-16 mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              </svg>
            </div>
            <p class="text-lg">开始一个新的对话</p>
            <p class="text-sm mt-2">上传文档或直接输入问题</p>
          </div>
          
          <div v-for="(message, index) in messages" :key="index" class="flex" :class="message.role === 'user' ? 'justify-end' : 'justify-start'">
            <div class="max-w-3xl rounded-md p-4" :class="[
              message.role === 'user' 
                ? isDarkMode ? 'bg-zinc-800 text-white' : 'bg-gray-200 text-black' 
                : isDarkMode ? 'bg-zinc-800/50 text-zinc-100' : 'bg-gray-100 text-black'
            ]">
              {{ message.content }}
            </div>
          </div>
        </div>
        
        <!-- 输入区域 -->
        <div class="border-t border-zinc-800 pt-4">
          <div class="relative">
            <textarea 
              v-model="userInput" 
              @keydown.enter.prevent="sendMessage"
              placeholder="开始摧毁格式..." 
              class="w-full rounded-md pl-12 pr-12 py-3 resize-none focus:outline-none focus:ring-1"
              :class="isDarkMode ? 'bg-zinc-800 text-zinc-100 focus:ring-zinc-700' : 'bg-gray-100 text-black focus:ring-gray-300'"
              rows="3"
            ></textarea>
            
            <div class="absolute left-3 bottom-3">
              <!-- 上传文件按钮 -->
              <button 
                @click="triggerFileUpload"
                class="p-2 rounded-md bg-zinc-700 hover:bg-zinc-600 text-zinc-300 transition-colors"
                title="上传文档"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="17 8 12 3 7 8"></polyline>
                  <line x1="12" y1="3" x2="12" y2="15"></line>
                </svg>
              </button>
            </div>
            
            <div class="absolute right-3 bottom-3">
              <!-- 发送按钮 -->
              <button 
                @click="sendMessage"
                class="p-2 rounded-md bg-zinc-700 hover:bg-zinc-600 text-zinc-300 transition-colors"
                title="发送消息"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13"></line>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
              </button>
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
        </div>
      </div>
      
      <!-- 文档预览区域 -->
      <div 
        v-if="showDocPreview" 
        class="w-1/2 border-l border-zinc-800 flex flex-col overflow-hidden"
      >
        <div class="flex items-center justify-between p-3 border-b border-zinc-800">
          <h3 class="font-medium">{{ uploadedFileName || '文档预览' }}</h3>
          <button 
            @click="showDocPreview = false"
            class="p-1 rounded-md hover:bg-zinc-800 text-zinc-400 hover:text-zinc-100 transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        
        <div class="flex-1 overflow-hidden bg-white">
          <vue-office-docx
            v-if="docxSrc"
            :src="docxSrc"
            class="h-full"
          />
          <div v-else class="h-full flex items-center justify-center text-zinc-500">
            加载文档中...
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import { VueOfficeDocx } from '@vue-office/docx'
import axios from 'axios'

// 获取主题模式
const isDarkMode = inject('isDarkMode')

// 消息列表
const messages = ref([])
const userInput = ref('')

// 文件上传相关
const fileInput = ref(null)
const uploadedFile = ref(null)
const uploadedFileName = ref('')
const showDocPreview = ref(false)
const docxSrc = ref('')

// 获取通知函数
const showNotification = inject('showNotification', null)

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
      docxSrc.value = `/uploads/${file.name}` // 假设服务器将文件保存在uploads目录
      showDocPreview.value = true
      
      // 添加系统消息
      messages.value.push({
        role: 'system',
        content: `文件 "${file.name}" 已上传成功。您可以开始分析文档格式。`
      })
      
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

// 发送消息
async function sendMessage() {
  if (!userInput.value.trim() && !uploadedFile.value) return
  
  // 添加用户消息
  const userMessage = userInput.value.trim()
  if (userMessage) {
    messages.value.push({
      role: 'user',
      content: userMessage
    })
  }
  
  // 清空输入
  userInput.value = ''
  
  // 如果有上传的文件，发送分析请求
  if (uploadedFile.value) {
    try {
      // 添加加载消息
      const loadingMessageIndex = messages.value.length
      messages.value.push({
        role: 'system',
        content: '正在分析文档格式...'
      })
      
      // 显示加载通知
      if (showNotification) {
        showNotification('info', '分析中', '正在分析文档格式，这可能需要一些时间...', 0)
      }
      
      // 发送分析请求
      const response = await axios.post('/api/analyze-document', {
        doc_path: uploadedFile.value,
        message: userMessage
      })
      
      // 更新最后一条系统消息
      if (messages.value[loadingMessageIndex].role === 'system') {
        messages.value[loadingMessageIndex].content = response.data.message || '文档分析完成'
      }
      
      // 显示成功通知
      if (showNotification) {
        showNotification('success', '分析完成', '文档格式分析已完成', 3000)
      }
    } catch (error) {
      console.error('分析文档时出错:', error)
      
      // 更新最后一条系统消息
      const lastMessage = messages.value[messages.value.length - 1]
      if (lastMessage && lastMessage.role === 'system') {
        lastMessage.content = '分析文档时出错: ' + error.message
      } else {
        messages.value.push({
          role: 'system',
          content: '分析文档时出错: ' + error.message
        })
      }
      
      // 显示错误通知
      if (showNotification) {
        showNotification('error', '分析失败', `分析文档时出错: ${error.message}`, 5000)
      }
    }
  } else if (userMessage) {
    // 如果没有上传文件但有用户消息，发送普通消息
    try {
      // 添加加载消息
      const loadingMessageIndex = messages.value.length
      messages.value.push({
        role: 'system',
        content: '正在思考...'
      })
      
      const response = await axios.post('/api/send-message', {
        message: userMessage
      })
      
      // 更新最后一条系统消息
      if (messages.value[loadingMessageIndex].role === 'system') {
        messages.value[loadingMessageIndex].content = response.data.reply || '没有回复'
      }
    } catch (error) {
      console.error('发送消息时出错:', error)
      
      // 更新最后一条系统消息
      const lastMessage = messages.value[messages.value.length - 1]
      if (lastMessage && lastMessage.role === 'system') {
        lastMessage.content = '发送消息时出错: ' + error.message
      } else {
        messages.value.push({
          role: 'system',
          content: '发送消息时出错: ' + error.message
        })
      }
      
      // 显示错误通知
      if (showNotification) {
        showNotification('error', '发送失败', `发送消息时出错: ${error.message}`, 5000)
      }
    }
  }
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
  background: #18181b;
}

.scrollbar-thin::-webkit-scrollbar-thumb {
  background-color: #3f3f46;
  border-radius: 2px;
}

.scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background-color: #52525b;
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