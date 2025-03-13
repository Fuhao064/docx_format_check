<template>
  <div class="p-6 ">
    <div class="mb-6">
      <h1 class="text-2xl font-semibold mb-2">格式配置</h1>
      <p class="text-zinc-400">管理文档格式规范和样式配置</p>
    </div>
    
    <!-- 配置编辑器 -->
    <div class="bg-zinc-800 rounded-lg p-6 mb-6">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-lg font-medium">配置编辑器</h2>
        <div class="flex space-x-3">
          <button 
            @click="loadExampleConfig"
            class="px-3 py-1.5 bg-zinc-700 hover:bg-zinc-600 text-white rounded-md transition-colors text-sm"
          >
            加载示例配置
          </button>
          <button 
            @click="saveConfig"
            class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md transition-colors text-sm"
            :disabled="!configData"
          >
            保存配置
          </button>
        </div>
      </div>
      
      <div v-if="loading" class="flex items-center justify-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500"></div>
      </div>
      
      <div v-else-if="configData" class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- 纸张设置 -->
        <div class="bg-zinc-900 rounded-lg p-4">
          <h3 class="text-md font-medium mb-3 border-b border-zinc-700 pb-2">纸张设置</h3>
          
          <div class="space-y-3">
            <div>
              <label class="block text-sm font-medium text-zinc-400 mb-1">纸张大小</label>
              <select 
                v-model="configData.paper.size"
                class="w-full bg-zinc-800 text-zinc-100 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="A4">A4</option>
                <option value="Letter">Letter</option>
                <option value="Legal">Legal</option>
              </select>
            </div>
            
            <div>
              <label class="block text-sm font-medium text-zinc-400 mb-1">纸张方向</label>
              <select 
                v-model="configData.paper.orientation"
                class="w-full bg-zinc-800 text-zinc-100 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="portrait">纵向</option>
                <option value="landscape">横向</option>
              </select>
            </div>
            
            <div>
              <label class="block text-sm font-medium text-zinc-400 mb-1">页边距</label>
              <div class="grid grid-cols-2 gap-2">
                <div>
                  <label class="block text-xs text-zinc-500 mb-1">上</label>
                  <input 
                    v-model="configData.paper.margins.top"
                    type="text" 
                    class="w-full bg-zinc-800 text-zinc-100 rounded-md px-3 py-1 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label class="block text-xs text-zinc-500 mb-1">下</label>
                  <input 
                    v-model="configData.paper.margins.bottom"
                    type="text" 
                    class="w-full bg-zinc-800 text-zinc-100 rounded-md px-3 py-1 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label class="block text-xs text-zinc-500 mb-1">左</label>
                  <input 
                    v-model="configData.paper.margins.left"
                    type="text" 
                    class="w-full bg-zinc-800 text-zinc-100 rounded-md px-3 py-1 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label class="block text-xs text-zinc-500 mb-1">右</label>
                  <input 
                    v-model="configData.paper.margins.right"
                    type="text" 
                    class="w-full bg-zinc-800 text-zinc-100 rounded-md px-3 py-1 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 标题设置 -->
        <div class="bg-zinc-900 rounded-lg p-4">
          <h3 class="text-md font-medium mb-3 border-b border-zinc-700 pb-2">标题设置</h3>
          
          <div class="space-y-3">
            <div>
              <label class="block text-sm font-medium text-zinc-400 mb-1">中文字体</label>
              <input 
                v-model="configData.title_zh.fonts.zh_family"
                type="text" 
                class="w-full bg-zinc-800 text-zinc-100 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-zinc-400 mb-1">英文字体</label>
              <input 
                v-model="configData.title_zh.fonts.en_family"
                type="text" 
                class="w-full bg-zinc-800 text-zinc-100 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-zinc-400 mb-1">字体大小</label>
              <input 
                v-model="configData.title_zh.fonts.size"
                type="text" 
                class="w-full bg-zinc-800 text-zinc-100 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            
            <div class="flex space-x-4">
              <div class="flex items-center">
                <input 
                  v-model="configData.title_zh.fonts.bold"
                  type="checkbox" 
                  id="title-bold"
                  class="w-4 h-4 bg-zinc-800 rounded focus:ring-indigo-500 text-indigo-600 border-zinc-600"
                />
                <label for="title-bold" class="ml-2 text-sm text-zinc-400">粗体</label>
              </div>
              
              <div class="flex items-center">
                <input 
                  v-model="configData.title_zh.fonts.italic"
                  type="checkbox" 
                  id="title-italic"
                  class="w-4 h-4 bg-zinc-800 rounded focus:ring-indigo-500 text-indigo-600 border-zinc-600"
                />
                <label for="title-italic" class="ml-2 text-sm text-zinc-400">斜体</label>
              </div>
              
              <div class="flex items-center">
                <input 
                  v-model="configData.title_zh.fonts.isAllCaps"
                  type="checkbox" 
                  id="title-caps"
                  class="w-4 h-4 bg-zinc-800 rounded focus:ring-indigo-500 text-indigo-600 border-zinc-600"
                />
                <label for="title-caps" class="ml-2 text-sm text-zinc-400">全大写</label>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 正文设置 -->
        <div class="bg-zinc-900 rounded-lg p-4">
          <h3 class="text-md font-medium mb-3 border-b border-zinc-700 pb-2">正文设置</h3>
          
          <div class="space-y-3">
            <div>
              <label class="block text-sm font-medium text-zinc-400 mb-1">中文字体</label>
              <input 
                v-model="configData.body.fonts.zh_family"
                type="text" 
                class="w-full bg-zinc-800 text-zinc-100 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-zinc-400 mb-1">英文字体</label>
              <input 
                v-model="configData.body.fonts.en_family"
                type="text" 
                class="w-full bg-zinc-800 text-zinc-100 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-zinc-400 mb-1">字体大小</label>
              <input 
                v-model="configData.body.fonts.size"
                type="text" 
                class="w-full bg-zinc-800 text-zinc-100 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-zinc-400 mb-1">行间距</label>
              <input 
                v-model="configData.body.line_spacing"
                type="text" 
                class="w-full bg-zinc-800 text-zinc-100 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
        </div>
        
        <!-- 高级设置 -->
        <div class="bg-zinc-900 rounded-lg p-4">
          <h3 class="text-md font-medium mb-3 border-b border-zinc-700 pb-2">高级设置</h3>
          
          <div class="space-y-3">
            <div>
              <label class="block text-sm font-medium text-zinc-400 mb-1">JSON 编辑器</label>
              <textarea 
                v-model="jsonEditor"
                rows="10"
                class="w-full bg-zinc-800 text-zinc-100 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-sm"
                @input="updateFromJson"
              ></textarea>
            </div>
            
            <div v-if="jsonError" class="text-red-500 text-sm">
              {{ jsonError }}
            </div>
          </div>
        </div>
      </div>
      
      <div v-else class="text-center py-12 text-zinc-500">
        未加载配置数据，请点击"加载示例配置"按钮。
      </div>
    </div>
    
    <!-- 保存成功提示 -->
    <div 
      v-if="showSaveSuccess" 
      class="fixed bottom-4 right-4 bg-green-600 text-white px-4 py-2 rounded-md shadow-lg"
    >
      配置已成功保存！
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import axios from 'axios'

