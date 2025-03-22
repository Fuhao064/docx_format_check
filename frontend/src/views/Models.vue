<template>
  <div class="p-6 overflow-y-auto h-full transition-colors duration-[--transition-speed]"
       :class="isDarkMode ? 'bg-[hsl(var(--background))] text-[hsl(var(--foreground))]' : 'bg-[hsl(var(--background))] text-[hsl(var(--foreground))]'">
    <div class="mb-6">
      <h1 class="text-2xl font-semibold mb-2 text-[hsl(var(--foreground))]">模型管理</h1>
      <p class="text-[hsl(var(--muted-foreground))]">管理和配置可用的AI模型</p>
    </div>
    

    <!-- 各代理模型配置 -->
    <div :class="[isDarkMode ? 'bg-[hsl(var(--card))]' : 'bg-[hsl(var(--card))]', 'rounded-md p-4 mb-6']">
      <h2 class="text-lg font-medium mb-3 text-[hsl(var(--foreground))]">代理模型配置</h2>
      <div class="grid grid-cols-1 gap-4">
        <!-- 格式代理 -->
        <div class="p-3 border border-[hsl(var(--border))] rounded-md">
          <h3 class="font-medium mb-2 text-[hsl(var(--foreground))]">格式代理 (Format Agent)</h3>
          <div class="flex items-center justify-between">
            <select 
              v-model="agentModels.format" 
              class="bg-[hsl(var(--input))] text-[hsl(var(--foreground))] rounded-md px-3 py-2 border border-[hsl(var(--border))] focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))]"
            >
              <option value="">请选择模型</option>
              <option v-for="(model, key) in models" :key="`format-${key}`" :value="key">
                {{ key }} ({{ model.model_name }})
              </option>
            </select>
            <button 
              @click="updateAgentModel('format', agentModels.format)"
              :disabled="!agentModels.format"
              :class="[
                'bg-[hsl(var(--primary))] hover:bg-[hsl(var(--primary)/0.9)] text-[hsl(var(--primary-foreground))]',
                'px-3 py-1.5 rounded-md transition-colors duration-[--transition-speed] text-sm ml-2',
                !agentModels.format ? 'opacity-50 cursor-not-allowed' : ''
              ]"
            >
              应用
            </button>
          </div>
        </div>

        <!-- 编辑代理 -->
        <div class="p-3 border border-[hsl(var(--border))] rounded-md">
          <h3 class="font-medium mb-2 text-[hsl(var(--foreground))]">编辑代理 (Editor Agent)</h3>
          <div class="flex items-center justify-between">
            <select 
              v-model="agentModels.editor" 
              class="bg-[hsl(var(--input))] text-[hsl(var(--foreground))] rounded-md px-3 py-2 border border-[hsl(var(--border))] focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))]"
            >
              <option value="">请选择模型</option>
              <option v-for="(model, key) in models" :key="`editor-${key}`" :value="key">
                {{ key }} ({{ model.model_name }})
              </option>
            </select>
            <button 
              @click="updateAgentModel('editor', agentModels.editor)"
              :disabled="!agentModels.editor"
              :class="[
                'bg-[hsl(var(--primary))] hover:bg-[hsl(var(--primary)/0.9)] text-[hsl(var(--primary-foreground))]',
                'px-3 py-1.5 rounded-md transition-colors duration-[--transition-speed] text-sm ml-2',
                !agentModels.editor ? 'opacity-50 cursor-not-allowed' : ''
              ]"
            >
              应用
            </button>
          </div>
        </div>

        <!-- 建议代理 -->
        <div class="p-3 border border-[hsl(var(--border))] rounded-md">
          <h3 class="font-medium mb-2 text-[hsl(var(--foreground))]">建议代理 (Advice Agent)</h3>
          <div class="flex items-center justify-between">
            <select 
              v-model="agentModels.advice" 
              class="bg-[hsl(var(--input))] text-[hsl(var(--foreground))] rounded-md px-3 py-2 border border-[hsl(var(--border))] focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))]"
            >
              <option value="">请选择模型</option>
              <option v-for="(model, key) in models" :key="`advice-${key}`" :value="key">
                {{ key }} ({{ model.model_name }})
              </option>
            </select>
            <button 
              @click="updateAgentModel('advice', agentModels.advice)"
              :disabled="!agentModels.advice"
              :class="[
                'bg-[hsl(var(--primary))] hover:bg-[hsl(var(--primary)/0.9)] text-[hsl(var(--primary-foreground))]',
                'px-3 py-1.5 rounded-md transition-colors duration-[--transition-speed] text-sm ml-2',
                !agentModels.advice ? 'opacity-50 cursor-not-allowed' : ''
              ]"
            >
              应用
            </button>
          </div>
        </div>

        <!-- 通信代理 -->
        <div class="p-3 border border-[hsl(var(--border))] rounded-md">
          <h3 class="font-medium mb-2 text-[hsl(var(--foreground))]">通信代理 (Communicate Agent)</h3>
          <div class="flex items-center justify-between">
            <select 
              v-model="agentModels.communicate" 
              class="bg-[hsl(var(--input))] text-[hsl(var(--foreground))] rounded-md px-3 py-2 border border-[hsl(var(--border))] focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))]"
            >
              <option value="">请选择模型</option>
              <option v-for="(model, key) in models" :key="`communicate-${key}`" :value="key">
                {{ key }} ({{ model.model_name }})
              </option>
            </select>
            <button 
              @click="updateAgentModel('communicate', agentModels.communicate)"
              :disabled="!agentModels.communicate"
              :class="[
                'bg-[hsl(var(--primary))] hover:bg-[hsl(var(--primary)/0.9)] text-[hsl(var(--primary-foreground))]',
                'px-3 py-1.5 rounded-md transition-colors duration-[--transition-speed] text-sm ml-2',
                !agentModels.communicate ? 'opacity-50 cursor-not-allowed' : ''
              ]"
            >
              应用
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 模型列表 -->
    <div :class="[isDarkMode ? 'bg-[hsl(var(--card))]' : 'bg-[hsl(var(--card))]', 'rounded-md overflow-hidden mb-6 border border-[hsl(var(--border))]']">
      <div class="overflow-x-auto">
        <table class="w-full border-collapse">
          <thead>
            <tr :class="isDarkMode ? 'bg-[hsl(var(--secondary))]' : 'bg-[hsl(var(--secondary))]'">
              <th :class="['text-[hsl(var(--secondary-foreground))]', 'px-6 py-3 text-left font-medium']">模型提供商</th>
              <th :class="['text-[hsl(var(--secondary-foreground))]', 'px-6 py-3 text-left font-medium']">模型名称</th>
              <th :class="['text-[hsl(var(--secondary-foreground))]', 'px-6 py-3 text-left font-medium']">API Key</th>
              <th :class="['text-[hsl(var(--secondary-foreground))]', 'px-6 py-3 text-left font-medium']">操作</th>
            </tr>
          </thead>
          <tbody :class="isDarkMode ? 'divide-y divide-[hsl(var(--border))]' : 'divide-y divide-[hsl(var(--border))]'">
            <tr v-for="(model, key) in models" :key="key" :class="isDarkMode ? 'hover:bg-[hsl(var(--secondary))/0.5]' : 'hover:bg-[hsl(var(--secondary))/0.5]'">
              <td class="px-6 py-4 text-[hsl(var(--foreground))]">{{ getProviderName(key) }}</td>
              <td class="px-6 py-4 text-[hsl(var(--foreground))]">{{ model.model_name }}</td>
              <td class="px-6 py-4">
                <span class="font-mono text-sm text-[hsl(var(--foreground))]">{{ maskApiKey(model.api_key) }}</span>
              </td>
              <td class="px-6 py-4">
                <div class="flex space-x-2">
                  <button
                    @click="confirmDeleteModel(key)"
                    :class="[
                      'bg-[hsl(var(--destructive)/0.2)] hover:bg-[hsl(var(--destructive)/0.3)] text-[hsl(var(--destructive))]',
                      'px-3 py-1 rounded-md transition-colors duration-[--transition-speed] text-sm'
                    ]"
                  >
                    删除
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="Object.keys(models).length === 0">
              <td colspan="4" :class="['text-[hsl(var(--muted-foreground))]', 'px-6 py-4 text-center']">
                暂无模型数据
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 添加模型表单 -->
    <div :class="[isDarkMode ? 'bg-[hsl(var(--card))]' : 'bg-[hsl(var(--card))]', 'rounded-md p-6']">
      <h2 class="text-lg font-medium mb-4 text-[hsl(var(--foreground))]">添加新模型</h2>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <label :class="['text-[hsl(var(--muted-foreground))]', 'block text-sm font-medium mb-1']">模型名称</label>
          <input
            v-model="newModel.name"
            type="text"
            :class="[
              'bg-[hsl(var(--input))] text-[hsl(var(--foreground))]',
              'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))]'
            ]"
            placeholder="例如: gpt-4"
          />
        </div>

        <div>
          <label :class="['text-[hsl(var(--muted-foreground))]', 'block text-sm font-medium mb-1']">API 基础 URL</label>
          <input
            v-model="newModel.base_url"
            type="text"
            :class="[
              'bg-[hsl(var(--input))] text-[hsl(var(--foreground))]',
              'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))]'
            ]"
            placeholder="例如: https://api.openai.com"
          />
        </div>

        <div>
          <label :class="['text-[hsl(var(--muted-foreground))]', 'block text-sm font-medium mb-1']">API Key</label>
          <input
            v-model="newModel.api_key"
            type="text"
            :class="[
             'bg-[hsl(var(--input))] text-[hsl(var(--foreground))]',
              'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))]'
            ]"
            placeholder="输入API密钥"
          />
        </div>

        <div>
          <label :class="['text-[hsl(var(--muted-foreground))]', 'block text-sm font-medium mb-1']">模型标识符</label>
          <input
            v-model="newModel.model_name"
            type="text"
            :class="[
              'bg-[hsl(var(--input))] text-[hsl(var(--foreground))]',
              'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))]'
            ]"
            placeholder="例如: gpt-3.5-turbo"
          />
        </div>
      </div>

      <button
        @click="addModel"
        :class="[
          'bg-[hsl(var(--primary))] hover:bg-[hsl(var(--primary)/0.9)] text-[hsl(var(--primary-foreground))]',
          'px-4 py-2 rounded-md transition-colors duration-[--transition-speed]',
          isAddButtonDisabled ? 'opacity-50 cursor-not-allowed' : ''
        ]"
        :disabled="isAddButtonDisabled"
      >
        添加模型
      </button>
    </div>

    <!-- 确认删除对话框 -->
    <div v-if="showDeleteConfirm" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div :class="[isDarkMode ? 'bg-[hsl(var(--card))]' : 'bg-[hsl(var(--card))]', 'rounded-md p-6 max-w-md w-full mx-4']">
        <h3 class="text-xl font-semibold mb-4 text-[hsl(var(--foreground))]">确认删除</h3>
        <p class="mb-6 text-[hsl(var(--muted-foreground))]">确定要删除模型 "{{ modelToDelete }}" 吗？此操作无法撤销。</p>
        <div class="flex justify-end space-x-3">
          <button
            @click="showDeleteConfirm = false"
            :class="[
              'bg-[hsl(var(--secondary))] hover:bg-[hsl(var(--secondary)/0.9)] text-[hsl(var(--secondary-foreground))]',
              'px-4 py-2 rounded-md transition-colors duration-[--transition-speed]'
            ]"
          >
            取消
          </button>
          <button
            @click="deleteModel"
            :class="[
              'bg-[hsl(var(--destructive))] hover:bg-[hsl(var(--destructive)/0.9)] text-[hsl(var(--destructive-foreground))]',
              'px-4 py-2 rounded-md transition-colors duration-[--transition-speed]'
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

