<template>
  <div class="p-6 overflow-y-auto h-full" :class="{ 'bg-white text-black': !isDarkMode, 'bg-zinc-950 text-zinc-100': isDarkMode }">
    <div class="mb-6">
      <h1 class="text-2xl font-semibold mb-2">模型管理</h1>
      <p :class="isDarkMode ? 'text-zinc-400' : 'text-gray-600'">管理和配置可用的AI模型</p>
    </div>
    
    <!-- 当前选择的模型 -->
    <div :class="[isDarkMode ? 'bg-zinc-800' : 'bg-gray-100', 'rounded-md p-4 mb-6']">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-medium mb-1">当前选择的模型</h2>
          <p :class="isDarkMode ? 'text-zinc-400' : 'text-gray-600'">{{ currentModel || '未选择模型' }}</p>
        </div>
        <button 
          v-if="currentModel"
          @click="refreshModels"
          :class="[
            isDarkMode ? 'bg-zinc-700 hover:bg-zinc-600 text-zinc-300' : 'bg-gray-200 hover:bg-gray-300 text-gray-700',
            'px-3 py-1.5 rounded-md transition-colors text-sm'
          ]"
        >
          刷新
        </button>
      </div>
    </div>
    
    <!-- 模型列表 -->
    <div :class="[isDarkMode ? 'bg-zinc-900' : 'bg-white border border-gray-200', 'rounded-md overflow-hidden mb-6']">
      <div class="overflow-x-auto">
        <table class="w-full border-collapse">
          <thead>
            <tr :class="isDarkMode ? 'bg-zinc-800' : 'bg-gray-50'">
              <th :class="[isDarkMode ? 'text-zinc-300' : 'text-gray-700', 'px-6 py-3 text-left font-medium']">模型提供商</th>
              <th :class="[isDarkMode ? 'text-zinc-300' : 'text-gray-700', 'px-6 py-3 text-left font-medium']">模型名称</th>
              <th :class="[isDarkMode ? 'text-zinc-300' : 'text-gray-700', 'px-6 py-3 text-left font-medium']">API Key</th>
              <th :class="[isDarkMode ? 'text-zinc-300' : 'text-gray-700', 'px-6 py-3 text-left font-medium']">操作</th>
            </tr>
          </thead>
          <tbody :class="isDarkMode ? 'divide-y divide-zinc-800' : 'divide-y divide-gray-200'">
            <tr v-for="(model, key) in models" :key="key" :class="isDarkMode ? 'hover:bg-zinc-800/50' : 'hover:bg-gray-50'">
              <td class="px-6 py-4">{{ getProviderName(key) }}</td>
              <td class="px-6 py-4">{{ model.model_name }}</td>
              <td class="px-6 py-4">
                <span class="font-mono text-sm">{{ maskApiKey(model.api_key) }}</span>
              </td>
              <td class="px-6 py-4">
                <div class="flex space-x-2">
                  <button 
                    @click="selectModel(key)"
                    :class="[
                      isDarkMode ? 'bg-zinc-700 hover:bg-zinc-600 text-zinc-300' : 'bg-gray-200 hover:bg-gray-300 text-gray-700',
                      'px-3 py-1 rounded-md transition-colors text-sm'
                    ]"
                  >
                    选择
                  </button>
                  <button 
                    @click="confirmDeleteModel(key)"
                    :class="[
                      isDarkMode ? 'bg-red-600/20 hover:bg-red-600/30 text-red-400' : 'bg-red-100 hover:bg-red-200 text-red-600',
                      'px-3 py-1 rounded-md transition-colors text-sm'
                    ]"
                  >
                    删除
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="Object.keys(models).length === 0">
              <td colspan="4" :class="[isDarkMode ? 'text-zinc-500' : 'text-gray-500', 'px-6 py-4 text-center']">
                暂无模型数据
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    
    <!-- 添加模型表单 -->
    <div :class="[isDarkMode ? 'bg-zinc-800' : 'bg-gray-100', 'rounded-md p-6']">
      <h2 class="text-lg font-medium mb-4">添加新模型</h2>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <label :class="[isDarkMode ? 'text-zinc-400' : 'text-gray-600', 'block text-sm font-medium mb-1']">模型名称</label>
          <input 
            v-model="newModel.name" 
            type="text" 
            :class="[
              isDarkMode ? 'bg-zinc-700 text-zinc-100' : 'bg-white text-gray-900 border border-gray-300',
              'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-1',
              isDarkMode ? 'focus:ring-zinc-600' : 'focus:ring-blue-500'
            ]"
            placeholder="例如: gpt-4"
          />
        </div>
        
        <div>
          <label :class="[isDarkMode ? 'text-zinc-400' : 'text-gray-600', 'block text-sm font-medium mb-1']">API 基础 URL</label>
          <input 
            v-model="newModel.base_url" 
            type="text" 
            :class="[
              isDarkMode ? 'bg-zinc-700 text-zinc-100' : 'bg-white text-gray-900 border border-gray-300',
              'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-1',
              isDarkMode ? 'focus:ring-zinc-600' : 'focus:ring-blue-500'
            ]"
            placeholder="例如: https://api.openai.com"
          />
        </div>
        
        <div>
          <label :class="[isDarkMode ? 'text-zinc-400' : 'text-gray-600', 'block text-sm font-medium mb-1']">API Key</label>
          <input 
            v-model="newModel.api_key" 
            type="text" 
            :class="[
              isDarkMode ? 'bg-zinc-700 text-zinc-100' : 'bg-white text-gray-900 border border-gray-300',
              'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-1',
              isDarkMode ? 'focus:ring-zinc-600' : 'focus:ring-blue-500'
            ]"
            placeholder="输入API密钥"
          />
        </div>
        
        <div>
          <label :class="[isDarkMode ? 'text-zinc-400' : 'text-gray-600', 'block text-sm font-medium mb-1']">模型标识符</label>
          <input 
            v-model="newModel.model_name" 
            type="text" 
            :class="[
              isDarkMode ? 'bg-zinc-700 text-zinc-100' : 'bg-white text-gray-900 border border-gray-300',
              'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-1',
              isDarkMode ? 'focus:ring-zinc-600' : 'focus:ring-blue-500'
            ]"
            placeholder="例如: gpt-3.5-turbo"
          />
        </div>
      </div>
      
      <button 
        @click="addModel"
        :class="[
          isDarkMode ? 'bg-zinc-700 hover:bg-zinc-600 text-zinc-300' : 'bg-blue-500 hover:bg-blue-600 text-white',
          'px-4 py-2 rounded-md transition-colors',
          isAddButtonDisabled ? 'opacity-50 cursor-not-allowed' : ''
        ]"
        :disabled="isAddButtonDisabled"
      >
        添加模型
      </button>
    </div>
    
    <!-- 确认删除对话框 -->
    <div v-if="showDeleteConfirm" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div :class="[isDarkMode ? 'bg-zinc-900' : 'bg-white', 'rounded-md p-6 max-w-md w-full mx-4']">
        <h3 class="text-xl font-semibold mb-4">确认删除</h3>
        <p class="mb-6" :class="isDarkMode ? 'text-zinc-400' : 'text-gray-600'">确定要删除模型 "{{ modelToDelete }}" 吗？此操作无法撤销。</p>
        <div class="flex justify-end space-x-3">
          <button 
            @click="showDeleteConfirm = false"
            :class="[
              isDarkMode ? 'bg-zinc-700 hover:bg-zinc-600 text-zinc-300' : 'bg-gray-200 hover:bg-gray-300 text-gray-700',
              'px-4 py-2 rounded-md transition-colors'
            ]"
          >
            取消
          </button>
          <button 
            @click="deleteModel"
            :class="[
              isDarkMode ? 'bg-red-600/80 hover:bg-red-600 text-white' : 'bg-red-500 hover:bg-red-600 text-white',
              'px-4 py-2 rounded-md transition-colors'
            ]"
          >
            删除
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
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

