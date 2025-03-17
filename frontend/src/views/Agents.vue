<template>
  <div class="p-6" :class="{ 'bg-white text-black': !isDarkMode, 'bg-zinc-950 text-zinc-100': isDarkMode }">
    <div class="mb-6">
      <h1 class="text-2xl font-semibold mb-2">Agent中心</h1>
      <p :class="isDarkMode ? 'text-zinc-400' : 'text-gray-600'">智能Agent助手，帮助你解决文档格式问题</p>
    </div>
    
    <!-- Agent列表 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div 
        v-for="agent in agents" 
        :key="agent.id" 
        class="p-6 rounded-lg border transition-colors"
        :class="[
          isDarkMode ? 'bg-zinc-800 border-zinc-700 hover:bg-zinc-700' : 'bg-white border-gray-200 hover:bg-gray-50',
        ]"
      >
        <div class="flex items-center mb-4">
          <div class="w-10 h-10 rounded-full flex items-center justify-center mr-3"
            :class="agent.bgColor"
          >
            <component :is="agent.icon" class="w-6 h-6" :class="agent.iconColor" />
          </div>
          <h3 class="text-lg font-medium" :class="isDarkMode ? 'text-zinc-100' : 'text-gray-900'">{{ agent.name }}</h3>
        </div>
        
        <p class="mb-4 text-sm" :class="isDarkMode ? 'text-zinc-400' : 'text-gray-600'">{{ agent.description }}</p>
        
        <div class="mt-auto">
          <button 
            @click="navigateToHome"
            class="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-md transition-colors"
            :class="isDarkMode ? 'bg-blue-600 hover:bg-blue-700 text-white' : 'bg-blue-500 hover:bg-blue-600 text-white'"
          >
            <span>开始使用</span>
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m9 18 6-6-6-6"></path>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, h, inject } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const isDarkMode = inject('isDarkMode', ref(true))

// Agent数据
const agents = [
  {
    id: 1,
    name: 'Agent 1：结构修复',
    description: '专注于修复文档结构问题，如标题层级、段落格式等。帮助你确保文档结构符合规范，提高可读性和专业性。',
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
    description: '提供字体、颜色、间距等样式优化建议，提升文档美观度。让你的文档看起来更加专业、一致和美观。',
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
    description: '检查文档是否符合特定标准或规范，提供合规性建议。确保你的文档符合行业标准、学术要求或组织规范。',
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

// 导航到首页
function navigateToHome() {
  router.push('/')
}
</script> 