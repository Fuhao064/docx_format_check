<template>
  <div class="min-h-screen bg-zinc-950 text-zinc-100 flex">
    <!-- 侧边栏 -->
    <aside 
      class="h-screen flex flex-col bg-zinc-900 border-r border-zinc-800 transition-all duration-300 overflow-hidden"
      :class="sidebarCollapsed ? 'w-16' : 'w-64'"
    >
      <!-- 顶部Logo和标题 -->
      <div class="p-4 flex items-center border-b border-zinc-800">
        <div class="w-8 h-8 bg-zinc-800 rounded-md flex items-center justify-center mr-3">
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
          class="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md py-2 px-3 transition-colors"
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
          <div v-if="item.id === 'models'" class="w-5 h-5">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
              <polyline points="3.29 7 12 12 20.71 7"></polyline>
              <line x1="12" y1="22" x2="12" y2="12"></line>
            </svg>
          </div>
          <div v-else-if="item.id === 'format'" class="w-5 h-5">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <path d="M14 2v6h6"></path>
              <path d="M9 13h6"></path>
              <path d="M9 17h6"></path>
              <path d="M9 9h1"></path>
            </svg>
          </div>
          <div v-else-if="item.id === 'help'" class="w-5 h-5">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
              <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
          </div>
          <div v-else-if="item.id === 'about'" class="w-5 h-5">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
          </div>
          <span class="ml-2 truncate" v-if="!sidebarCollapsed">{{ item.name[currentLanguage] }}</span>
        </router-link>
      </div>
    </aside>

    <!-- 主内容区域 -->
    <main class="flex-1 flex flex-col h-screen overflow-hidden">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

// 路由配置
const router = useRouter()
const route = useRoute()

// 侧边栏折叠状态
const sidebarCollapsed = ref(false)

// 导航菜单项
const menuItems = [
  { 
    id: 'models',
    name: { zh: '模型', en: 'Models' },
    href: '/models'
  },
  {
    id: 'format',
    name: { zh: '格式', en: 'Format' },
    href: '/format'
  },
  {
    id: 'help',
    name: { zh: '帮助', en: 'Help' },
    href: '/help'
  },
  {
    id: 'about',
    name: { zh: '关于', en: 'About' },
    href: '/about'
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
</style>