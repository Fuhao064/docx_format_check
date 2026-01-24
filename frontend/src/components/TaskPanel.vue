<template>
  <div class="task-panel p-6 overflow-y-auto">
    <h1 class="text-2xl font-bold mb-6 text-[hsl(var(--foreground))]">任务管理</h1>

    <div class="bg-[hsl(var(--card))] rounded-lg border border-[hsl(var(--border))] p-4">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-lg font-semibold text-[hsl(var(--foreground))]">所有任务</h2>
        <button
          @click="createTask"
          class="flex items-center gap-2 px-4 py-2 rounded-lg
                 bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]
                 hover:bg-[hsl(var(--primary)/0.9)] transition-colors"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2">
            <path d="M12 5v14M5 12h14"></path>
          </svg>
          新建任务
        </button>
      </div>

      <div v-if="tasks.length === 0" class="text-center py-12 text-[hsl(var(--muted-foreground))]">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="1.5" class="mx-auto mb-4 text-[hsl(var(--muted))]">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
        </svg>
        <p class="text-lg">暂无任务</p>
        <p class="text-sm mt-2">点击上方按钮创建新任务</p>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="task in tasks"
          :key="task.id"
          class="task-item p-4 rounded-lg border border-[hsl(var(--border))]
                 hover:bg-[hsl(var(--secondary))] transition-colors"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <h3 class="font-semibold text-[hsl(var(--foreground))] mb-1">
                {{ task.title }}
              </h3>
              <div class="flex items-center gap-4 text-sm text-[hsl(var(--muted-foreground))]">
                <span class="flex items-center gap-1">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                    stroke-width="2">
                    <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2z"></path>
                    <polyline points="12 6 12 12 16 14"></polyline>
                    <polyline points="12 18 12 18 12 18"></polyline>
                  </svg>
                  {{ formatDate(task.createdAt) }}
                </span>
                <span class="flex items-center gap-1">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                    stroke-width="2">
                    <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2z"></path>
                    <circle cx="12" cy="12" r="4"></circle>
                  </svg>
                  {{ formatDate(task.lastUpdated) }}
                </span>
              </div>
            </div>
            <div class="flex items-center gap-2 ml-4">
              <button
                @click="switchTask(task.id)"
                class="p-2 rounded-lg hover:bg-[hsl(var(--primary)/0.15)]
                       text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--primary))]
                       transition-colors"
                title="切换到此任务"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                </svg>
              </button>
              <button
                @click="deleteTask(task.id)"
                class="p-2 rounded-lg hover:bg-[hsl(var(--destructive)/0.15)]
                       text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--destructive))]
                       transition-colors"
                title="删除任务"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  stroke-width="2">
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAllTasks, createTask as dbCreateTask, deleteTask as dbDeleteTask, switchTask as dbSwitchTask } from '../lib/db.js'
import { inject } from 'vue'

const tasks = ref([])
const currentTaskId = inject('currentTask', ref(null))
const showNotification = inject('showNotification', null)

onMounted(async () => {
  await loadTasks()
})

async function loadTasks() {
  try {
    tasks.value = await getAllTasks()
  } catch (error) {
    console.error('加载任务列表失败:', error)
  }
}

async function createTask() {
  try {
    const taskId = await dbCreateTask('新任务')
    showNotification('success', '任务创建成功', '已创建新任务', 2000)
    await loadTasks()
    return taskId
  } catch (error) {
    console.error('创建任务失败:', error)
    showNotification('error', '创建失败', '无法创建新任务', 3000)
  }
}

async function deleteTask(taskId) {
  if (!confirm('确定要删除此任务吗？此操作不可恢复。')) {
    return
  }

  try {
    await dbDeleteTask(taskId)
    showNotification('success', '任务已删除', '任务已被删除', 2000)
    await loadTasks()
  } catch (error) {
    console.error('删除任务失败:', error)
    showNotification('error', '删除失败', '无法删除任务', 3000)
  }
}

async function switchTask(taskId) {
  try {
    await dbSwitchTask(taskId)
    currentTaskId.value = taskId
    showNotification('success', '任务切换成功', '已切换到指定任务', 2000)
  } catch (error) {
    console.error('切换任务失败:', error)
    showNotification('error', '切换失败', '无法切换任务', 3000)
  }
}

function formatDate(date) {
  if (!date) return '未知'
  const d = new Date(date)
  if (isNaN(d.getTime())) return '未知'
  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.task-panel {
  height: 100%;
}
</style>
