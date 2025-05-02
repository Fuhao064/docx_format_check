<template>
  <div class="min-h-screen flex"
    :class="isDarkMode ? 'bg-[hsl(var(--background))] text-[hsl(var(--foreground))]' : 'bg-[hsl(var(--background))] text-[hsl(var(--foreground))]'">
    <!-- 侧边栏 -->
    <aside class="h-screen flex flex-col transition-all duration-[--transition-speed] overflow-hidden fixed z-50"
      :class="[
        isDarkMode ? 'bg-[hsl(var(--sidebar-background))] border-[hsl(var(--sidebar-border))]' : 'bg-[hsl(var(--sidebar-background))] border-[hsl(var(--sidebar-border))]',
        'border-r',
        sidebarCollapsed ? 'w-12' : 'w-64'
      ]">
      <!-- 顶部Logo和标题 -->
      <div class="p-4 flex items-center"
        :class="isDarkMode ? 'border-[hsl(var(--sidebar-border))]' : 'border-[hsl(var(--sidebar-border))]'">
        <h1 class="text-lg font-semibold truncate font-serif italic items-center text-[hsl(var(--foreground))]"
          :class="sidebarCollapsed ? 'hidden' : ''">Scriptor</h1>
        <button @click="toggleSidebar"
          :class="['text-[hsl(var(--sidebar-foreground))] hover:text-[hsl(var(--sidebar-primary))]', 'ml-auto transition-colors sidebar-toggle-button']">
          <svg v-if="!sidebarCollapsed" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
            fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m15 18-6-6 6-6"></path>
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m9 18 6-6-6-6"></path>
          </svg>
        </button>
      </div>

      <!-- 新增对话按钮 -->
      <div class="p-3">
        <button @click="createNewChat"
          class="w-full flex items-center justify-center gap-2 rounded-md py-2 transition-colors duration-[--transition-speed]"
          :class="[
            'bg-[hsl(var(--primary))] hover:bg-[hsl(var(--primary)/0.9)] text-[hsl(var(--primary-foreground))]',
            sidebarCollapsed ? 'px-0' : 'px-3'
          ]">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="8" x2="12" y2="16"></line>
            <line x1="8" y1="12" x2="16" y2="12"></line>
          </svg>

          <span v-if="!sidebarCollapsed">新增任务</span>
        </button>
      </div>

      <!-- 历史对话记录 -->
      <div class="flex-1 overflow-y-auto scrollbar-thin py-2">
        <div v-for="chat in chatHistory" :key="chat.id" class="group relative">
          <div @click="selectChat(chat)"
            class="flex items-center px-3 py-2 mx-2 rounded-md cursor-pointer transition-colors duration-[--transition-speed]"
            :class="[
              currentChat && currentChat.id === chat.id
                ? 'bg-[hsl(var(--primary)/0.2)] text-[hsl(var(--primary))]'
                : 'text-[hsl(var(--sidebar-foreground))] hover:bg-[hsl(var(--sidebar-accent))] hover:text-[hsl(var(--sidebar-accent-foreground)))]'
            ]">
            <div class="flex items-center space-x-2 w-full" :class="sidebarCollapsed ? 'justify-center' : ''">
              <div class="flex-shrink-0">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <path d="M14 2v6h6" />
                  <path d="M16 13H8" />
                  <path d="M16 17H8" />
                  <path d="M10 9H8" />
                </svg>
              </div>
              <div class="flex-1 overflow-hidden" v-if="!sidebarCollapsed">
                <div class="flex items-center">
                  <span class="truncate">{{ chat.docName || chat.title }}</span>
                  <span v-if="chat.colorClass" class="ml-1 w-2 h-2 rounded-full" :class="chat.colorClass"></span>
                </div>
                <div v-if="chat.timestamp" class="text-xs opacity-60 mt-0.5 text-[hsl(var(--muted-foreground))]">{{ new
                  Date(chat.timestamp).toLocaleTimeString() }}</div>
              </div>
            </div>
          </div>
          <!-- 删除按钮 -->
          <button
            v-if="!sidebarCollapsed && chatHistory.length > 1"
            @click="deleteChat(chat)"
            class="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 rounded-full text-[hsl(var(--sidebar-foreground))] opacity-0 group-hover:opacity-100 hover:bg-[hsl(var(--sidebar-accent))] hover:text-[hsl(var(--destructive))] transition-opacity duration-200"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 6h18"></path>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"></path>
              <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
          </button>
        </div>
      </div>

      <!-- 底部菜单 -->
      <div :class="['border-t border-[hsl(var(--sidebar-border))]', 'py-2']">
        <router-link v-for="item in menuItems" :key="item.id" :to="item.href"
          class="flex items-center transition-colors duration-[--transition-speed] rounded-md group relative" :class="[
            sidebarCollapsed ? 'justify-center py-2 mx-2' : 'px-3 py-2 mx-2',
            route.path === item.href && currentChat === null
              ? 'bg-[hsl(var(--primary)/0.2)] text-[hsl(var(--primary))]'
              : 'text-[hsl(var(--sidebar-foreground))] hover:bg-[hsl(var(--sidebar-accent))] hover:text-[hsl(var(--sidebar-accent-foreground))]'
          ]">
          <div class="w-5 h-5 flex items-center justify-center">
            <component :is="item.icon" />
          </div>
          <span class="ml-3 truncate" v-if="!sidebarCollapsed">{{ item.name[currentLanguage] }}</span>
          <!-- 悬停提示 -->
          <div v-if="sidebarCollapsed"
            class="absolute left-full ml-2 px-2 py-1 bg-black bg-opacity-80 text-white text-xs rounded pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50">
            {{ item.name[currentLanguage] }}
          </div>
        </router-link>
      </div>
    </aside>


    <!-- 主内容区域 -->
    <main class="flex-1 flex flex-col h-screen overflow-auto transition-all duration-[--transition-speed]"
      :class="sidebarCollapsed ? 'ml-12' : 'ml-64'">
      <div class="flex-1 flex flex-col overflow-hidden">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>


    <!-- 通知容器 -->
    <div class="fixed top-4 right-4 flex flex-row-reverse items-start gap-4 z-50">
      <!-- 通知组件 -->
      <div v-if="notification.show"
        class="flex-shrink-0 w-80 overflow-hidden transition-all duration-[--transition-speed] transform rounded-lg shadow-lg"
        :class="[
          'bg-[hsl(var(--card))] border border-[hsl(var(--border))]',
          notification.show ? 'translate-y-0 opacity-100' : '-translate-y-4 opacity-0'
        ]">
        <div class="flex p-4">
          <div class="flex-shrink-0">
            <svg v-if="notification.type === 'success'" class="h-5 w-5 text-green-400"
              xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clip-rule="evenodd" />
            </svg>
            <svg v-else-if="notification.type === 'error'" class="h-5 w-5 text-red-400"
              xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clip-rule="evenodd" />
            </svg>
            <svg v-else class="h-5 w-5 text-blue-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2h-1V9a1 1 0 00-1-1z"
                clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3 w-0 flex-1">
            <p class="text-sm font-medium text-[hsl(var(--foreground))]">{{ notification.title }}</p>
            <p class="mt-1 text-sm text-[hsl(var(--muted-foreground))]">{{ notification.message }}</p>
          </div>
          <div class="ml-4 flex-shrink-0 flex">
            <button @click="closeNotification"
              class="inline-flex transition-colors text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]">
              <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clip-rule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
        <div
          :class="notification.type === 'success' ? 'bg-green-500' : notification.type === 'error' ? 'bg-red-500' : notification.type === 'warning' ? 'bg-yellow-500' : 'bg-[hsl(var(--primary))]'"
          class="h-1" :style="{ width: `${notification.progress}%` }"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h, provide, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  getAllTasks,
  createTask,
  deleteTask,
  switchTask,
  getCurrentTaskState
} from './lib/db.js'

