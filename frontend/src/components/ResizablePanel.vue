<template>
  <div class="flex h-full">
    <!-- 左侧面板 -->
    <div 
      class="flex-1 overflow-hidden transition-all duration-300"
      :style="{ width: `${leftPanelWidth}%` }"
    >
      <slot name="left"></slot>
    </div>
    
    <!-- 分隔线 -->
    <div 
      class="w-1 cursor-col-resize flex items-center justify-center hover:bg-opacity-50 transition-colors group relative"
      :class="isDarkMode ? 'hover:bg-blue-700' : 'hover:bg-blue-300'"
      @mousedown="startResize"
    >
      <div 
        class="w-1 h-8 rounded-full"
        :class="isDarkMode ? 'bg-zinc-700' : 'bg-gray-300'"
      ></div>
      <!-- 拖拽图标 -->
      <div class="absolute p-1 rounded-full bg-opacity-80 text-white transform -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity"
        :class="isDarkMode ? 'bg-slate-700' : 'bg-slate-300'"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M7 8l5 5 5-5"/>
          <path d="M7 17l5-5 5 5"/>
        </svg>
      </div>
    </div>
    
    <!-- 右侧面板 -->
    <div 
      class="overflow-hidden transition-all duration-300"
      :style="{ width: `${100 - leftPanelWidth}%` }"
    >
      <div class="h-full flex flex-col">
        <div class="flex items-center justify-between p-2 border-b"
          :class="isDarkMode ? 'border-zinc-800' : 'border-gray-200'"
        >
          <h3 class="text-sm font-medium truncate">
            <slot name="right-title">预览</slot>
          </h3>
          <div class="flex items-center space-x-1">
            <button 
              @click="toggleMaximize"
              class="p-1 rounded transition-colors"
              :class="isDarkMode ? 'hover:bg-zinc-700 text-zinc-400 hover:text-zinc-100' : 'hover:bg-gray-200 text-gray-500 hover:text-gray-700'"
            >
              <svg v-if="isMaximized" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="4 14 10 14 10 20"></polyline>
                <polyline points="20 10 14 10 14 4"></polyline>
                <line x1="14" y1="10" x2="21" y2="3"></line>
                <line x1="3" y1="21" x2="10" y2="14"></line>
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="15 3 21 3 21 9"></polyline>
                <polyline points="9 21 3 21 3 15"></polyline>
                <line x1="21" y1="3" x2="14" y2="10"></line>
                <line x1="3" y1="21" x2="10" y2="14"></line>
              </svg>
            </button>
          </div>
        </div>
        <div class="flex-1 overflow-hidden">
          <slot name="right"></slot>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  initialLeftWidth: {
    type: Number,
    default: 60
  }
})

const emit = defineEmits(['resize', 'maximize'])

const isDarkMode = inject('isDarkMode')
const leftPanelWidth = ref(props.initialLeftWidth)
const isResizing = ref(false)
const isMaximized = ref(false)
const previousLeftWidth = ref(props.initialLeftWidth)

function startResize(e) {
  isResizing.value = true
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', stopResize)
  // 阻止默认行为和冒泡
  e.preventDefault()
  e.stopPropagation()
}

function handleMouseMove(e) {
  if (!isResizing.value) return
  
  const container = e.currentTarget
  const containerRect = container.getBoundingClientRect()
  const containerWidth = containerRect.width
  
  // 计算鼠标位置相对于容器的百分比
  const mouseX = e.clientX - containerRect.left
  let newLeftWidth = (mouseX / containerWidth) * 100
  
  // 限制最小和最大宽度
  newLeftWidth = Math.max(20, Math.min(newLeftWidth, 80))
  
  leftPanelWidth.value = newLeftWidth
  emit('resize', newLeftWidth)
}

function stopResize() {
  isResizing.value = false
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', stopResize)
}

function toggleMaximize() {
  if (isMaximized.value) {
    // 恢复之前的宽度
    leftPanelWidth.value = previousLeftWidth.value
  } else {
    // 保存当前宽度并最大化右侧面板
    previousLeftWidth.value = leftPanelWidth.value
    leftPanelWidth.value = 0
  }
  
  isMaximized.value = !isMaximized.value
  emit('maximize', isMaximized.value)
}

onMounted(() => {
  // 确保在组件挂载时设置初始宽度
  leftPanelWidth.value = props.initialLeftWidth
})

onUnmounted(() => {
  // 确保在组件卸载时移除事件监听器
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', stopResize)
})
</script>