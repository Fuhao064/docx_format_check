<template>
  <div class="stat-card p-4 rounded-lg bg-[hsl(var(--card))] border border-[hsl(var(--border))] transition-all hover:shadow-md">
    <div class="flex items-center gap-3">
      <div
        class="w-10 h-10 rounded-lg flex items-center justify-center"
        :class="{
          'bg-[hsl(var(--primary)/0.15)] text-[hsl(var(--primary))]': color === 'primary',
          'bg-[hsl(var(--success)/0.15)] text-[hsl(var(--success))]': color === 'success',
          'bg-[hsl(var(--warning)/0.15)] text-[hsl(var(--warning))]': color === 'warning',
          'bg-[hsl(var(--destructive)/0.15)] text-[hsl(var(--destructive))]': color === 'destructive'
        }"
      >
        <!-- tasks icon -->
        <svg v-if="icon === 'tasks'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 11l3 3L22 4"></path>
          <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
        </svg>
        <!-- check icon -->
        <svg v-else-if="icon === 'check'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
          <polyline points="22 4 12 14.01 9 11.01"></polyline>
        </svg>
        <!-- clock icon -->
        <svg v-else-if="icon === 'clock'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <polyline points="12 6 12 12 16 14"></polyline>
        </svg>
        <!-- alert icon -->
        <svg v-else-if="icon === 'alert'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3l-8.47-14.14a2 2 0 0 0-3.42 0z"></path>
          <line x1="12" y1="9" x2="12" y2="13"></line>
          <line x1="12" y1="17" x2="12.01" y2="17"></line>
        </svg>
        <!-- default file icon -->
        <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
        </svg>
      </div>
      <div>
        <p class="text-2xl font-bold text-[hsl(var(--foreground))]">{{ value }}</p>
        <p class="text-sm text-[hsl(var(--muted-foreground))]">{{ title }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true
  },
  value: {
    type: Number,
    default: 0
  },
  icon: {
    type: String,
    default: 'file'
  },
  color: {
    type: String,
    default: 'primary'
  }
})
</script>

<style scoped>
.stat-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
}
</style>
