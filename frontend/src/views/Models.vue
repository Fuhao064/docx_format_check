<template>
  <div class="p-6 max-w-6xl mx-auto">
    <div class="mb-6">
      <h1 class="text-2xl font-semibold mb-2">模型管理</h1>
      <p class="text-zinc-400">管理和配置可用的AI模型</p>
    </div>
    
    <!-- 当前选择的模型 -->
    <div class="bg-zinc-800 rounded-lg p-4 mb-6">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-medium mb-1">当前选择的模型</h2>
          <p class="text-zinc-400">{{ currentModel || '未选择模型' }}</p>
        </div>
        <button 
          v-if="currentModel"
          @click="refreshModels"
          class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md transition-colors text-sm"
        >
          刷新
        </button>
      </div>
    </div>
    
    <!-- 模型列表 -->
    <div class="bg-zinc-900 rounded-lg overflow-hidden mb-6">
      <div class="overflow-x-auto">
        <table class="w-full border-collapse">
          <thead>
            <tr class="bg-zinc-800 text-left">
              <th class="px-6 py-3 text-zinc-300 font-medium">模型提供商</th>
              <th class="px-6 py-3 text-zinc-300 font-medium">模型名称</th>
              <th class="px-6 py-3 text-zinc-300 font-medium">API Key</th>
              <th class="px-6 py-3 text-zinc-300 font-medium">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-800">
            <tr v-for="(model, key) in models" :key="key" class="hover:bg-zinc-800/50 transition-colors">
              <td class="px-6 py-4">{{ getProviderName(key) }}</td>
              <td class="px-6 py-4">{{ model.model_name }}</td>
              <td class="px-6 py-4">
                <span class="font-mono text-sm">{{ maskApiKey(model.api_key) }}</span>
              </td>
              <td class="px-6 py-4">
                <div class="flex space-x-2">
                  <button 
                    @click="selectModel(key)"
                    class="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md transition-colors text-sm"
                  >
                    选择
                  </button>
                  <button 
                    @click="confirmDeleteModel(key)"
                    class="px-3 py-1 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-md transition-colors text-sm"
                  >
                    删除
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="Object.keys(models).length === 0">
              <td colspan="4" class="px-6 py-4 text-center text-zinc-500">
                暂无模型数据
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    
    <!-- 添加模型表单 -->
    <div class="bg-zinc-800 rounded-lg p-6">
      <h2 class="text-lg font-medium mb-4">添加新模型</h2>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <label class="block text-sm font-medium text-zinc-400 mb-1">模型名称</label>
          <input 
            v-model="newModel.name" 
            type="text" 
            class="w-full bg-zinc-700 text-zinc-100 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="例如: gpt-4"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-zinc-400 mb-1">API 基础 URL</label>
          <input 
            v-model="newModel.base_url" 
            type="text" 
            class="w-full bg-zinc-700 text-zinc-100 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="例如: https://api.openai.com"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-zinc-400 mb-1">API Key</label>
          <input 
            v-model="newModel.api_key" 
            type="text" 
            class="w-full bg-zinc-700 text-zinc-100 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="输入API密钥"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-zinc-400 mb-1">模型标识符</label>
          <input 
            v-model="newModel.model_name" 
            type="text" 
            class="w-full bg-zinc-700 text-zinc-100 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="例如: gpt-3.5-turbo"
          />
        </div>
      </div>
      
      <button 
        @click="addModel"
        class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md transition-colors"
        :disabled="isAddButtonDisabled"
        :class="{ 'opacity-50 cursor-not-allowed': isAddButtonDisabled }"
      >
        添加模型
      </button>
    </div>
    
    <!-- 确认删除对话框 -->
    <div v-if="showDeleteConfirm" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-zinc-900 rounded-lg p-6 max-w-md w-full mx-4">
        <h3 class="text-xl font-semibold mb-4">确认删除</h3>
        <p class="mb-6">确定要删除模型 "{{ modelToDelete }}" 吗？此操作无法撤销。</p>
        <div class="flex justify-end space-x-3">
          <button 
            @click="showDeleteConfirm = false"
            class="px-4 py-2 bg-zinc-700 hover:bg-zinc-600 text-white rounded-md transition-colors"
          >
            取消
          </button>
          <button 
            @click="deleteModel"
            class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
          >
            删除
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

