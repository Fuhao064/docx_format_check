<template>
  <div class="dashboard-overview p-6 overflow-y-auto">
    <h1 class="text-2xl font-bold mb-6 text-[hsl(var(--foreground))]">工作台概览</h1>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <StatCard
        title="总任务数"
        :value="stats.totalTasks"
        icon="tasks"
        color="primary"
      />
      <StatCard
        title="已完成"
        :value="stats.completedTasks"
        icon="check"
        color="success"
      />
      <StatCard
        title="进行中"
        :value="stats.inProgressTasks"
        icon="clock"
        color="warning"
      />
      <StatCard
        title="格式问题"
        :value="stats.recentErrors"
        icon="alert"
        color="destructive"
      />
    </div>

    <!-- 最近任务 -->
    <div class="mb-8">
      <h2 class="text-lg font-semibold mb-4 text-[hsl(var(--foreground))]">最近任务</h2>
      <div class="bg-[hsl(var(--card))] rounded-lg border border-[hsl(var(--border))] p-4">
        <div v-if="recentTasks.length === 0" class="text-center py-8 text-[hsl(var(--muted-foreground))]">
          暂无任务
        </div>
        <div v-else class="space-y-2">
          <div
            v-for="task in recentTasks"
            :key="task.id"
            class="flex items-center justify-between p-3
                   rounded-lg hover:bg-[hsl(var(--secondary))]
                   transition-colors cursor-pointer"
            @click="openTask(task)"
          >
            <div class="flex items-center gap-3">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                stroke-width="2" class="text-[hsl(var(--primary))]">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
              </svg>
              <span class="text-[hsl(var(--foreground))]">{{ task.title }}</span>
            </div>
            <span class="text-xs text-[hsl(var(--muted-foreground))]">
              {{ formatDate(task.lastUpdated || task.createdAt) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="mb-8">
      <h2 class="text-lg font-semibold mb-4 text-[hsl(var(--foreground))]">快捷操作</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button
          @click="createNewTask"
          class="flex items-center gap-3 p-4 rounded-lg
                 bg-[hsl(var(--card))] border border-[hsl(var(--border))]
                 hover:bg-[hsl(var(--secondary))]
                 transition-colors text-[hsl(var(--foreground))]"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" class="text-[hsl(var(--primary))]">
            <path d="M12 5v14M5 12h14"></path>
          </svg>
          <span>新建任务</span>
        </button>
        <button
          @click="goToFiles"
          class="flex items-center gap-3 p-4 rounded-lg
                 bg-[hsl(var(--card))] border border-[hsl(var(--border))]
                 hover:bg-[hsl(var(--secondary))]
                 transition-colors text-[hsl(var(--foreground))]"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" class="text-[hsl(var(--primary))]">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="17 8 12 3 7 8"></polyline>
            <line x1="12" y1="3" x2="12" y2="15"></line>
          </svg>
          <span>上传文件</span>
        </button>
        <button
          @click="showModels"
          class="flex items-center gap-3 p-4 rounded-lg
                 bg-[hsl(var(--card))] border border-[hsl(var(--border))]
                 hover:bg-[hsl(var(--secondary))]
                 transition-colors text-[hsl(var(--foreground))]"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" class="text-[hsl(var(--primary))]">
            <path d="M12 2a10 10 0 1 0 10 10 10 10 0 0 0-10-10z"></path>
            <path d="M12 6v6l4 2"></path>
          </svg>
          <span>模型设置</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { inject, ref } from 'vue'
import StatCard from './StatCard.vue'

const stats = inject('stats', ref({
  totalTasks: 0,
  completedTasks: 0,
  inProgressTasks: 0,
  totalFiles: 0,
  recentErrors: 0
}))

const recentTasks = inject('recentTasks', ref([]))
const switchTab = inject('switchTab', () => {})
const showNotification = inject('showNotification', null)

function formatDate(date) {
  if (!date) return '未知'
  const d = new Date(date)
  if (isNaN(d.getTime())) return '未知'
  return d.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function openTask(task) {
  showNotification('info', '打开任务', `正在打开任务: ${task.title}`, 1000)
}

function createNewTask() {
  showNotification('info', '新建任务', '请使用侧边栏创建新任务', 2000)
}

function goToFiles() {
  switchTab('main')
}

function showModels() {
  showNotification('info', '模型设置', '请使用侧边栏访问模型设置', 2000)
}
</script>

<style scoped>
.dashboard-overview {
  height: 100%;
}
</style>