// 路由配置
const router = useRouter()
const route = useRoute()

// 主题模式
const isDarkMode = ref(true)
provide('isDarkMode', isDarkMode)

// 侧边栏折叠状态
const sidebarCollapsed = ref(true)
provide('sidebarCollapsed', sidebarCollapsed)

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

// 菜单项配置
const menuItems = [
  {
    id: 'models',
    name: {
      'zh-CN': '模型管理',
      'en-US': 'Models'
    },
    href: '/models',
    icon: ModelsIcon
  },
  {
    id: 'format',
    name: {
      'zh-CN': '格式设置',
      'en-US': 'Format'
    },
    href: '/format',
    icon: FormatIcon
  },
  {
    id: 'help',
    name: {
      'zh-CN': '帮助',
      'en-US': 'Help'
    },
    href: '/help',
    icon: HelpIcon
  },
  {
    id: 'about',
    name: {
      'zh-CN': '关于',
      'en-US': 'About'
    },
    href: '/about',
    icon: AboutIcon
  },
]

// 语言设置
const currentLanguage = ref('zh-CN')


// 切换侧边栏
function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

// 聊天历史
const chatHistory = ref([])

// 当前聊天
const currentChat = ref(null)
provide('currentTask', currentChat)

// 加载任务列表
async function loadTasks() {
  try {
    const tasks = await getAllTasks();
    chatHistory.value = tasks.map(task => ({
      id: task.id,
      title: task.title,
      docName: task.title,
      timestamp: task.lastUpdated
    }));

    // 查找当前活动的任务
    if (chatHistory.value.length > 0) {
      const currentTaskState = await getCurrentTaskState();
      const currentTaskId = currentTaskState.taskId;
      const currentTaskIndex = chatHistory.value.findIndex(chat => chat.id === currentTaskId);

      if (currentTaskIndex >= 0) {
        // 确保创建新引用，触发监听器
        currentChat.value = { ...chatHistory.value[currentTaskIndex] };
      } else if (chatHistory.value.length > 0) {
        // 如果没有找到当前任务，默认选中第一个
        await switchTask(chatHistory.value[0].id);
        currentChat.value = { ...chatHistory.value[0] };
      }
    }
  } catch (error) {
    console.error('加载任务列表失败:', error);
  }
}

