<template>
  <div class="min-h-screen bg-zinc-950 text-zinc-100 flex">
    <!-- 侧边栏 -->
    <aside 
      class="h-screen flex flex-col bg-zinc-900 border-r border-zinc-800 transition-all duration-300 overflow-hidden fixed z-10"
      :class="sidebarCollapsed ? 'w-12' : 'w-64'"
    >
      <!-- 顶部Logo和标题 -->
      <div class="p-4 flex items-center border-b border-zinc-800">
        <div v-if="!sidebarCollapsed" class="w-8 h-8 bg-zinc-800 rounded-md flex items-center justify-center mr-3">
          <!-- 占位Logo -->
          <div class="w-5 h-5 text-zinc-300">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
              <path d="M2 17l10 5 10-5"></path>
              <path d="M2 12l10 5 10-5"></path>
            </svg>
          </div>
        </div>
        <h1 class="text-lg font-semibold truncate" v-show="!sidebarCollapsed">Putain le format</h1>
        
        <!-- 折叠按钮 -->
        <button 
          @click="toggleSidebar" 
          class="ml-auto text-zinc-400 hover:text-zinc-100 transition-colors"
        >
          <svg v-if="!sidebarCollapsed" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m15 18-6-6 6-6"></path>
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m9 18 6-6-6-6"></path>
          </svg>
        </button>
      </div>
      
      <!-- 新增对话按钮 -->
      <div class="p-3">
        <button 
          @click="createNewChat"
          class="w-full flex items-center justify-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-md py-2 transition-colors"
          :class="sidebarCollapsed ? 'px-0' : 'px-3'"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 5v14M5 12h14"></path>
          </svg>
          <span v-if="!sidebarCollapsed">新增对话</span>
        </button>
      </div>
      
      <!-- 历史对话记录 -->
      <div class="flex-1 overflow-y-auto scrollbar-thin py-2">
        <div 
          v-for="chat in chatHistory" 
          :key="chat.id" 
          @click="selectChat(chat)"
          class="flex items-center px-3 py-2 mx-2 rounded-md cursor-pointer transition-colors"
          :class="[
            currentChat && currentChat.id === chat.id 
              ? 'bg-zinc-800 text-white' 
              : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-100'
          ]"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
          <span class="truncate" v-if="!sidebarCollapsed">{{ chat.title }}</span>
        </div>
      </div>
      
      <!-- 底部菜单 -->
      <div class="border-t border-zinc-800 py-2">
        <router-link 
          v-for="item in menuItems" 
          :key="item.id" 
          :to="item.href"
          class="flex items-center px-3 py-2 mx-2 rounded-md transition-colors"
          :class="route.path === item.href ? 'bg-zinc-800 text-white' : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-100'"
        >
          <div class="w-5 h-5 flex items-center justify-center">
            <component :is="item.icon" />
          </div>
          <span class="ml-2 truncate" v-if="!sidebarCollapsed">{{ item.name[currentLanguage] }}</span>
        </router-link>
      </div>
    </aside>

    <!-- 侧边栏展开按钮 (当侧边栏折叠时显示) -->
    <div 
      v-if="sidebarCollapsed"
      class="fixed left-12 top-4 z-10"
    >
      <button 
        @click="toggleSidebar" 
        class="p-2 bg-zinc-800 rounded-md text-zinc-400 hover:text-zinc-100 transition-colors"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="m9 18 6-6-6-6"></path>
        </svg>
      </button>
    </div>

    <!-- 主内容区域 -->
    <main class="flex-1 flex flex-col h-screen overflow-auto transition-all duration-300" :class="sidebarCollapsed ? 'ml-12' : 'ml-64'">
      <router-view />
    </main>
    
    <!-- 通知组件 -->
    <div 
      v-if="notification.show" 
      class="fixed top-4 right-4 max-w-sm bg-zinc-800 border border-zinc-700 rounded-md shadow-lg overflow-hidden transition-all duration-300 transform"
      :class="notification.show ? 'translate-y-0 opacity-100' : '-translate-y-4 opacity-0'"
    >
      <div class="flex p-4">
        <div class="flex-shrink-0">
          <svg v-if="notification.type === 'success'" class="h-5 w-5 text-green-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
          </svg>
          <svg v-else-if="notification.type === 'error'" class="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
          <svg v-else class="h-5 w-5 text-blue-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2h-1V9a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
        </div>
        <div class="ml-3 w-0 flex-1">
          <p class="text-sm font-medium text-zinc-100">{{ notification.title }}</p>
          <p class="mt-1 text-sm text-zinc-400">{{ notification.message }}</p>
        </div>
        <div class="ml-4 flex-shrink-0 flex">
          <button @click="closeNotification" class="inline-flex text-zinc-400 hover:text-zinc-100">
            <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </button>
        </div>
      </div>
      <div class="bg-zinc-700 h-1" :style="{ width: `${notification.progress}%` }"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h, provide } from 'vue'
import { useRouter, useRoute } from 'vue-router'

// 路由配置
const router = useRouter()
const route = useRoute()

// 侧边栏折叠状态
const sidebarCollapsed = ref(false)

// 图标组件
const ModelsIcon = h('svg', {
  xmlns: 'http://www.w3.org/2000/svg',
  width: '20',
  height: '20',
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': '2',
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('path', { d: 'M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z' }),
  h('polyline', { points: '3.29 7 12 12 20.71 7' }),
  h('line', { x1: '12', y1: '22', x2: '12', y2: '12' })
])

