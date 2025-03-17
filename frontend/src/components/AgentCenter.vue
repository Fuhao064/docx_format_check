<template>
  <div 
    class="fixed inset-y-0 right-0 w-80 transform transition-transform duration-300 z-20 flex flex-col"
    :class="[
      isOpen ? 'translate-x-0' : 'translate-x-full',
      isDarkMode ? 'bg-zinc-800 border-zinc-700' : 'bg-white border-gray-200',
      'border-l'
    ]"
  >
    <!-- 头部 -->
    <div class="p-4 flex items-center justify-between border-b" :class="isDarkMode ? 'border-zinc-700' : 'border-gray-200'">
      <h2 class="text-lg font-semibold" :class="isDarkMode ? 'text-zinc-100' : 'text-gray-900'">格式Agent中心</h2>
      <button 
        @click="close"
        class="p-1 rounded-md transition-colors"
        :class="isDarkMode ? 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-700' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>
    
    <!-- 内容区域 -->
    <div class="flex-1 overflow-y-auto p-4">
      <!-- 选择Agent模式 -->
      <div v-if="!selectedAgent" class="space-y-4">
        <p class="text-sm mb-4" :class="isDarkMode ? 'text-zinc-400' : 'text-gray-600'">
          选择一个Agent来帮助你解决文档格式问题
        </p>
        
        <!-- Agent卡片列表 -->
        <div 
          v-for="agent in agents" 
          :key="agent.id" 
          @click="selectAgent(agent)"
          class="p-4 rounded-lg cursor-pointer transition-colors border"
          :class="[
            isDarkMode ? 'bg-zinc-700 hover:bg-zinc-600 border-zinc-600' : 'bg-white hover:bg-gray-50 border-gray-200',
          ]"
        >
          <div class="flex items-center mb-2">
            <div class="w-8 h-8 rounded-full flex items-center justify-center mr-2"
              :class="agent.bgColor"
            >
              <component :is="agent.icon" class="w-5 h-5" :class="agent.iconColor" />
            </div>
            <h3 class="font-medium" :class="isDarkMode ? 'text-zinc-100' : 'text-gray-900'">{{ agent.name }}</h3>
          </div>
          <p class="text-sm" :class="isDarkMode ? 'text-zinc-400' : 'text-gray-600'">{{ agent.description }}</p>
        </div>
      </div>
      
      <!-- 聊天界面 -->
      <div v-else class="h-full flex flex-col">
        <div class="mb-4 flex items-center">
          <button 
            @click="backToAgentSelection"
            class="p-1 mr-2 rounded-md transition-colors"
            :class="isDarkMode ? 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-700' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m15 18-6-6 6-6"></path>
            </svg>
          </button>
          <div class="flex items-center">
            <div class="w-6 h-6 rounded-full flex items-center justify-center mr-2"
              :class="selectedAgent.bgColor"
            >
              <component :is="selectedAgent.icon" class="w-4 h-4" :class="selectedAgent.iconColor" />
            </div>
            <h3 class="font-medium" :class="isDarkMode ? 'text-zinc-100' : 'text-gray-900'">{{ selectedAgent.name }}</h3>
          </div>
        </div>
        
        <!-- 聊天消息区域 -->
        <div class="flex-1 overflow-y-auto mb-4 space-y-4">
          <div v-for="(message, index) in messages" :key="index" class="flex">
            <div v-if="message.sender === 'agent'" class="max-w-[85%] mr-auto">
              <div class="rounded-lg p-3 inline-block"
                :class="isDarkMode ? 'bg-zinc-700 text-zinc-100' : 'bg-gray-100 text-gray-900'"
              >
                {{ message.text }}
              </div>
            </div>
            <div v-else class="max-w-[85%] ml-auto">
              <div class="rounded-lg p-3 inline-block"
                :class="isDarkMode ? 'bg-blue-600 text-white' : 'bg-blue-500 text-white'"
              >
                {{ message.text }}
              </div>
            </div>
          </div>
        </div>
        
        <!-- 输入区域 -->
        <div class="mt-auto">
          <div class="flex items-center">
            <input 
              v-model="userInput"
              @keyup.enter="sendMessage"
              type="text"
              placeholder="输入你的问题..."
              class="flex-1 rounded-l-md py-2 px-3 focus:outline-none"
              :class="isDarkMode ? 'bg-zinc-700 text-zinc-100 placeholder-zinc-500' : 'bg-white text-gray-900 border border-gray-300 placeholder-gray-400'"
            />
            <button 
              @click="sendMessage"
              class="rounded-r-md py-2 px-4 transition-colors"
              :class="isDarkMode ? 'bg-blue-600 hover:bg-blue-700 text-white' : 'bg-blue-500 hover:bg-blue-600 text-white'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, h, inject, watch } from 'vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  formatErrors: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close'])

const isDarkMode = inject('isDarkMode', ref(true))

