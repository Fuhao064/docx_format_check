<template>
  <div class="p-6 overflow-y-auto transition-colors duration-[--transition-speed]"
       :class="isDarkMode ? 'bg-[hsl(var(--background))] text-[hsl(var(--foreground))]' : 'bg-[hsl(var(--background))] text-[hsl(var(--foreground))]'">
    <div class="mb-6">
      <h1 class="text-2xl font-semibold mb-2 text-[hsl(var(--foreground))]">格式配置</h1>
      <p class="text-[hsl(var(--muted-foreground))]">管理文档格式规范和样式配置</p>
    </div>

    <!-- 配置编辑器 -->
    <div :class="[isDarkMode ? 'bg-[hsl(var(--card))]' : 'bg-[hsl(var(--card))]', 'rounded-lg p-6 mb-6']">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-lg font-medium text-[hsl(var(--foreground))]">配置编辑器</h2>
        <div class="flex space-x-3">
          <button
            @click="loadExampleConfig"
            :class="[
              isDarkMode ? 'bg-[hsl(var(--secondary))] hover:bg-[hsl(var(--secondary)/0.9)] text-[hsl(var(--secondary-foreground))]' : 'bg-[hsl(var(--secondary))] hover:bg-[hsl(var(--secondary)/0.9)] text-[hsl(var(--secondary-foreground))]',
              'px-3 py-1.5 text-sm rounded-md transition-colors duration-[--transition-speed]'
            ]"
          >
            加载示例配置
          </button>
          <button
            @click="saveConfig"
            :class="[
              'bg-[hsl(var(--primary))] hover:bg-[hsl(var(--primary)/0.9)] text-[hsl(var(--primary-foreground))]',
              'px-3 py-1.5 text-sm rounded-md transition-colors duration-[--transition-speed]'
            ]"
          >
            保存配置
          </button>
          <button
            @click="toggleAdvancedMode"
            :class="[
              isDarkMode ? 'bg-[hsl(var(--secondary))] hover:bg-[hsl(var(--secondary)/0.9)] text-[hsl(var(--secondary-foreground))]' : 'bg-[hsl(var(--secondary))] hover:bg-[hsl(var(--secondary)/0.9)] text-[hsl(var(--secondary-foreground))]',
              advancedMode ? 'ring-1 ring-[hsl(var(--primary))]' : '',
              'px-3 py-1.5 text-sm rounded-md transition-colors duration-[--transition-speed]'
            ]"
          >
            高级模式
          </button>
        </div>
      </div>

      <!-- 基本模式：表单编辑器 -->
      <div v-if="!advancedMode && configData">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- 纸张设置 -->
          <div :class="[isDarkMode ? 'bg-[hsl(var(--card))] border border-[hsl(var(--border))]' : 'bg-[hsl(var(--card))] border border-[hsl(var(--border))]', 'rounded-lg p-4']">
            <h3 class="text-md font-medium mb-3 pb-2 text-[hsl(var(--foreground))]" :class="[ 'border-b border-[hsl(var(--border))]']">纸张设置</h3>

            <div class="space-y-3">
              <div>
                <label :class="['text-[hsl(var(--muted-foreground))]', 'block text-sm mb-1']">纸张大小</label>
                <select
                  v-model="configData.paper.size"
                  :class="[
                    'bg-[hsl(var(--input))] text-[hsl(var(--foreground))]',
                    'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))]'
                  ]"
                >
                  <option value="A4">A4</option>
                  <option value="Letter">Letter</option>
                  <option value="Legal">Legal</option>
                </select>
              </div>

              <div>
                <label :class="['text-[hsl(var(--muted-foreground))]', 'block text-sm mb-1']">方向</label>
                <select
                  v-model="configData.paper.orientation"
                  :class="[
                    'bg-[hsl(var(--input))] text-[hsl(var(--foreground))]',
                    'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))]'
                  ]"
                >
                  <option value="portrait">纵向</option>
                  <option value="landscape">横向</option>
                </select>
              </div>

              <div>
                <label :class="['text-[hsl(var(--muted-foreground))]', 'block text-sm mb-1']">上边距</label>
                <input
                  v-model="configData.paper.margins.top"
                  type="text"
                  :class="[
                    'bg-[hsl(var(--input))] text-[hsl(var(--foreground))]',
                    'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))]'
                  ]"
                />
              </div>

              <div>
                <label :class="['text-[hsl(var(--muted-foreground))]', 'block text-sm mb-1']">下边距</label>
                <input
                  v-model="configData.paper.margins.bottom"
                  type="text"
                  :class="[
                    'bg-[hsl(var(--input))] text-[hsl(var(--foreground))]',
                    'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))]'
                  ]"
                />
              </div>

              <div>
                <label :class="['text-[hsl(var(--muted-foreground))]', 'block text-sm mb-1']">左边距</label>
                <input
                  v-model="configData.paper.margins.left"
                  type="text"
                  :class="[
                   'bg-[hsl(var(--input))] text-[hsl(var(--foreground))]',
                    'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))]'
                  ]"
                />
              </div>

              <div>
                <label :class="['text-[hsl(var(--muted-foreground))]', 'block text-sm mb-1']">右边距</label>
                <input
                  v-model="configData.paper.margins.right"
                  type="text"
                  :class="[
                    'bg-[hsl(var(--input))] text-[hsl(var(--foreground))]',
                    'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))]'
                  ]"
                />
              </div>
            </div>
          </div>

          <!-- 中文标题 -->
          <FormatSection
            :isDarkMode="isDarkMode"
            title="中文标题"
            :config="configData.title_zh"
            @update:config="val => configData.title_zh = val"
          />

          <!-- 中文摘要 -->
          <FormatSection
            :isDarkMode="isDarkMode"
            title="中文摘要"
            :config="configData.abstract_zh"
            @update:config="val => configData.abstract_zh = val"
          />

          <!-- 中文摘要内容 -->
          <FormatSection
            :isDarkMode="isDarkMode"
            title="中文摘要内容"
            :config="configData.abstract_content_zh"
            @update:config="val => configData.abstract_content_zh = val"
          />

          <!-- 中文关键词 -->
          <FormatSection
            :isDarkMode="isDarkMode"
            title="中文关键词"
            :config="configData.keywords_zh"
            @update:config="val => configData.keywords_zh = val"
          />

          <!-- 中文关键词内容 -->
          <FormatSection
            :isDarkMode="isDarkMode"
            title="中文关键词内容"
            :config="configData.keywords_content_zh"
            @update:config="val => configData.keywords_content_zh = val"
          />

          <!-- 英文标题 -->
          <FormatSection
            :isDarkMode="isDarkMode"
            title="英文标题"
            :config="configData.title_en"
            @update:config="val => configData.title_en = val"
          />

          <!-- 英文摘要 -->
          <FormatSection
            :isDarkMode="isDarkMode"
            title="英文摘要"
            :config="configData.abstract_en"
            @update:config="val => configData.abstract_en = val"
          />

          <!-- 英文摘要内容 -->
          <FormatSection
            :isDarkMode="isDarkMode"
            title="英文摘要内容"
            :config="configData.abstract_content_en"
            @update:config="val => configData.abstract_content_en = val"
          />

          <!-- 英文关键词 -->
          <FormatSection
            :isDarkMode="isDarkMode"
            title="英文关键词"
            :config="configData.keywords_en"
            @update:config="val => configData.keywords_en = val"
          />

          <!-- 英文关键词内容 -->
          <FormatSection
            :isDarkMode="isDarkMode"
            title="英文关键词内容"
            :config="configData.keywords_content_en"
            @update:config="val => configData.keywords_content_en = val"
          />

          <!-- 一级标题 -->
          <FormatSection
            :isDarkMode="isDarkMode"
            title="一级标题"
            :config="configData.heading1"
            @update:config="val => configData.heading1 = val"
          />

          <!-- 二级标题 -->
          <FormatSection
            :isDarkMode="isDarkMode"
            title="二级标题"
            :config="configData.heading2"
            @update:config="val => configData.heading2 = val"
          />

          <!-- 三级标题 -->
          <FormatSection
            :isDarkMode="isDarkMode"
            title="三级标题"
            :config="configData.heading3"
            @update:config="val => configData.heading3 = val"
          />

          <!-- 正文 -->
          <FormatSection
            :isDarkMode="isDarkMode"
            title="正文"
            :config="configData.body"
            @update:config="val => configData.body = val"
          />
        </div>
      </div>

      <!-- 高级模式：JSON编辑器 -->
      <div v-else-if="advancedMode && configData" class="space-y-4">
        <div class="flex justify-end space-x-3 mb-2">
          <button
            @click="exportConfig"
            :class="[
              isDarkMode ? 'bg-[hsl(var(--secondary))] hover:bg-[hsl(var(--secondary)/0.9)] text-[hsl(var(--secondary-foreground))]' : 'bg-[hsl(var(--secondary))] hover:bg-[hsl(var(--secondary)/0.9)] text-[hsl(var(--secondary-foreground))]',
              'px-3 py-1.5 text-sm rounded-md transition-colors duration-[--transition-speed]'
            ]"
          >
            导出配置
          </button>
          <label
            :class="[
              isDarkMode ? 'bg-[hsl(var(--secondary))] hover:bg-[hsl(var(--secondary)/0.9)] text-[hsl(var(--secondary-foreground))] cursor-pointer' : 'bg-[hsl(var(--secondary))] hover:bg-[hsl(var(--secondary)/0.9)] text-[hsl(var(--secondary-foreground))] cursor-pointer',
              'px-3 py-1.5 text-sm rounded-md transition-colors duration-[--transition-speed]'
            ]"
          >
            导入配置
            <input
              type="file"
              accept=".json"
              class="hidden"
              @change="importConfig"
            />
          </label>
        </div>

        <textarea
          v-model="jsonConfig"
          :class="[
            'bg-[hsl(var(--input))] text-[hsl(var(--foreground))]',
            'w-full h-[60vh] font-mono text-sm p-4 rounded-md border focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))]',
            jsonError ? 'border-red-500' : '' // Keep red border for error
          ]"
          @input="validateJson"
        ></textarea>

        <div v-if="jsonError" class="text-red-500 text-sm mt-2">
          {{ jsonError }}
        </div>
      </div>

      <div v-else class="text-center py-12 text-[hsl(var(--muted-foreground))]">
        未加载配置数据，请点击"加载示例配置"按钮。
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted, watch } from 'vue'
import axios from 'axios'
import FormatSection from '../components/FormatSection.vue'

