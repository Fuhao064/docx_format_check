<template>
  <div class="flex h-full">
    <!-- 主工作台区域 -->
    <main class="flex-1 flex flex-col overflow-hidden">
      <!-- 仪表板概览 -->
      <DashboardOverview v-if="activeTab === 'dashboard'" />

      <!-- 任务管理面板 -->
      <TaskPanel v-if="activeTab === 'tasks'" />

      <!-- 文件操作区 -->
      <FileOperationPanel v-if="activeTab === 'files'" />

      <!-- 原有主视图 -->
      <MainView v-if="activeTab === 'main'" />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import DashboardOverview from '../components/DashboardOverview.vue'
import TaskPanel from '../components/TaskPanel.vue'
import FileOperationPanel from '../components/FileOperationPanel.vue'
import MainView from './Main.vue'
import StatCard from '../components/StatCard.vue'
import { getCurrentTaskState, getAllTasks, getFormatErrors, getAllMessages } from '../lib/db.js'
import { inject, provide } from 'vue'

const activeTab = ref('dashboard')
const isDarkMode = inject('isDarkMode', ref(true))
const showNotification = inject('showNotification', null)

// 仪表板数据
const stats = ref({
  totalTasks: 0,
  completedTasks: 0,
  inProgressTasks: 0,
  totalFiles: 0,
  recentErrors: 0
})

const recentFiles = ref([])
const recentTasks = ref([])

onMounted(async () => {
  await loadDashboardData()
})

async function loadDashboardData() {
  try {
    // 加载任务统计
    const tasks = await getAllTasks()
    stats.value.totalTasks = tasks.length
    stats.value.completedTasks = tasks.filter(t => t.lastUpdated).length
    stats.value.inProgressTasks = tasks.filter(t => !t.lastUpdated).length

    if (tasks.length > 0) {
      recentTasks.value = tasks.slice(-5).reverse()
    }

    // 加载错误统计
    const errors = await getFormatErrors()
    stats.value.recentErrors = errors.length

    // 加载消息统计
    const messages = await getAllMessages()
    stats.value.totalFiles = messages.length
  } catch (error) {
    console.error('加载仪表板数据失败:', error)
  }
}

// 切换标签页
function switchTab(tab) {
  activeTab.value = tab
}

// 暴露给子组件使用
provide('activeTab', activeTab)
provide('switchTab', switchTab)
provide('stats', stats)
provide('recentFiles', recentFiles)
provide('recentTasks', recentTasks)
provide('loadDashboardData', loadDashboardData)
</script>

<style scoped>
.main-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: row;
}
</style>
