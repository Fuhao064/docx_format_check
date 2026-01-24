<template>
  <div class="notification-bar">
    <transition-group name="notification" tag="div" class="notifications-container">
      <div
        v-for="notification in notifications"
        :key="notification.id"
        class="notification-item p-4 rounded-lg shadow-lg flex items-center gap-3 min-w-[320px]"
        :class="{
          'bg-[hsl(var(--destructive))] text-[hsl(var(--destructive-foreground))]': notification.level === 'error',
          'bg-[hsl(var(--warning))] text-[hsl(var(--warning-foreground))]': notification.level === 'warning',
          'bg-[hsl(var(--success))] text-[hsl(var(--success-foreground))]': notification.level === 'success',
          'bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]': notification.level === 'info'
        }"
      >
        <!-- 图标 -->
        <svg v-if="notification.level === 'success'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
          <polyline points="22 4 12 14.01 9 11.01"></polyline>
        </svg>
        <svg v-else-if="notification.level === 'error'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="15" y1="9" x2="9" y2="15"></line>
          <line x1="9" y1="9" x2="15" y2="15"></line>
        </svg>
        <svg v-else-if="notification.level === 'warning'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3l-8.47-14.14a2 2 0 0 0-3.42 0z"></path>
          <line x1="12" y1="9" x2="12" y2="13"></line>
          <line x1="12" y1="17" x2="12.01" y2="17"></line>
        </svg>
        <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="16" x2="12" y2="12"></line>
          <line x1="12" y1="8" x2="12.01" y2="8"></line>
        </svg>

        <!-- 内容 -->
        <div class="flex-1">
          <p v-if="notification.title" class="font-semibold text-sm">{{ notification.title }}</p>
          <p class="text-sm">{{ notification.message }}</p>
        </div>

        <!-- 关闭按钮 -->
        <button
          @click="removeNotification(notification.id)"
          class="p-1 rounded hover:bg-black/10 transition-colors"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>
    </transition-group>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const notifications = ref([])
let nextId = 1

onMounted(() => {
  // 全局通知函数
  window.showNotification = addNotification
})

onUnmounted(() => {
  delete window.showNotification
})

function addNotification(level) {
  return (title, message, duration = 3000) => {
    const id = nextId++
    const notification = {
      id,
      level,
      title,
      message,
      timestamp: new Date()
    }

    notifications.value.push(notification)

    if (duration > 0) {
      setTimeout(() => {
        removeNotification(id)
      }, duration)
    }
  }
}

function removeNotification(id) {
  const index = notifications.value.findIndex(n => n.id === id)
  if (index !== -1) {
    notifications.value.splice(index, 1)
  }
}

// 暴露通知函数供其他组件使用
defineExpose({
  addNotification,
  removeNotification
})
</script>

<style scoped>
.notification-bar {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 12px;
  pointer-events: none;
}

.notifications-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.notification-item {
  pointer-events: auto;
  max-width: 400px;
}

.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.notification-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>