// 模型数据
const models = ref({})
const currentModel = ref('')

// 新模型表单
const newModel = ref({
  name: '',
  base_url: '',
  api_key: '',
  model_name: ''
})

// 删除确认
const showDeleteConfirm = ref(false)
const modelToDelete = ref('')

// 计算属性：添加按钮是否禁用
const isAddButtonDisabled = computed(() => {
  return !newModel.value.name || 
         !newModel.value.base_url || 
         !newModel.value.api_key || 
         !newModel.value.model_name
})

// 获取模型提供商名称
function getProviderName(key) {
  const providerMap = {
    'openai': 'OpenAI',
    'deepseek': 'DeepSeek',
    'qwen': 'Qwen (阿里云)',
    'glm': 'GLM (智谱)',
    'deepseek-r1': 'DeepSeek R1'
  }
  
  for (const [provider, name] of Object.entries(providerMap)) {
    if (key.toLowerCase().includes(provider)) {
      return name
    }
  }
  
  return key
}

// 掩码API密钥
function maskApiKey(apiKey) {
  if (!apiKey) return '未设置'
  if (apiKey.length <= 8) return '****' + apiKey.slice(-4)
  return apiKey.slice(0, 4) + '****' + apiKey.slice(-4)
}

// 获取所有模型
async function fetchModels() {
  try {
    const response = await axios.get('/api/models')
    if (response.data.models) {
      // 获取完整的模型配置
      const keysResponse = await axios.get('/keys.json')
      models.value = keysResponse.data
    }
  } catch (error) {
    console.error('获取模型列表失败:', error)
    alert('获取模型列表失败: ' + error.message)
  }
}

// 选择模型
async function selectModel(modelName) {
  try {
    const response = await axios.post('/api/set-model', {
      model_name: modelName
    })
    
    if (response.data.message) {
      currentModel.value = modelName
      alert(response.data.message)
    }
  } catch (error) {
    console.error('设置模型失败:', error)
    alert('设置模型失败: ' + error.message)
  }
}

// 确认删除模型
function confirmDeleteModel(modelName) {
  modelToDelete.value = modelName
  showDeleteConfirm.value = true
}

// 删除模型
async function deleteModel() {
  try {
    const response = await axios.delete(`/api/delete-model/${modelToDelete.value}`)
    
    if (response.data.message) {
      // 如果删除的是当前选中的模型，清空当前模型
      if (currentModel.value === modelToDelete.value) {
        currentModel.value = ''
      }
      
      // 重新获取模型列表
      await fetchModels()
      
      // 关闭确认对话框
      showDeleteConfirm.value = false
      modelToDelete.value = ''
      
      alert(response.data.message)
    }
  } catch (error) {
    console.error('删除模型失败:', error)
    alert('删除模型失败: ' + error.message)
    showDeleteConfirm.value = false
  }
}

// 添加模型
async function addModel() {
  if (isAddButtonDisabled.value) return
  
  try {
    const response = await axios.post('/api/add-model', {
      name: newModel.value.name,
      base_url: newModel.value.base_url,
      api_key: newModel.value.api_key,
      model_name: newModel.value.model_name
    })
    
    if (response.data.message) {
      // 重置表单
      newModel.value = {
        name: '',
        base_url: '',
        api_key: '',
        model_name: ''
      }
      
      // 重新获取模型列表
      await fetchModels()
      
      alert(response.data.message)
    }
  } catch (error) {
    console.error('添加模型失败:', error)
    alert('添加模型失败: ' + error.message)
  }
}

// 刷新模型列表
function refreshModels() {
  fetchModels()
}

// 组件挂载时获取模型列表
onMounted(() => {
  fetchModels()
})
</script>