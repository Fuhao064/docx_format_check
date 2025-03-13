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
            <div class="max-w-3xl rounded-lg p-4" :class="message.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-zinc-800 text-zinc-100'">
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
              class="w-full bg-zinc-800 text-zinc-100 rounded-lg pl-4 pr-12 py-3 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
              rows="3"
            ></textarea>
            
            <div class="absolute right-3 bottom-3 flex space-x-2">
              <!-- 上传文件按钮 -->
              <button 
                @click="triggerFileUpload"
                class="p-2 rounded-full bg-zinc-700 hover:bg-zinc-600 text-zinc-300 transition-colors"
                title="上传文档"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="17 8 12 3 7 8"></polyline>
                  <line x1="12" y1="3" x2="12" y2="15"></line>
                </svg>
              </button>
              
              <!-- 发送按钮 -->
              <button 
                @click="sendMessage"
                class="p-2 rounded-full bg-indigo-600 hover:bg-indigo-700 text-white transition-colors"
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
import { ref, onMounted } from 'vue'
import { VueOfficeDocx } from '@vue-office/docx'
import axios from 'axios'

// 消息列表
const messages = ref([])
const userInput = ref('')

// 文件上传相关
const fileInput = ref(null)
const uploadedFile = ref(null)
const uploadedFileName = ref('')
const showDocPreview = ref(false)
const docxSrc = ref('')

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
    } else {
      alert('文件上传失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('上传文件时出错:', error)
    alert('上传文件时出错: ' + error.message)
  }
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
      messages.value.push({
        role: 'system',
        content: '正在分析文档格式...'
      })
      
      // 发送分析请求
      const response = await axios.post('/api/analyze-document', {
        doc_path: uploadedFile.value,
        message: userMessage
      })
      
      // 更新最后一条系统消息
      if (messages.value[messages.value.length - 1].role === 'system') {
        messages.value.pop()
      }
      
      // 添加分析结果
      messages.value.push({
        role: 'system',
        content: response.data.message || '文档分析完成'
      })
    } catch (error) {
      console.error('分析文档时出错:', error)
      
      // 更新最后一条系统消息
      if (messages.value[messages.value.length - 1].role === 'system') {
        messages.value.pop()
      }
      
      messages.value.push({
        role: 'system',
        content: '分析文档时出错: ' + error.message
      })
    }
  } else if (userMessage) {
    // 如果没有上传文件但有用户消息，发送普通消息
    try {
      const response = await axios.post('/api/send-message', {
        message: userMessage
      })
      
      messages.value.push({
        role: 'system',
        content: response.data.reply || '没有回复'
      })
    } catch (error) {
      console.error('发送消息时出错:', error)
      messages.value.push({
        role: 'system',
        content: '发送消息时出错: ' + error.message
      })
    }
  }
}
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
</style> 