// 代理模型配置
const agentModels = ref({
  format: '',
  editor: '',
  advice: '',
  communicate: ''
})

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
  // 根据keys.json中的数据结构解析提供商名称
  const providerMap = {
    'openai': 'OpenAI',
    'deepseek': 'DeepSeek',
    'qwen': 'Qwen (阿里云)',
    'glm': 'GLM (智谱)',
    'gemini': 'Gemini (Google)',
    'deepseek-r1': 'DeepSeek R1'
  }

  // 尝试从key中提取提供商名称
  for (const [provider, name] of Object.entries(providerMap)) {
    if (key.toLowerCase().includes(provider)) {
      return name
    }
  }

  // 如果没有匹配到任何已知提供商，返回原始key
  return key
}

// 掩码API密钥
function maskApiKey(apiKey) {
  if (!apiKey) return ''
  if (apiKey.length <= 8) return '*'.repeat(apiKey.length)
  return apiKey.slice(0, 4) + '*'.repeat(apiKey.length - 8) + apiKey.slice(-4)
}

// 获取所有模型和当前配置
async function fetchModels() {
  try {
    // 获取模型列表
    const modelsResponse = await axios.get('/api/models')
    models.value = modelsResponse.data.models || {}
    
    // 获取所有代理的当前模型配置
    try {
      const agentConfigResponse = await axios.get('/api/agent-models')
      const config = agentConfigResponse.data
      
      // 更新本地配置
      if (config.format_model) agentModels.value.format = config.format_model
      if (config.editor_model) agentModels.value.editor = config.editor_model
      if (config.advice_model) agentModels.value.advice = config.advice_model
      if (config.communicate_model) agentModels.value.communicate = config.communicate_model
    } catch (err) {
      console.error('获取代理模型配置失败:', err)
    }
  } catch (error) {
    console.error('获取模型列表失败:', error)
    showNotification('error', '获取失败', '无法获取模型列表，请稍后重试')
  }
}

