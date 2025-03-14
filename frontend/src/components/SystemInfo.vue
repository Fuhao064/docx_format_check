<template>
  <div class="system-info p-6 rounded-lg" :class="isDarkMode ? 'bg-zinc-800/50' : 'bg-gray-100'">
    <h2 class="text-xl font-semibold mb-4" :class="isDarkMode ? 'text-zinc-100' : 'text-gray-900'">{{ title }}</h2>
    
    <div class="space-y-6">
      <div v-for="(section, index) in sections" :key="index" class="space-y-2">
        <h3 class="text-lg font-medium" :class="isDarkMode ? 'text-zinc-200' : 'text-gray-900'">{{ section.title }}</h3>
        <p class="text-sm leading-relaxed" :class="isDarkMode ? 'text-zinc-400' : 'text-gray-700'">{{ section.content }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { inject } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: '系统介绍'
  },
  sections: {
    type: Array,
    default: () => [
      {
        title: '系统介绍',
        content: '文档格式检查系统是一个专业的工具，用于检查和分析文档的格式是否符合特定的规范要求。系统支持上传Word文档(.docx)，并可以根据预设或自定义的格式规范进行检查。'
      },
      {
        title: '核心功能',
        content: '自动分析文档结构、检查格式规范合规性、生成详细的分析报告、支持自定义格式要求、提供格式修正建议。'
      },
      {
        title: '技术特点',
        content: '采用先进的文档解析技术，精确识别文档结构和格式；使用人工智能技术分析文档内容，提供智能化的格式建议；支持批量处理，提高工作效率；界面友好，操作简单直观。'
      }
    ]
  }
})

const isDarkMode = inject('isDarkMode')
</script>

<style scoped>
.system-info {
  max-width: 100%;
  transition: all 0.3s ease;
}
</style> 