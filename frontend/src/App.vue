<template>
  <div class="min-h-screen bg-[#1A1B1E] text-white flex">
    <!-- 左侧导航栏 -->
    <Sheet class="fixed left-0 top-0 h-screen w-64 bg-gray-800 p-4 border-r border-gray-700">
      <div class="flex items-center mb-8">
        <h1 class="text-xl font-bold text-white">{{ title }}</h1>
      </div>
      <div class="space-y-2">
        <template v-for="item in menuItems" :key="item.id">
          <NavigationMenuItem as-child>
          <a :href="item.href" class="block px-4 py-2 text-white hover:bg-gray-700 rounded-md transition-colors">
            <component :is="item.icon" class="h-5 w-5 inline-block mr-2" />
            <span>{{ item.name[currentLanguage] }}</span>
          </a>
        </NavigationMenuItem>
        </template>
      </div>
    </Sheet>

    <!-- 主内容区 -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- 顶部标题栏 -->
      <header class="bg-[#25262B] p-4 shadow-lg border-b border-gray-700 flex justify-between items-center">
        <div class="flex items-center space-x-4">
          <Menu v-if="docxUrl" as="div" class="relative inline-block text-left">
            <MenuButton class="inline-flex justify-center items-center px-4 py-2 bg-[#3B82F6] hover:bg-blue-700 text-white rounded-md transition-colors">
              {{ translations.documentOperations[currentLanguage] }}
              <ChevronDownIcon class="ml-2 -mr-1 h-5 w-5" aria-hidden="true" />
            </MenuButton>
            <transition
              enter-active-class="transition duration-100 ease-out"
              enter-from-class="transform scale-95 opacity-0"
              enter-to-class="transform scale-100 opacity-100"
              leave-active-class="transition duration-75 ease-in"
              leave-from-class="transform scale-100 opacity-100"
              leave-to-class="transform scale-95 opacity-0"
            >
              <MenuItems class="absolute left-0 mt-2 w-56 origin-top-right bg-[#25262B] rounded-md shadow-lg ring-1 ring-blue-500 ring-opacity-50 focus:outline-none">
                <div class="py-1">
                  <MenuItem v-slot="{ active }">
                    <button
                      @click="downloadDocx"
                      :class="[active ? 'bg-[#3B82F6]' : '', 'block w-full text-left px-4 py-2 text-sm text-white']"
                    >
                      {{ translations.downloadDocument[currentLanguage] }}
                    </Button>
                  </MenuItem>
                </div>
              </MenuItems>
            </transition>
          </Menu>
        </div>
        <!-- 语言切换 -->
        <div class="flex items-center space-x-2">
          <button
            v-for="lang in languages"
            :key="lang.code"
            @click="changeLanguage(lang.code)"
            :class="[
              'px-3 py-1 rounded-md text-sm transition-colors',
              currentLanguage === lang.code ? 'bg-[#3B82F6] text-white' : 'bg-[#2C2D31] text-gray-300 hover:bg-[#3B82F6]/50'
            ]"
          >
            {{ lang.name }}
          </Button>
        </div>
      </header>

      <!-- 主要内容区域 -->
      <main class="flex-1 flex overflow-hidden p-4">
        <!-- 左侧对话区域 -->
        <div class="w-2/3 flex flex-col overflow-hidden">
          <!-- 模型选择组件 -->
          <ModelManager class="mb-4" />
          <!-- 消息列表 -->
          <div class="flex-grow overflow-y-auto mb-4 space-y-4 pr-2 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-[#25262B]" ref="messagesContainer">
            <div v-for="(message, index) in messages" :key="index" 
                 class="flex" :class="{'justify-end': message.sender === 'user', 'justify-start': message.sender === 'system'}">
              <div :class="{
                'bg-[#3B82F6] text-white rounded-lg p-3 max-w-3/4 shadow-md': message.sender === 'user',
                'bg-[#25262B] text-white rounded-lg p-3 max-w-3/4 shadow-md': message.sender === 'system'
              }">
                {{ message.content }}
              </div>
            </div>
          </div>

          <!-- 进度条 -->
          <div v-if="showProgress" class="mb-4">
            <div class="flex justify-between text-sm text-gray-400 mb-1">
              <span>{{ translations.progress[currentLanguage] }}</span>
              <span>{{ completedSteps }}/{{ totalSteps }}</span>
            </div>
            <div class="w-full bg-[#25262B] rounded-full h-2.5">
              <div class="bg-[#3B82F6] h-2.5 rounded-full transition-all duration-300 ease-out" :style="{ width: `${progressPercentage}%` }"></div>
            </div>
          </div>

          <!-- 输入区域 -->
          <div class="flex space-x-2">
            <div class="flex-grow relative">
              <input 
                v-model="userInput" 
                @keyup.enter="sendMessage"
                :placeholder="translations.inputPlaceholder[currentLanguage]"
                class="w-full bg-[#25262B] text-white px-4 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-[#3B82F6]"
              />
            </div>
            
            <Button 
              v-if="!docxFile"
              variant="ghost"
              class="hover:bg-[#3B82F6] text-white px-4 py-2 rounded-md inline-flex items-center"
              @click="$refs.fileInput.click()"
            >
              {{ translations.uploadFile[currentLanguage] }}
              <input 
                ref="fileInput"
                type="file" 
                accept=".docx" 
                class="hidden" 
                @change="handleFileUpload"
              />
            </Button>
            <Button
              @click="sendMessage"
              class="hover:bg-blue-700 text-white px-4 py-2 rounded-md inline-flex items-center"
            >
              {{ translations.send[currentLanguage] }}
              <ChevronRightIcon class="ml-2 -mr-1 h-5 w-5" aria-hidden="true" />
            </Button>

            <Button 
              variant="outline"
              @click="resetConversation" 
              class="hover:bg-[#3B82F6] text-white px-4 py-2 rounded-md inline-flex items-center"
            >
              {{ translations.reset[currentLanguage] }}
              <ArrowPathIcon class="ml-2 -mr-1 h-5 w-5" aria-hidden="true" />
            </Button>
          </div>
        </div>

        <!-- 右侧文档预览区域 -->
        <div class="w-1/3 bg-[#1A1B1E] p-4 overflow-hidden flex flex-col border-l border-gray-800 ml-4">
          <h2 class="text-lg font-semibold mb-4 text-white">{{ translations.documentPreview[currentLanguage] }}</h2>
          <div class="flex-grow overflow-y-auto bg-[#25262B] rounded-md pr-2 border border-gray-800 hover:border-[#3B82F6]/50 transition-all duration-300">
            <vue-office-docx 
              v-if="docxContent" 
              :src="docxContent"
              @rendered="handleDocxRendered"
              @error="handleDocxError"
              class="w-full h-full"
            />
            <div v-else class="flex-grow flex items-center justify-center text-gray-400">
              <p>{{ translations.uploadPrompt[currentLanguage] }}</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
  <SidebarProvider>
    <AppSidebar />
    <SidebarInset>
      <header class="flex h-14 shrink-0 items-center gap-2">
        <div class="flex flex-1 items-center gap-2 px-3">
          <SidebarTrigger />
          <Separator orientation="vertical" class="mr-2 h-4" />
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbPage class="line-clamp-1">
                  Project Management & Task Tracking
                </BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
        </div>
        <div class="ml-auto px-3">
          <NavActions />
        </div>
      </header>
      <div class="flex flex-1 flex-col gap-4 px-4 py-10">
        <div class="mx-auto h-24 w-full max-w-3xl rounded-xl bg-muted/50" />
        <div class="mx-auto h-full w-full max-w-3xl rounded-xl bg-muted/50" />
      </div>
    </SidebarInset>
  </SidebarProvider>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import axios from 'axios'
