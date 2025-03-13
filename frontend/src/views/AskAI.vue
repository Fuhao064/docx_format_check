<template>
  <div class="p-4">
    <h1 class="text-2xl font-bold mb-4">问AI</h1>
    <div class="space-y-4">
      <input 
        v-model="question" 
        placeholder="请输入问题..." 
        class="w-full p-2 bg-gray-800 text-white rounded-md"
      />
      <button 
        @click="submitQuestion" 
        class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
      >
        提交
      </button>
      <div v-if="answer" class="p-4 bg-gray-800 rounded-md">
        <p class="text-gray-400">{{ answer }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const question = ref('')
const answer = ref('')

function submitQuestion() {
  // 模拟AI回复
  answer.value = `您问的问题是：${question.value}`
}
</script>