<template>
  <div class="bg-gray-800 p-4 rounded-lg">
    <!-- 模型选择 -->
    <div class="mb-4">
      <label class="block text-sm font-medium text-gray-300 mb-2">选择模型</label>
      <select
        v-model="selectedModel"
        @change="handleModelChange"
        class="w-full bg-gray-700 text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option v-for="model in models" :key="model.name" :value="model.name">
          {{ model.name }}
        </option>
      </select>
    </div>

    <!-- 模型管理按钮 -->
    <div class="flex justify-end mb-4">
      <button
        @click="showAddModal = true"
        class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md transition-colors mr-2"
      >
        添加模型
      </button>
      <button
        v-if="selectedModel"
        @click="deleteModel"
        class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md transition-colors"
      >
        删除模型
      </button>
    </div>

    <!-- 添加模型弹窗 -->
    <div v-if="showAddModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div class="bg-gray-800 p-6 rounded-lg w-96">
        <h3 class="text-lg font-medium text-white mb-4">添加新模型</h3>
        <form @submit.prevent="addModel" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-2">模型名称</label>
            <input
              v-model="newModel.name"
              type="text"
              required
              class="w-full bg-gray-700 text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-2">Base URL</label>
            <input
              v-model="newModel.base_url"
              type="text"
              required
              class="w-full bg-gray-700 text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-2">API Key</label>
            <input
              v-model="newModel.api_key"
              type="password"
              required
              class="w-full bg-gray-700 text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-2">模型名称参数</label>
            <input
              v-model="newModel.model_name"
              type="text"
              required
              class="w-full bg-gray-700 text-white rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
          </div>
          <div class="flex justify-end space-x-2">
            <button
              type="button"
              @click="showAddModal = false"
              class="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md transition-colors"
            >
              添加
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const models = ref([])
const selectedModel = ref('')
const showAddModal = ref(false)
const newModel = ref({
  name: '',
  base_url: '',
  api_key: '',
  model_name: ''
})

// 获取所有可用模型
const fetchModels = async () => {
  try {
    const response = await axios.get('/api/models')
    models.value = response.data.models
    if (models.value.length > 0 && !selectedModel.value) {
      selectedModel.value = models.value[0].name
    }
  } catch (error) {
    console.error('获取模型列表失败:', error)
  }
}

// 切换选中的模型
const handleModelChange = async () => {
  try {
    await axios.post('/api/set-model', { model_name: selectedModel.value })
  } catch (error) {
    console.error('切换模型失败:', error)
  }
}

// 添加新模型
const addModel = async () => {
  try {
    await axios.post('/api/add-model', newModel.value)
    showAddModal.value = false
    newModel.value = { name: '', base_url: '', api_key: '', model_name: '' }
    await fetchModels()
  } catch (error) {
    console.error('添加模型失败:', error)
  }
}

// 删除模型
const deleteModel = async () => {
  if (!selectedModel.value) return
  
  if (confirm(`确定要删除模型 ${selectedModel.value} 吗？`)) {
    try {
      await axios.delete(`/api/delete-model/${selectedModel.value}`)
      await fetchModels()
    } catch (error) {
      console.error('删除模型失败:', error)
    }
  }
}

onMounted(() => {
  fetchModels()
})
</script>