import { VueOfficeDocx } from '@vue-office/docx'
import '@vue-office/docx/lib/index.css'
import ModelManager from './components/ModelManager.vue'
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/vue'
import { ChevronDownIcon, ChevronRightIcon, ArrowPathIcon } from '@heroicons/vue/20/solid'
import AppSidebar from './components/AppSidebar.vue'
import NavActions from './components/sidebar/NavActions.vue'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
} from './components/ui/breadcrumb'
import { Separator } from './components/ui/separator'
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from './components/ui/sidebar'
const description = 'A sidebar in a popover.'
const iframeHeight = '800px'

defineExpose({
  description,
  iframeHeight
})
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

// 语言配置
const languages = [
  { code: 'zh', name: '中文' },
  { code: 'en', name: 'English' }
]

const currentLanguage = ref('zh')

const translations = {
  documentOperations: {
    zh: '文档操作',
    en: 'Document Operations'
  },
  downloadDocument: {
    zh: '下载文档',
    en: 'Download Document'
  },
  progress: {
    zh: '处理进度',
    en: 'Progress'
  },
  inputPlaceholder: {
    zh: '请输入消息...',
    en: 'Enter your message...'
  },
  uploadFile: {
    zh: '上传文件',
    en: 'Upload File'
  },
  send: {
    zh: '发送',
    en: 'Send'
  },
  reset: {
    zh: '重置',
    en: 'Reset'
  },
  documentPreview: {
    zh: '文档预览',
    en: 'Document Preview'
  },
  uploadPrompt: {
    zh: '请上传DOCX文件以预览',
    en: 'Please upload a DOCX file to preview'
  }
}

const menuItems = [
  { 
    id: 'home',
    name: { zh: '首页', en: 'Home' },
    icon: 'HomeIcon'
  },
  {
    id: 'settings',
    name: { zh: '设置', en: 'Settings' },
    icon: 'CogIcon'
  }
]

function changeLanguage(lang) {
  currentLanguage.value = lang
}
</script>

<style>
@layer component {
  /* 自定义滚动条样式 */
  .scrollbar-thin::-webkit-scrollbar {
    width: 6px;
  }

  .scrollbar-thin::-webkit-scrollbar-track {
    background: #1f2937;
  }

  .scrollbar-thin::-webkit-scrollbar-thumb {
    background-color: #4b5563;
    border-radius: 3px;
  }

  .scrollbar-thin::-webkit-scrollbar-thumb:hover {
    background-color: #6b7280;
  }
}

/* 输入框和按钮统一样式 */
input:focus, button:focus {
  outline: none;
  @apply ring-2 ring-blue-600;
}

button {
  transition: all 0.3s ease-in-out;
}

button:hover {
  transform: scale(1.02);
  box-shadow: 0 0 15px rgba(59, 130, 246, 0.5);
}
</style>