// 获取通知函数和主题模式
const showNotification = inject('showNotification', null)
const isDarkMode = inject('isDarkMode', ref(true))

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
  if (!apiKey) return ''
  if (apiKey.length <= 8) return '*'.repeat(apiKey.length)
  return apiKey.slice(0, 4) + '*'.repeat(apiKey.length - 8) + apiKey.slice(-4)
}

// 获取所有模型
async function fetchModels() {
  try {
    // 获取模型列表
    const modelsResponse = await axios.get('/api/models')
    models.value = modelsResponse.data.models || {}
    
    // 获取当前选中的模型
    try {
      const currentModelResponse = await axios.get('/api/current-model')
      currentModel.value = currentModelResponse.data.current_model || ''
    } catch (err) {
      console.error('获取当前模型失败:', err)
      // 如果无法获取当前模型，不阻止页面显示
    }
  } catch (error) {
    console.error('获取模型列表失败:', error)
    showNotification('error', '获取失败', '无法获取模型列表，请稍后重试')
  }
}

// 选择模型
async function selectModel(modelName) {
  try {
    await axios.post('/api/set-model', { model_name: modelName })
    currentModel.value = modelName
    showNotification('success', '选择成功', `已选择模型: ${modelName}`)
  } catch (error) {
    console.error('选择模型失败:', error)
    showNotification('error', '选择失败', '无法选择该模型，请稍后重试')
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
    await axios.delete(`/api/models/${modelToDelete.value}`)
    if (currentModel.value === modelToDelete.value) {
      currentModel.value = ''
    }
    delete models.value[modelToDelete.value]
    showDeleteConfirm.value = false
    showNotification('success', '删除成功', `已删除模型: ${modelToDelete.value}`)
  } catch (error) {
    console.error('删除模型失败:', error)
    showNotification('error', '删除失败', '无法删除该模型，请稍后重试')
  }
}

// 添加模型
async function addModel() {
  if (isAddButtonDisabled.value) return
  
  try {
    const modelData = {
      name: newModel.value.name,
      base_url: newModel.value.base_url,
      api_key: newModel.value.api_key,
      model_name: newModel.value.model_name
    }
    
    await axios.post('/api/models', modelData)
    
    // 重置表单
    newModel.value = {
      name: '',
      base_url: '',
      api_key: '',
      model_name: ''
    }
    
    // 刷新模型列表
    await fetchModels()
    showNotification('success', '添加成功', `已添加新模型: ${modelData.name}`)
  } catch (error) {
    console.error('添加模型失败:', error)
    showNotification('error', '添加失败', '无法添加新模型，请检查输入信息是否正确')
  }
}

// 刷新模型列表
async function refreshModels() {
  await fetchModels()
}

// 组件挂载时获取模型列表
onMounted(() => {
  fetchModels()
})
</script>