// 选择聊天
async function selectChat(chat) {
  try {
    // 如果当前已经选中该任务，则清空引用再重新设置，确保触发watch
    if (currentChat.value && currentChat.value.id === chat.id) {
      // 创建一个临时变量保存当前任务ID
      const taskId = chat.id;
      // 清空当前任务引用
      currentChat.value = null;
      // 等待视图更新
      await nextTick();
      // 重新加载任务状态
      await switchTask(taskId);
      // 重新设置当前任务，添加时间戳确保引用不同
      currentChat.value = { ...chat, _timestamp: Date.now() };
    } else {
      // 正常切换任务
      // 先加载任务状态
      await switchTask(chat.id);
      // 更新当前任务引用
      currentChat.value = { ...chat, _timestamp: Date.now() };
    }

    // 跳转到首页，确保显示对话内容
    if (route.path !== '/') {
      router.push('/');
    }
  } catch (error) {
    console.error('切换任务失败:', error);
    showNotification('error', '切换失败', '无法切换到所选任务', 3000);
  }
}

// 创建新聊天
async function createNewChat() {
  try {
    // 创建新任务
    const taskId = await createTask(`新任务 #${chatHistory.value.length + 1}`);

    // 重新加载任务列表
    await loadTasks();

    // 选择新创建的任务
    const newTaskIndex = chatHistory.value.findIndex(chat => chat.id === taskId);
    if (newTaskIndex >= 0) {
      const newChat = chatHistory.value[newTaskIndex];
      // 切换到选择的任务
      await switchTask(newChat.id);
      // 创建新引用以触发监听器
      currentChat.value = { ...newChat };
    }

    // 确保跳转到聊天页面
    router.push('/');
  } catch (error) {
    console.error('创建新任务失败:', error);
    showNotification('error', '创建失败', '无法创建新任务', 3000);
  }
}

