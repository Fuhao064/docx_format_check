<template>
  <div class="p-6">
    <div class="mb-6">
      <h1 class="text-2xl font-semibold mb-2">设置</h1>
      <p class="text-zinc-400">自定义应用程序设置</p>
    </div>
    
    <!-- 语言设置 -->
    <div class="bg-zinc-800 rounded-lg p-6 mb-6">
      <h2 class="text-lg font-medium mb-4">语言设置</h2>
      <div class="flex flex-col space-y-4">
        <div class="flex items-center space-x-4">
          <span class="text-zinc-300 w-24">当前语言:</span>
          <div class="flex space-x-2">
            <button 
              v-for="lang in languages" 
              :key="lang.code"
              @click="changeLanguage(lang.code)"
              class="px-4 py-2 rounded-md transition-colors"
              :class="currentLanguage === lang.code 
                ? 'bg-zinc-700 text-white' 
                : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-700 hover:text-white'"
            >
              {{ lang.name }}
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 外观设置 -->
    <div class="bg-zinc-800 rounded-lg p-6 mb-6">
      <h2 class="text-lg font-medium mb-4">外观设置</h2>
      <div class="flex flex-col space-y-4">
        <div class="flex items-center space-x-4">
          <span class="text-zinc-300 w-24">主题模式:</span>
          <div class="flex space-x-2">
            <button 
              @click="changeTheme('dark')"
              class="px-4 py-2 rounded-md transition-colors"
              :class="currentTheme === 'dark' 
                ? 'bg-zinc-700 text-white' 
                : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-700 hover:text-white'"
            >
              暗色模式
            </button>
            <button 
              @click="changeTheme('light')"
              class="px-4 py-2 rounded-md transition-colors"
              :class="currentTheme === 'light' 
                ? 'bg-zinc-700 text-white' 
                : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-700 hover:text-white'"
            >
              亮色模式
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 界面设置 -->
    <div class="bg-zinc-800 rounded-lg p-6">
      <h2 class="text-lg font-medium mb-4">界面设置</h2>
      <div class="flex flex-col space-y-4">
        <div class="flex items-center space-x-4">
          <span class="text-zinc-300 w-24">圆角样式:</span>
          <div class="flex space-x-2">
            <button 
              @click="changeCornerStyle('subtle')"
              class="px-4 py-2 rounded-md transition-colors"
              :class="cornerStyle === 'subtle' 
                ? 'bg-zinc-700 text-white' 
                : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-700 hover:text-white'"
            >
              微圆角
            </button>
            <button 
              @click="changeCornerStyle('rounded')"
              class="px-4 py-2 rounded-md transition-colors"
              :class="cornerStyle === 'rounded' 
                ? 'bg-zinc-700 text-white' 
                : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-700 hover:text-white'"
            >
              标准圆角
            </button>
          </div>
        </div>
        
        <div class="flex items-center space-x-4">
          <span class="text-zinc-300 w-24">动画效果:</span>
          <label class="inline-flex items-center cursor-pointer">
            <input 
              type="checkbox" 
              v-model="enableAnimations" 
              class="sr-only peer"
              @change="toggleAnimations"
            >
            <div class="relative w-11 h-6 bg-zinc-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
            <span class="ms-3 text-sm font-medium text-zinc-300">{{ enableAnimations ? '已启用' : '已禁用' }}</span>
          </label>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

// 路由
const router = useRouter()

// 语言设置
const languages = [
  { code: 'zh', name: '中文' },
  { code: 'en', name: 'English' }
]
const currentLanguage = ref('zh')

// 主题设置
const currentTheme = ref('dark')
const cornerStyle = ref('subtle')
const enableAnimations = ref(true)

// 加载设置
onMounted(() => {
  // 从本地存储加载设置
  const savedLanguage = localStorage.getItem('language')
  const savedTheme = localStorage.getItem('theme')
  const savedCornerStyle = localStorage.getItem('cornerStyle')
  const savedAnimations = localStorage.getItem('enableAnimations')
  
  if (savedLanguage) currentLanguage.value = savedLanguage
  if (savedTheme) currentTheme.value = savedTheme
  if (savedCornerStyle) cornerStyle.value = savedCornerStyle
  if (savedAnimations !== null) enableAnimations.value = savedAnimations === 'true'
  
  // 应用设置
  applyTheme()
  applyCornerStyle()
  applyAnimations()
})

// 更改语言
function changeLanguage(lang) {
  currentLanguage.value = lang
  localStorage.setItem('language', lang)
  
  // 这里可以添加更多的语言切换逻辑
  // 例如通知其他组件语言已更改
}

// 更改主题
function changeTheme(theme) {
  currentTheme.value = theme
  localStorage.setItem('theme', theme)
  applyTheme()
}

// 应用主题
function applyTheme() {
  const root = document.documentElement
  
  if (currentTheme.value === 'dark') {
    root.classList.add('dark-theme')
    root.classList.remove('light-theme')
    document.body.style.backgroundColor = '#09090b'
    document.body.style.color = '#f4f4f5'
  } else {
    root.classList.add('light-theme')
    root.classList.remove('dark-theme')
    document.body.style.backgroundColor = '#f4f4f5'
    document.body.style.color = '#18181b'
  }
}

// 更改圆角样式
function changeCornerStyle(style) {
  cornerStyle.value = style
  localStorage.setItem('cornerStyle', style)
  applyCornerStyle()
}

// 应用圆角样式
function applyCornerStyle() {
  const root = document.documentElement
  
  if (cornerStyle.value === 'subtle') {
    root.style.setProperty('--border-radius-sm', '4px')
    root.style.setProperty('--border-radius-md', '6px')
    root.style.setProperty('--border-radius-lg', '8px')
  } else {
    root.style.setProperty('--border-radius-sm', '6px')
    root.style.setProperty('--border-radius-md', '8px')
    root.style.setProperty('--border-radius-lg', '12px')
  }
}

// 切换动画
function toggleAnimations() {
  localStorage.setItem('enableAnimations', enableAnimations.value)
  applyAnimations()
}

// 应用动画设置
function applyAnimations() {
  const root = document.documentElement
  
  if (enableAnimations.value) {
    root.style.setProperty('--transition-speed', '300ms')
  } else {
    root.style.setProperty('--transition-speed', '0ms')
  }
}
</script> 