// 状态变量
const configData = ref(null)
const loading = ref(false)
const jsonEditor = ref('')
const jsonError = ref('')
const showSaveSuccess = ref(false)

// 监听配置数据变化，更新JSON编辑器
watch(configData, (newVal) => {
  if (newVal) {
    try {
      jsonEditor.value = JSON.stringify(newVal, null, 2)
    } catch (error) {
      console.error('JSON序列化错误:', error)
    }
  }
}, { deep: true })

// 从JSON编辑器更新配置数据
function updateFromJson() {
  try {
    const parsed = JSON.parse(jsonEditor.value)
    configData.value = parsed
    jsonError.value = ''
  } catch (error) {
    jsonError.value = '无效的JSON格式: ' + error.message
  }
}

// 加载示例配置
async function loadExampleConfig() {
  loading.value = true
  jsonError.value = ''
  
  try {
    const response = await axios.get('/api/get-config-example')
    configData.value = response.data.config
  } catch (error) {
    console.error('加载示例配置失败:', error)
    alert('加载示例配置失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 保存配置
async function saveConfig() {
  if (!configData.value) return
  
  loading.value = true
  jsonError.value = ''
  
  try {
    const response = await axios.post('/api/create-config', {
      config_path: 'config.json',
      config_data: configData.value
    })
    
    if (response.data.success) {
      showSaveSuccess.value = true
      setTimeout(() => {
        showSaveSuccess.value = false
      }, 3000)
    } else {
      alert('保存配置失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('保存配置失败:', error)
    alert('保存配置失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 组件挂载时加载配置
onMounted(async () => {
  try {
    const response = await axios.get('/config.json')
    configData.value = response.data
  } catch (error) {
    console.error('加载配置失败:', error)
    // 不显示错误提示，让用户手动加载示例配置
  }
})
</script> 