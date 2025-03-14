<template>
  <div :class="[isDarkMode ? 'bg-zinc-900' : 'bg-white border border-gray-200', 'rounded-lg p-4']">
    <h3 class="text-md font-medium mb-3 pb-2" :class="[isDarkMode ? 'border-zinc-700' : 'border-gray-200', 'border-b']">{{ title }}</h3>
    
    <div class="space-y-3">
      <!-- 段落格式设置 -->
      <div v-if="config.paragraph_format">
        <h4 :class="[isDarkMode ? 'text-zinc-300' : 'text-gray-700', 'text-sm font-medium mb-2']">段落格式</h4>
        <div class="space-y-3">
          <div>
            <label :class="[isDarkMode ? 'text-zinc-400' : 'text-gray-600', 'block text-sm mb-1']">对齐方式</label>
            <select 
              v-model="config.paragraph_format.alignment"
              :class="[
                isDarkMode ? 'bg-zinc-800 text-zinc-100' : 'bg-gray-50 text-gray-900 border border-gray-300',
                'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-2',
                isDarkMode ? 'focus:ring-blue-500' : 'focus:ring-blue-600'
              ]"
            >
              <option value="left">左对齐</option>
              <option value="center">居中</option>
              <option value="right">右对齐</option>
              <option value="justify">两端对齐</option>
            </select>
          </div>

          <div>
            <label :class="[isDarkMode ? 'text-zinc-400' : 'text-gray-600', 'block text-sm mb-1']">首行缩进</label>
            <input 
              v-model="config.paragraph_format.indentation.first_line"
              type="number"
              step="0.1"
              :class="[
                isDarkMode ? 'bg-zinc-800 text-zinc-100' : 'bg-gray-50 text-gray-900 border border-gray-300',
                'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-2',
                isDarkMode ? 'focus:ring-blue-500' : 'focus:ring-blue-600'
              ]"
            />
          </div>

          <div>
            <label :class="[isDarkMode ? 'text-zinc-400' : 'text-gray-600', 'block text-sm mb-1']">段前间距</label>
            <input 
              v-model="config.paragraph_format.before_spacing"
              type="number"
              step="1"
              :class="[
                isDarkMode ? 'bg-zinc-800 text-zinc-100' : 'bg-gray-50 text-gray-900 border border-gray-300',
                'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-2',
                isDarkMode ? 'focus:ring-blue-500' : 'focus:ring-blue-600'
              ]"
            />
          </div>

          <div>
            <label :class="[isDarkMode ? 'text-zinc-400' : 'text-gray-600', 'block text-sm mb-1']">段后间距</label>
            <input 
              v-model="config.paragraph_format.after_spacing"
              type="number"
              step="1"
              :class="[
                isDarkMode ? 'bg-zinc-800 text-zinc-100' : 'bg-gray-50 text-gray-900 border border-gray-300',
                'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-2',
                isDarkMode ? 'focus:ring-blue-500' : 'focus:ring-blue-600'
              ]"
            />
          </div>

          <div>
            <label :class="[isDarkMode ? 'text-zinc-400' : 'text-gray-600', 'block text-sm mb-1']">行间距</label>
            <select 
              v-model="config.paragraph_format.line_spacing"
              :class="[
                isDarkMode ? 'bg-zinc-800 text-zinc-100' : 'bg-gray-50 text-gray-900 border border-gray-300',
                'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-2',
                isDarkMode ? 'focus:ring-blue-500' : 'focus:ring-blue-600'
              ]"
            >
              <option value="单倍行距">单倍行距</option>
              <option value="1.5倍行距">1.5倍行距</option>
              <option value="2倍行距">2倍行距</option>
            </select>
          </div>
        </div>
      </div>

      <!-- 字体设置 -->
      <div v-if="config.fonts">
        <h4 :class="[isDarkMode ? 'text-zinc-300' : 'text-gray-700', 'text-sm font-medium mb-2']">字体设置</h4>
        <div class="space-y-3">
          <div>
            <label :class="[isDarkMode ? 'text-zinc-400' : 'text-gray-600', 'block text-sm mb-1']">中文字体</label>
            <input 
              v-model="config.fonts.zh_family"
              type="text"
              :class="[
                isDarkMode ? 'bg-zinc-800 text-zinc-100' : 'bg-gray-50 text-gray-900 border border-gray-300',
                'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-2',
                isDarkMode ? 'focus:ring-blue-500' : 'focus:ring-blue-600'
              ]"
            />
          </div>

          <div>
            <label :class="[isDarkMode ? 'text-zinc-400' : 'text-gray-600', 'block text-sm mb-1']">英文字体</label>
            <input 
              v-model="config.fonts.en_family"
              type="text"
              :class="[
                isDarkMode ? 'bg-zinc-800 text-zinc-100' : 'bg-gray-50 text-gray-900 border border-gray-300',
                'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-2',
                isDarkMode ? 'focus:ring-blue-500' : 'focus:ring-blue-600'
              ]"
            />
          </div>

          <div>
            <label :class="[isDarkMode ? 'text-zinc-400' : 'text-gray-600', 'block text-sm mb-1']">字体大小</label>
            <input 
              v-model="config.fonts.size"
              type="number"
              :class="[
                isDarkMode ? 'bg-zinc-800 text-zinc-100' : 'bg-gray-50 text-gray-900 border border-gray-300',
                'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-2',
                isDarkMode ? 'focus:ring-blue-500' : 'focus:ring-blue-600'
              ]"
            />
          </div>

          <div>
            <label :class="[isDarkMode ? 'text-zinc-400' : 'text-gray-600', 'block text-sm mb-1']">字体颜色</label>
            <input 
              v-model="config.fonts.color"
              type="color"
              :class="[
                isDarkMode ? 'bg-zinc-800' : 'bg-gray-50 border border-gray-300',
                'w-full h-10 rounded-md px-2 focus:outline-none focus:ring-2',
                isDarkMode ? 'focus:ring-blue-500' : 'focus:ring-blue-600'
              ]"
            />
          </div>

          <div class="flex space-x-4">
            <div class="flex items-center">
              <input 
                v-model="config.fonts.bold"
                type="checkbox"
                :class="[
                  isDarkMode ? 'bg-zinc-800 border-zinc-600' : 'bg-gray-50 border-gray-300',
                  'w-4 h-4 rounded focus:ring-2',
                  isDarkMode ? 'focus:ring-blue-500 text-blue-600' : 'focus:ring-blue-600 text-blue-600'
                ]"
              />
              <label :class="[isDarkMode ? 'text-zinc-400' : 'text-gray-600', 'ml-2 text-sm']">粗体</label>
            </div>

            <div class="flex items-center">
              <input 
                v-model="config.fonts.italic"
                type="checkbox"
                :class="[
                  isDarkMode ? 'bg-zinc-800 border-zinc-600' : 'bg-gray-50 border-gray-300',
                  'w-4 h-4 rounded focus:ring-2',
                  isDarkMode ? 'focus:ring-blue-500 text-blue-600' : 'focus:ring-blue-600 text-blue-600'
                ]"
              />
              <label :class="[isDarkMode ? 'text-zinc-400' : 'text-gray-600', 'ml-2 text-sm']">斜体</label>
            </div>

            <div class="flex items-center">
              <input 
                v-model="config.fonts.isAllcaps"
                type="checkbox"
                :class="[
                  isDarkMode ? 'bg-zinc-800 border-zinc-600' : 'bg-gray-50 border-gray-300',
                  'w-4 h-4 rounded focus:ring-2',
                  isDarkMode ? 'focus:ring-blue-500 text-blue-600' : 'focus:ring-blue-600 text-blue-600'
                ]"
              />
              <label :class="[isDarkMode ? 'text-zinc-400' : 'text-gray-600', 'ml-2 text-sm']">全大写</label>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits, watch } from 'vue'

const props = defineProps({
  isDarkMode: {
    type: Boolean,
    default: true
  },
  title: {
    type: String,
    required: true
  },
  config: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:config'])

// Watch for deep changes in config and emit updates
watch(() => props.config, (newVal) => {
  emit('update:config', newVal)
}, { deep: true })
</script>