// 删除聊天
async function deleteChat(chat) {
  try {
    await deleteTask(chat.id);

    // 重新加载任务列表
    await loadTasks();

    // 如果删除的是当前选中的聊天，自动选择第一个
    if (currentChat.value && currentChat.value.id === chat.id) {
      currentChat.value = chatHistory.value.length > 0 ? chatHistory.value[0] : null;
    }
  } catch (error) {
    console.error('删除任务失败:', error);
    showNotification('error', '删除失败', '无法删除任务', 3000);
  }
}

// 通知系统
const notification = ref({
  show: false,
  type: 'info',
  title: '',
  message: '',
  progress: 100,
  timeout: null
})

// 显示通知
function showNotification(type, title, message, duration = 5000) {
  // 清除之前的超时
  if (notification.value.timeout) {
    clearTimeout(notification.value.timeout)
  }

  // 设置新通知
  notification.value = {
    show: true,
    type,
    title,
    message,
    progress: 100,
    timeout: null
  }

  if (duration > 0) {
    const startTime = Date.now()
    const animate = () => {
      const elapsed = Date.now() - startTime
      const remaining = duration - elapsed

      if (remaining <= 0) {
        closeNotification()
      } else {
        notification.value.progress = (remaining / duration) * 100
        notification.value.timeout = requestAnimationFrame(animate)
      }
    }

    notification.value.timeout = requestAnimationFrame(animate)
  }
}

// 关闭通知
function closeNotification() {
  if (notification.value.timeout) {
    cancelAnimationFrame(notification.value.timeout)
  }
  notification.value.show = false
  notification.value.timeout = null
}

// 更新当前聊天的文档信息
async function updateChatHistory(docName, colorClass) {
  if (currentChat.value) {
    // 更新本地状态
    currentChat.value.docName = docName;
    currentChat.value.colorClass = colorClass;

    // 更新聊天历史中对应的项
    const chatIndex = chatHistory.value.findIndex(chat => chat.id === currentChat.value.id);
    if (chatIndex !== -1) {
      chatHistory.value[chatIndex] = { ...currentChat.value };
    }
  }
}

// 切换主题
function toggleTheme() {
  isDarkMode.value = !isDarkMode.value

  // 将主题状态添加到 HTML 元素，方便全局样式访问
  if (isDarkMode.value) {
    document.documentElement.classList.add('dark')
    document.documentElement.classList.remove('light')
  } else {
    document.documentElement.classList.add('light')
    document.documentElement.classList.remove('dark')
  }

  // 存储用户主题偏好
  localStorage.setItem('theme', isDarkMode.value ? 'dark' : 'light')
}

// 提供函数给子组件
provide('showNotification', showNotification)
provide('currentLanguage', currentLanguage)
provide('updateChatHistory', updateChatHistory)
provide('toggleTheme', toggleTheme)
provide('isCollapsed', sidebarCollapsed)
provide('deleteChat', deleteChat)

// 初始化主题
onMounted(async () => {
  // 加载任务列表
  await loadTasks();

  // 检查用户保存的偏好设置
  const savedTheme = localStorage.getItem('theme')

  // 如果用户有保存的主题设置，应用它
  if (savedTheme) {
    isDarkMode.value = savedTheme === 'dark'
  } else {
    // 否则检查系统主题偏好
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    isDarkMode.value = prefersDark
  }

  // 应用主题样式
  if (isDarkMode.value) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.add('light')
  }
})
</script>

<style scoped>
/* 自定义滚动条样式 */
.scrollbar-thin::-webkit-scrollbar {
  width: 6px;
  /* Width of the scrollbar */
  height: 6px;
}

.scrollbar-thin::-webkit-scrollbar-track {
  background: hsl(var(--background));
  /* Color of the track */
}

.scrollbar-thin::-webkit-scrollbar-thumb {
  background: hsl(var(--border));
  /* Color of the scroll thumb */
  border-radius: 3px;
}

.scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background: hsl(var(--foreground)/0.7);
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


/* 侧边栏折叠按钮样式 */
.sidebar-toggle-button {
  display: flex;
  align-items: center;
  justify-content: center;
}

.sidebar-toggle-button svg {
  width: 100%;
  height: 100%;
}

/* 添加字体样式 */
.font-serif {
  font-family: 'Georgia', serif;
}

.italic {
  font-style: italic;
}
</style>