// 获取主题模式和通知函数
const isDarkMode = inject('isDarkMode', ref(true))
const showNotification = inject('showNotification', null)

// 配置数据
const configData = ref(null)
const loading = ref(false)
const advancedMode = ref(false)
const jsonConfig = ref('')
const jsonError = ref(null)

// 切换高级模式
function toggleAdvancedMode() {
  if (advancedMode.value) {
    // 从高级模式切换到基本模式，应用JSON编辑器中的更改
    if (!jsonError.value) {
      try {
        configData.value = JSON.parse(jsonConfig.value)
      } catch (error) {
        showNotification('error', 'JSON解析错误', error.message)
        return
      }
    } else {
      showNotification('error', 'JSON格式错误', '请先修复JSON格式错误')
      return
    }
  } else {
    // 从基本模式切换到高级模式，更新JSON编辑器
    jsonConfig.value = JSON.stringify(configData.value, null, 2)
  }
  advancedMode.value = !advancedMode.value
}

// 验证JSON格式
function validateJson() {
  try {
    JSON.parse(jsonConfig.value)
    jsonError.value = null
  } catch (error) {
    jsonError.value = `JSON格式错误: ${error.message}`
  }
}

// 导出配置
function exportConfig() {
  const dataStr = JSON.stringify(configData.value, null, 2)
  const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr)

  const exportFileDefaultName = 'config.json'

  const linkElement = document.createElement('a')
  linkElement.setAttribute('href', dataUri)
  linkElement.setAttribute('download', exportFileDefaultName)
  linkElement.click()
}

