<template>
  <div class="flex flex-col h-full">
    <!-- 标签页头部 -->
    <div class="flex border-b" :class="isDarkMode ? 'border-zinc-800' : 'border-gray-200'">
      <button 
        v-for="agent in agents" 
        :key="agent.id"
         @click="selectAgent(agent.id)"
        class="px-4 py-2 font-medium transition-colors relative group"
        :class="[
          activeAgentId === agent.id 
            ? isDarkMode 
              ? 'text-blue-400 border-b-2 border-blue-400' 
              : 'text-blue-600 border-b-2 border-blue-600'
            : isDarkMode 
              ? 'text-zinc-400 hover:text-zinc-100' 
              : 'text-gray-500 hover:text-gray-700'
        ]"
      >
        <div class="flex items-center">
          <div class="w-4 h-4 rounded-full mr-2" :class="agent.bgColor"></div>
          {{ agent.name }}
        </div>
        <!-- 切换反馈效果 -->
        <span 
          class="absolute bottom-0 left-0 w-full h-0.5 transform scale-x-0 transition-transform duration-300 group-hover:scale-x-100"
          :class="activeAgentId !== agent.id ? isDarkMode ? 'bg-zinc-700' : 'bg-gray-300' : ''"
        ></span>
      </button>
      
      <!-- 协作按钮 -->
      <button 
        @click="startCollaboration"
        class="ml-auto px-4 py-2 flex items-center transition-colors"
        :class="isDarkMode ? 'text-zinc-400 hover:text-zinc-100' : 'text-gray-500 hover:text-gray-700'"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-1">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
          <circle cx="9" cy="7" r="4"></circle>
          <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
          <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
        </svg>
        协作模式
      </button>
    </div>
    
    <!-- 标签页内容 -->
    <div class="flex-1 overflow-hidden">
      <div v-for="agent in agents" :key="agent.id" v-show="activeAgentId === agent.id || collaborationMode" class="h-full">
        <slot :name="agent.id"></slot>
      </div>
      
      <!-- 协作模式内容 -->
      <div v-if="collaborationMode" class="h-full">
        <slot name="collaboration"></slot>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject } from 'vue'

const props = defineProps({
  agents: {
    type: Array,
    required: true
  },
  initialAgentId: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['agent-change', 'collaboration-start'])

const isDarkMode = inject('isDarkMode')
const activeAgentId = ref(props.initialAgentId || (props.agents.length > 0 ? props.agents[0].id : ''))
const collaborationMode = ref(false)

function selectAgent(agentId) {
  activeAgentId.value = agentId
  collaborationMode.value = false
  emit('agent-change', agentId)
}

function startCollaboration() {
  collaborationMode.value = true
  emit('collaboration-start')
}
</script>