<template>
  <div class="rounded-lg border transition-all duration-300 overflow-hidden mb-4"
    :class="[
      isDarkMode ? 'bg-zinc-800 border-zinc-700' : 'bg-white border-gray-200',
      expanded ? 'max-h-[500px]' : 'max-h-[42px]'
    ]"
  >
    <div class="flex items-center justify-between p-2 cursor-pointer" @click="toggleExpand">
      <div class="flex items-center">
        <span class="font-medium" :class="isDarkMode ? 'text-zinc-100' : 'text-gray-900'">
          {{ title }}
          <span v-if="errorCount > 0" class="ml-2 px-2 py-0.5 text-xs rounded-full" 
            :class="isDarkMode ? 'bg-red-900/30 text-red-300' : 'bg-red-100 text-red-700'">
            {{ errorCount }}个问题
          </span>
        </span>
      </div>
      <button class="p-1 rounded-md transition-colors"
        :class="isDarkMode ? 'text-zinc-400 hover:text-zinc-100' : 'text-gray-500 hover:text-gray-700'"
      >
        <svg v-if="expanded" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="18 15 12 9 6 15"></polyline>
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
      </button>
    </div>
    
    <div class="p-4 overflow-y-auto max-h-[450px] scrollbar-thin">
      <slot></slot>
    </div>
  </div>
</template>

<script setup>
import { ref, inject } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: '处理状态'
  },
  errorCount: {
    type: Number,
    default: 0
  },
  initialExpanded: {
    type: Boolean,
    default: false
  }
})

const isDarkMode = inject('isDarkMode')
const expanded = ref(props.initialExpanded)

function toggleExpand() {
  expanded.value = !expanded.value
}
</script>