// 导入配置
function importConfig(event) {
  const file = event.target.files[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const importedConfig = JSON.parse(e.target.result)
      configData.value = importedConfig
      jsonConfig.value = JSON.stringify(importedConfig, null, 2)
      showNotification('success', '导入成功', '配置已成功导入')
    } catch (error) {
      showNotification('error', '导入失败', `无法解析JSON: ${error.message}`)
    }
  }
  reader.readAsText(file)
}

// 加载示例配置
async function loadExampleConfig() {
  loading.value = true
  try {
    const response = await axios.get('/api/get-config-example')
    configData.value = response.data.config
    if (advancedMode.value) {
      jsonConfig.value = JSON.stringify(configData.value, null, 2)
    }
    showNotification('success', '加载成功', '已加载示例配置')
  } catch (error) {
    console.error('加载示例配置失败:', error)
    showNotification('error', '加载失败', '无法加载示例配置，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 保存配置
async function saveConfig() {
  if (!configData.value) return

  // 如果在高级模式下，先验证并应用JSON编辑器中的更改
  if (advancedMode.value) {
    if (jsonError.value) {
      showNotification('error', 'JSON格式错误', '请先修复JSON格式错误')
      return
    }

    try {
      configData.value = JSON.parse(jsonConfig.value)
    } catch (error) {
      showNotification('error', 'JSON解析错误', error.message)
      return
    }
  }

  loading.value = true
  try {
    const response = await axios.post('/api/set-config', configData.value)

    if (response.data.message === '配置保存成功') {
      showNotification('success', '保存成功', '配置已保存')
    } else {
      showNotification('error', '保存失败', response.data.message || '未知错误')
    }
  } catch (error) {
    console.error('保存配置失败:', error)
    showNotification('error', '保存失败', '无法保存配置，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 组件挂载时加载配置
onMounted(async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/get-config')
    configData.value = response.data
  } catch (error) {
    console.error('加载配置失败:', error)
    showNotification('error', '加载失败', '无法加载配置，请稍后重试')
  } finally {
    loading.value = false
  }
})
</script>