const FormatIcon = h('svg', {
  xmlns: 'http://www.w3.org/2000/svg',
  width: '20',
  height: '20',
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': '2',
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('path', { d: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z' }),
  h('path', { d: 'M14 2v6h6' }),
  h('path', { d: 'M9 13h6' }),
  h('path', { d: 'M9 17h6' }),
  h('path', { d: 'M9 9h1' })
])

const HelpIcon = h('svg', {
  xmlns: 'http://www.w3.org/2000/svg',
  width: '20',
  height: '20',
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': '2',
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('circle', { cx: '12', cy: '12', r: '10' }),
  h('path', { d: 'M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3' }),
  h('line', { x1: '12', y1: '17', x2: '12.01', y2: '17' })
])

const AboutIcon = h('svg', {
  xmlns: 'http://www.w3.org/2000/svg',
  width: '20',
  height: '20',
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': '2',
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('circle', { cx: '12', cy: '12', r: '10' }),
  h('line', { x1: '12', y1: '8', x2: '12', y2: '12' }),
  h('line', { x1: '12', y1: '16', x2: '12.01', y2: '16' })
])

const SettingsIcon = h('svg', {
  xmlns: 'http://www.w3.org/2000/svg',
  width: '20',
  height: '20',
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': '2',
  'stroke-linecap': 'round',
  'stroke-linejoin': 'round'
}, [
  h('circle', { cx: '12', cy: '12', r: '3' }),
  h('path', { d: 'M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z' })
])

// 导航菜单项
const menuItems = [
  { 
    id: 'models',
    name: { zh: '模型', en: 'Models' },
    href: '/models',
    icon: ModelsIcon
  },
  {
    id: 'format',
    name: { zh: '格式', en: 'Format' },
    href: '/format',
    icon: FormatIcon
  },
  {
    id: 'help',
    name: { zh: '帮助', en: 'Help' },
    href: '/help',
    icon: HelpIcon
  },
  {
    id: 'about',
    name: { zh: '关于', en: 'About' },
    href: '/about',
    icon: AboutIcon
  },
  {
    id: 'settings',
    name: { zh: '设置', en: 'Settings' },
    href: '/settings',
    icon: SettingsIcon
  }
]

// 语言配置
const languages = [
  { code: 'zh', name: '中文' },
  { code: 'en', name: 'English' }
]

const currentLanguage = ref('zh')

function changeLanguage(lang) {
  currentLanguage.value = lang
}

// 切换侧边栏折叠状态
function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('sidebarCollapsed', sidebarCollapsed.value)
}

// 聊天历史
const chatHistory = ref([
  { id: 1, title: '文档格式分析 #1' },
  { id: 2, title: '论文格式检查 #2' },
  { id: 3, title: '报告格式修正 #3' }
])

// 当前选中的聊天
const currentChat = ref(null)

// 选择聊天
function selectChat(chat) {
  currentChat.value = chat
  router.push('/')
}

// 创建新聊天
function createNewChat() {
  const newChat = {
    id: Date.now(),
    title: `新对话 #${chatHistory.value.length + 1}`
  }
  chatHistory.value.push(newChat)
  selectChat(newChat)
}

// 通知系统
const notification = ref({
  show: false,
  type: 'info', // 'info', 'success', 'error'
  title: '',
  message: '',
  progress: 100,
  timeout: null
})

// 显示通知
function showNotification(type, title, message, duration = 5000) {
  // 清除之前的定时器
  if (notification.value.timeout) {
    clearTimeout(notification.value.timeout)
    clearInterval(notification.value.interval)
  }
  
  // 设置通知内容
  notification.value.type = type
  notification.value.title = title
  notification.value.message = message
  notification.value.show = true
  notification.value.progress = 100
  
  // 如果持续时间为0，则不自动关闭
  if (duration === 0) return
  
  // 设置进度条
  const interval = setInterval(() => {
    notification.value.progress -= 100 / (duration / 100)
    if (notification.value.progress <= 0) {
      clearInterval(interval)
    }
  }, 100)
  
  // 设置自动关闭
  notification.value.timeout = setTimeout(() => {
    notification.value.show = false
    clearInterval(interval)
  }, duration)
  
  notification.value.interval = interval
}

// 关闭通知
function closeNotification() {
  notification.value.show = false
  if (notification.value.timeout) {
    clearTimeout(notification.value.timeout)
    clearInterval(notification.value.interval)
  }
}

// 提供通知函数给子组件
provide('showNotification', showNotification)
provide('currentLanguage', currentLanguage)

// 组件挂载时
onMounted(() => {
  // 从本地存储加载侧边栏状态
  const savedSidebarState = localStorage.getItem('sidebarCollapsed')
  if (savedSidebarState !== null) {
    sidebarCollapsed.value = savedSidebarState === 'true'
  }
  
  // 从本地存储加载语言设置
  const savedLanguage = localStorage.getItem('language')
  if (savedLanguage) {
    currentLanguage.value = savedLanguage
  }
})
</script>

<style>
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

/* 添加页面过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--transition-speed, 300ms) ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 设置CSS变量 */
:root {
  --border-radius-sm: 4px;
  --border-radius-md: 6px;
  --border-radius-lg: 8px;
  --transition-speed: 300ms;
}
</style>