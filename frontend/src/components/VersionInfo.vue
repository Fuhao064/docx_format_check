<template>
  <div class="version-info p-6 rounded-lg" :class="isDarkMode ? 'bg-zinc-800/50' : 'bg-gray-100'">
    <h2 class="text-xl font-semibold mb-4" :class="isDarkMode ? 'text-zinc-100' : 'text-gray-900'">{{ title }}</h2>
    
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <span class="text-sm font-medium" :class="isDarkMode ? 'text-zinc-300' : 'text-gray-700'">当前版本</span>
        <span class="text-sm px-2 py-1 rounded" :class="isDarkMode ? 'bg-blue-900/30 text-blue-400' : 'bg-blue-100 text-blue-700'">v{{ version }}</span>
      </div>
      
      <div class="flex items-center justify-between">
        <span class="text-sm font-medium" :class="isDarkMode ? 'text-zinc-300' : 'text-gray-700'">发布日期</span>
        <span class="text-sm" :class="isDarkMode ? 'text-zinc-400' : 'text-gray-600'">{{ releaseDate }}</span>
      </div>
      
      <div class="flex items-center justify-between">
        <span class="text-sm font-medium" :class="isDarkMode ? 'text-zinc-300' : 'text-gray-700'">更新状态</span>
        <span class="text-sm px-2 py-1 rounded" :class="isDarkMode ? 'bg-green-900/30 text-green-400' : 'bg-green-100 text-green-700'">{{ updateStatus }}</span>
      </div>
    </div>
    
    <div class="mt-4 pt-4 border-t" :class="isDarkMode ? 'border-zinc-700' : 'border-gray-200'">
      <h3 class="text-sm font-medium mb-2" :class="isDarkMode ? 'text-zinc-300' : 'text-gray-700'">更新日志</h3>
      <ul class="text-sm space-y-2">
        <li v-for="(log, index) in changelog" :key="index" class="flex items-start">
          <span class="inline-block w-1.5 h-1.5 rounded-full mt-1.5 mr-2" :class="isDarkMode ? 'bg-zinc-500' : 'bg-gray-500'"></span>
          <span :class="isDarkMode ? 'text-zinc-400' : 'text-gray-600'">{{ log }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { inject } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: '版本信息'
  },
  version: {
    type: String,
    default: '1.0.0'
  },
  releaseDate: {
    type: String,
    default: '2023-06-15'
  },
  updateStatus: {
    type: String,
    default: '最新版本'
  },
  changelog: {
    type: Array,
    default: () => [
      '优化了文档解析算法，提高了格式识别准确率',
      '改进了用户界面，提升了用户体验',
      '修复了部分已知问题',
      '增加了更多格式检查规则'
    ]
  }
})

const isDarkMode = inject('isDarkMode')
</script>

<style scoped>
.version-info {
  max-width: 100%;
  transition: all 0.3s ease;
}
</style> 