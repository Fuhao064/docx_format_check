<template>
  <router-view v-slot="{ Component }">
    <transition name="fade" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>
</template>

<script setup>
// App.vue作为根组件，只负责渲染当前路由对应的组件
</script>

<style>
/* 全局样式已在main.css中定义 */
</style>