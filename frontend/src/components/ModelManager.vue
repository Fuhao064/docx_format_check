<template>
  <div class="bg-gray-800 p-4 rounded-lg">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-medium text-white">模型管理</h2>
      <Button @click="showAddModal = true">
        添加模型
      </Button>
    </div>

    <DataTable
      :columns="columns"
      :data="models"
    />

    <Dialog
      :open="showAddModal"
      @close="showAddModal = false"
      class="fixed inset-0 z-50 overflow-y-auto"
    >
      <div class="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        <DialogOverlay class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />

        <div class="inline-block align-bottom bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-align-top sm:align-middle sm:max-w-lg sm:w-full">
          <div class="p-6">
            <DialogTitle class="text-lg font-medium text-white mb-4">添加新模型</DialogTitle>
            <form @submit.prevent="addModel" class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">模型名称</label>
                <Input
                  v-model="newModel.name"
                  required
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Base URL</label>
                <Input
                  v-model="newModel.base_url"
                  required
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">API Key</label>
                <Input
                  v-model="newModel.api_key"
                  type="password"
                  required
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">模型名称参数</label>
                <Input
                  v-model="newModel.model_name"
                  required
                />
              </div>
              <div class="flex justify-end space-x-2">
                <Button
                  variant="secondary"
                  @click="showAddModal = false"
                >
                  取消
                </Button>
                <Button type="submit">
                  添加
                </Button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { Dialog, DialogOverlay, DialogTitle } from '@headlessui/vue'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { DataTable } from './ui/data-table'
import { columns } from './ui/data-table/columns'

const models = ref([])
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
  } catch (error) {
    console.error('获取模型列表失败:', error)
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
const deleteModel = async (modelName) => {
  if (confirm(`确定要删除模型 ${modelName} 吗？`)) {
    try {
      await axios.delete(`/api/delete-model/${modelName}`)
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
