<template>
  <div class="flex flex-col h-screen overflow-hidden" :class="isDarkMode ? 'bg-zinc-900 text-zinc-100' : 'bg-white text-gray-900'">
    <!-- 顶部标题栏 -->
    <div class="flex items-center justify-between p-4 border-b" :class="isDarkMode ? 'border-zinc-800' : 'border-gray-200'">
      <h1 class="text-xl font-semibold">多Agent文档处理系统</h1>
      <div class="flex items-center space-x-2">
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
    
    <!-- 主内容区域 - 使用ResizablePanel组件 -->
    <div class="flex-1 overflow-hidden">
      <ResizablePanel :initial-left-width="60" @resize="handleResize" @maximize="handleMaximize">
        <!-- 左侧面板 - 聊天界面 -->
        <template #left>
          <div class="h-full flex flex-col overflow-hidden">
            <!-- Agent标签页 -->
            <AgentTabs 
              :agents="agents" 
              :initial-agent-id="activeAgentId"
              @agent-change="handleAgentChange"
              @collaboration-start="startCollaboration"
            >
              <!-- 结构Agent -->
              <template #structure>
                <ChatInterface />
              </template>
              
              <!-- 格式Agent -->
              <template #format>
                <ChatInterface />
              </template>
              
              <!-- 合规Agent -->
              <template #compliance>
                <ChatInterface />
              </template>
              
              <!-- 协作模式 -->
              <template #collaboration>
                <ChatInterface />
              </template>
            </AgentTabs>
          </div>
        </template>
        
        <!-- 右侧面板 - 文档预览 -->
        <template #right-title>
          {{ uploadedFileName || '文档预览' }}
        </template>
        
        <template #right>
          <div class="h-full overflow-hidden">
            <DocxPreview v-if="uploadedFile" :file-path="uploadedFile" />
            <div v-else class="h-full flex items-center justify-center" :class="isDarkMode ? 'text-zinc-500' : 'text-gray-400'">
              <p>请先上传文档</p>
            </div>
          </div>
        </template>
      </ResizablePanel>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, provide } from 'vue'
import ChatInterface from '../components/ChatInterface.vue'
import DocxPreview from '../components/DocxPreview.vue'
import ResizablePanel from '../components/ResizablePanel.vue'
import AgentTabs from '../components/AgentTabs.vue'

// 获取主题模式
const isDarkMode = inject('isDarkMode', ref(true))

// 提供给子组件
provide('isDarkMode', isDarkMode)

// 文档预览状态
const uploadedFile = ref(null)
const uploadedFileName = ref('')

// Agent相关
const activeAgentId = ref('structure')
const agents = [
  {
    id: 'structure',
    name: '结构Agent',
    bgColor: 'bg-green-500'
  },
  {
    id: 'format',
    name: '格式Agent',
    bgColor: 'bg-blue-500'
  },
  {
    id: 'compliance',
    name: '合规Agent',
    bgColor: 'bg-orange-500'
  }
]

// 处理面板调整
function handleResize(newLeftWidth) {
  console.log('面板宽度调整为:', newLeftWidth)
}

// 处理最大化
function handleMaximize(isMaximized) {
  console.log('面板最大化状态:', isMaximized)
}

// 处理Agent切换
function handleAgentChange(agentId) {
  activeAgentId.value = agentId
  console.log('切换到Agent:', agentId)
}

// 启动协作模式
function startCollaboration() {
  console.log('启动协作模式')
}

// 切换暗黑模式
function toggleDarkMode() {
  isDarkMode.value = !isDarkMode.value
}

// 监听文件上传事件
provide('onFileUploaded', (filePath, fileName, colorClass) => {
  uploadedFile.value = filePath
  uploadedFileName.value = fileName
  
  // 更新App.vue中的聊天历史
  const updateChatHistory = inject('updateChatHistory', null)
  if (updateChatHistory) {
    updateChatHistory(fileName, colorClass)
  }
})
</script>