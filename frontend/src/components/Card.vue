<template>
  <div class="rounded-lg overflow-hidden shadow-sm border transition-all duration-200 hover:shadow-md"
    :class="[
      isDarkMode 
        ? `bg-${color || 'zinc'}-900/20 border-${color || 'zinc'}-800/30` 
        : `bg-${color || 'gray'}-50 border-${color || 'gray'}-200`
    ]">
    <div v-if="header" class="px-4 py-3 border-b flex justify-between items-center"
      :class="isDarkMode ? `border-${color || 'zinc'}-800/30` : `border-${color || 'gray'}-200`">
      <slot name="header">
        <h3 class="font-medium" :class="isDarkMode ? `text-${color || 'zinc'}-100` : `text-${color || 'gray'}-900`">
          {{ header }}
        </h3>
      </slot>
    </div>
    <div class="p-4">
      <slot>
        <p :class="isDarkMode ? `text-${color || 'zinc'}-300` : `text-${color || 'gray'}-700`">
          这是卡片的内容
        </p>
      </slot>
    </div>
    <div v-if="$slots.footer" class="px-4 py-3 border-t"
      :class="isDarkMode ? `border-${color || 'zinc'}-800/30` : `border-${color || 'gray'}-200`">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Card',
  props: {
    header: String,
    color: {
      type: String,
      default: null
    }
  },
  computed: {
    isDarkMode() {
      return document.documentElement.classList.contains('dark');
    }
  }
}
</script> 