// 选择默认模型
async function selectModel(modelName) {
  try {
    await axios.post('/api/set-model', { model_name: modelName })
    currentModel.value = modelName
    showNotification('success', '选择成功', `已选择默认模型: ${modelName}`)
  } catch (error) {
    console.error('选择模型失败:', error)
    showNotification('error', '选择失败', '无法选择该模型，请稍后重试')
  }
}

// 更新代理模型
async function updateAgentModel(agentType, modelName) {
  if (!modelName) return
  
  try {
    await axios.post('/api/set-agent-model', { 
      agent_type: agentType,
      model_name: modelName
    })
    showNotification('success', '更新成功', `已将${getAgentDisplayName(agentType)}模型设置为: ${modelName}`)
  } catch (error) {
    console.error('更新代理模型失败:', error)
    showNotification('error', '更新失败', '无法更新代理模型，请稍后重试')
  }
}

// 获取代理显示名称
function getAgentDisplayName(agentType) {
  const agentNames = {
    format: '格式代理',
    editor: '编辑代理',
    advice: '建议代理',
    communicate: '通信代理'
  }
  return agentNames[agentType] || agentType
}

// 确认删除模型
function confirmDeleteModel(modelName) {
  modelToDelete.value = modelName
  showDeleteConfirm.value = true
}

// 删除模型
async function deleteModel() {
  try {
    await axios.delete(`/api/delete-model/${modelToDelete.value}`)
    if (currentModel.value === modelToDelete.value) {
      currentModel.value = ''
    }
    delete models.value[modelToDelete.value]
    showDeleteConfirm.value = false
    showNotification('success', '删除成功', `已删除模型: ${modelToDelete.value}`)
    
    // 删除后检查所有代理的模型设置并重置已被删除的模型
    Object.keys(agentModels.value).forEach(agentType => {
      if (agentModels.value[agentType] === modelToDelete.value) {
        agentModels.value[agentType] = ''
      }
    })
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