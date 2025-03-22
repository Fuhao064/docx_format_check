<template>
  <div :class="[isDarkMode ? 'bg-[hsl(var(--card))] border border-[hsl(var(--border))]' : 'bg-[hsl(var(--card))] border border-[hsl(var(--border))]', 'rounded-lg p-4']">
    <h3 class="text-md font-medium mb-3 pb-2 text-[hsl(var(--foreground))]" :class="['border-b border-[hsl(var(--border))]']">{{ title }}</h3>

    <div class="space-y-3">
      <!-- 段落格式设置 -->
      <div v-if="config.paragraph_format">
        <h4 class="text-[hsl(var(--muted-foreground))] text-sm font-medium mb-2">段落格式</h4>
        <div class="space-y-3">
          <div>
            <label class="text-[hsl(var(--muted-foreground))] block text-sm mb-1">对齐方式</label>
            <select
              v-model="config.paragraph_format.alignment"
              :class="[
                'bg-[hsl(var(--input))] text-[hsl(var(--foreground))]',
                'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))]'
              ]"
            >
              <option value="left">左对齐</option>
              <option value="center">居中</option>
              <option value="right">右对齐</option>
              <option value="justify">两端对齐</option>
            </select>
          </div>

          <div>
            <label class="text-[hsl(var(--muted-foreground))] block text-sm mb-1">首行缩进</label>
            <input
              v-model="config.paragraph_format.indentation.first_line"
              type="number"
              step="0.1"
              :class="[
                'bg-[hsl(var(--input))] text-[hsl(var(--foreground))]',
                'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))]'
              ]"
            />
          </div>

          <div>
            <label class="text-[hsl(var(--muted-foreground))] block text-sm mb-1">段前间距</label>
            <input
              v-model="config.paragraph_format.before_spacing"
              type="number"
              step="1"
              :class="[
                'bg-[hsl(var(--input))] text-[hsl(var(--foreground))]',
                'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))]'
              ]"
            />
          </div>

          <div>
            <label class="text-[hsl(var(--muted-foreground))] block text-sm mb-1">段后间距</label>
            <input
              v-model="config.paragraph_format.after_spacing"
              type="number"
              step="1"
              :class="[
               'bg-[hsl(var(--input))] text-[hsl(var(--foreground))]',
                'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))]'
              ]"
            />
          </div>

          <div>
            <label class="text-[hsl(var(--muted-foreground))] block text-sm mb-1">行间距</label>
            <select
              v-model="config.paragraph_format.line_spacing"
              :class="[
                'bg-[hsl(var(--input))] text-[hsl(var(--foreground))]',
                'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))]'
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
        <h4 class="text-[hsl(var(--muted-foreground))] text-sm font-medium mb-2">字体设置</h4>
        <div class="space-y-3">
          <div>
            <label class="text-[hsl(var(--muted-foreground))] block text-sm mb-1">中文字体</label>
            <input
              v-model="config.fonts.zh_family"
              type="text"
              :class="[
                'bg-[hsl(var(--input))] text-[hsl(var(--foreground))]',
                'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))]'
              ]"
            />
          </div>

          <div>
            <label class="text-[hsl(var(--muted-foreground))] block text-sm mb-1">英文字体</label>
            <input
              v-model="config.fonts.en_family"
              type="text"
              :class="[
                'bg-[hsl(var(--input))] text-[hsl(var(--foreground))]',
                'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))]'
              ]"
            />
          </div>

          <div>
            <label class="text-[hsl(var(--muted-foreground))] block text-sm mb-1">字体大小</label>
            <input
              v-model="config.fonts.size"
              type="number"
              :class="[
                'bg-[hsl(var(--input))] text-[hsl(var(--foreground))]',
                'w-full rounded-md px-3 py-2 focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))]'
              ]"
            />
          </div>

          <div>
            <label class="text-[hsl(var(--muted-foreground))] block text-sm mb-1">字体颜色</label>
            <input
              v-model="config.fonts.color"
              type="color"
              :class="[
                'bg-[hsl(var(--input))]',  
                'w-full h-10 rounded-md px-2 focus:outline-none focus:ring-1 focus:ring-[hsl(var(--ring))]',
                'appearance-none' 
              ]"
            />
          </div>

          <div class="flex space-x-4">
            <div class="flex items-center">
              <input
                v-model="config.fonts.bold"
                type="checkbox"
                :class="[
                  'bg-[hsl(var(--input))] border border-[hsl(var(--border))] text-[hsl(var(--primary))]',
                  'w-4 h-4 rounded focus:ring-2 focus:ring-[hsl(var(--ring))]',
                  'checked:bg-[hsl(var(--primary))] checked:border-[hsl(var(--primary))]' 
                ]"
              />
              <label class="text-[hsl(var(--muted-foreground))] ml-2 text-sm">粗体</label>
            </div>

            <div class="flex items-center">
              <input
                v-model="config.fonts.italic"
                type="checkbox"
                :class="[
                  'bg-[hsl(var(--input))] border border-[hsl(var(--border))] text-[hsl(var(--primary))]',
                  'w-4 h-4 rounded focus:ring-2 focus:ring-[hsl(var(--ring))]',
                  'checked:bg-[hsl(var(--primary))] checked:border-[hsl(var(--primary))]'
                ]"
              />
              <label class="text-[hsl(var(--muted-foreground))] ml-2 text-sm">斜体</label>
            </div>

            <div class="flex items-center">
              <input
                v-model="config.fonts.isAllcaps"
                type="checkbox"
                :class="[
                  'bg-[hsl(var(--input))] border border-[hsl(var(--border))] text-[hsl(var(--primary))]',
                  'w-4 h-4 rounded focus:ring-2 focus:ring-[hsl(var(--ring))]',
                  'checked:bg-[hsl(var(--primary))] checked:border-[hsl(var(--primary))]'
                ]"
              />
              <label class="text-[hsl(var(--muted-foreground))] ml-2 text-sm">全大写</label>
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

<style scoped>
/* Remove default appearance for color input */
input[type="color"]::-webkit-color-swatch-wrapper {
  padding: 0;
}

input[type="color"]::-webkit-color-swatch {
  border: none;
  border-radius: inherit; /* Inherit border-radius from the input */
}
input[type="color"] {
    -webkit-appearance: none;
    border: none;
    width: 32px;
    height: 32px;
}
input[type="color"]::-webkit-color-swatch-wrapper {
    padding: 0;
}
input[type="color"]::-webkit-color-swatch {
    border: none;
}
</style>