// Agent数据
const agents = [
  {
    id: 1,
    name: 'Agent 1：结构修复',
    description: '专注于修复文档结构问题，如标题层级、段落格式等',
    icon: h('svg', {
      xmlns: 'http://www.w3.org/2000/svg',
      viewBox: '0 0 24 24',
      fill: 'none',
      stroke: 'currentColor',
      'stroke-width': '2',
      'stroke-linecap': 'round',
      'stroke-linejoin': 'round'
    }, [
      h('path', { d: 'M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z' }),
      h('polyline', { points: '3.29 7 12 12 20.71 7' })
    ]),
    bgColor: isDarkMode.value ? 'bg-blue-900/50' : 'bg-blue-100',
    iconColor: isDarkMode.value ? 'text-blue-300' : 'text-blue-700'
  },
  {
    id: 2,
    name: 'Agent 2：样式建议',
    description: '提供字体、颜色、间距等样式优化建议，提升文档美观度',
    icon: h('svg', {
      xmlns: 'http://www.w3.org/2000/svg',
      viewBox: '0 0 24 24',
      fill: 'none',
      stroke: 'currentColor',
      'stroke-width': '2',
      'stroke-linecap': 'round',
      'stroke-linejoin': 'round'
    }, [
      h('path', { d: 'M12 20h9' }),
      h('path', { d: 'M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z' })
    ]),
    bgColor: isDarkMode.value ? 'bg-purple-900/50' : 'bg-purple-100',
    iconColor: isDarkMode.value ? 'text-purple-300' : 'text-purple-700'
  },
  {
    id: 3,
    name: 'Agent 3：合规检查',
    description: '检查文档是否符合特定标准或规范，提供合规性建议',
    icon: h('svg', {
      xmlns: 'http://www.w3.org/2000/svg',
      viewBox: '0 0 24 24',
      fill: 'none',
      stroke: 'currentColor',
      'stroke-width': '2',
      'stroke-linecap': 'round',
      'stroke-linejoin': 'round'
    }, [
      h('path', { d: 'M22 11.08V12a10 10 0 1 1-5.93-9.14' }),
      h('polyline', { points: '22 4 12 14.01 9 11.01' })
    ]),
    bgColor: isDarkMode.value ? 'bg-green-900/50' : 'bg-green-100',
    iconColor: isDarkMode.value ? 'text-green-300' : 'text-green-700'
  }
]

// 选中的Agent
const selectedAgent = ref(null)

// 聊天消息
const messages = ref([])

// 用户输入
const userInput = ref('')

// 选择Agent
function selectAgent(agent) {
  selectedAgent.value = agent
  
  // 根据选中的Agent和格式错误生成初始消息
  let initialMessage = '你好！我是' + agent.name.split('：')[1] + '。'
  
  if (props.formatErrors && props.formatErrors.length > 0) {
    if (agent.id === 1) {
      initialMessage += '我注意到你的文档有一些结构问题需要修复。需要我帮你解决哪些问题？'
    } else if (agent.id === 2) {
      initialMessage += '我可以帮你优化文档样式，使其更加美观。你想从哪方面开始改进？'
    } else if (agent.id === 3) {
      initialMessage += '我可以帮你检查文档是否符合特定标准。你有什么具体的合规要求吗？'
    }
  } else {
    initialMessage += '我可以帮助你解决文档格式问题。请告诉我你需要什么帮助？'
  }
  
  messages.value = [
    { sender: 'agent', text: initialMessage }
  ]
}

// 返回Agent选择
function backToAgentSelection() {
  selectedAgent.value = null
  messages.value = []
  userInput.value = ''
}

// 发送消息
function sendMessage() {
  if (!userInput.value.trim()) return
  
  // 添加用户消息
  messages.value.push({ sender: 'user', text: userInput.value })
  
  // 模拟Agent回复
  setTimeout(() => {
    let response = ''
    
    if (selectedAgent.value.id === 1) {
      response = '我理解你的结构问题。根据我的分析，你可以尝试调整标题层级，确保正确使用标题1到标题6，并保持层级关系。你还需要其他结构方面的建议吗？'
    } else if (selectedAgent.value.id === 2) {
      response = '关于样式优化，我建议你统一字体类型，正文使用无衬线字体如Arial或Calibri，标题可以使用稍微不同的字体增加对比。你还可以调整行间距为1.15-1.5倍，提高可读性。'
    } else if (selectedAgent.value.id === 3) {
      response = '从合规角度看，请确保你的文档包含必要的版权声明和引用格式。如果是学术论文，请检查是否符合APA或MLA等引用规范。你需要我详细解释某个具体标准吗？'
    }
    
    messages.value.push({ sender: 'agent', text: response })
  }, 1000)
  
  // 清空输入
  userInput.value = ''
}

// 关闭面板
function close() {
  emit('close')
}
</script>

<style scoped>
/* 自定义滚动条样式 */
.overflow-y-auto::-webkit-scrollbar {
  width: 4px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: transparent;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background-color: v-bind('isDarkMode ? "#3f3f46" : "#d1d5db"');
  border-radius: 2px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background-color: v-bind('isDarkMode ? "#52525b" : "#9ca3af"');
}
</style> 