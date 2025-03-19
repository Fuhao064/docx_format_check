<!-- src/components/Dialog.vue -->
<template>
  <div class="flex flex-col h-screen">
    <!-- 对话界面 -->
    <div class="flex-1 flex overflow-hidden">
      <!-- 主内容区域 -->
      <div class="flex-1 flex flex-col overflow-hidden p-4" :class="isDarkMode ? 'bg-zinc-900' : 'bg-gray-50'">
        
        <!-- 文档错误卡片区域 -->
        <div v-if="formatErrors.length > 0" class="mb-4">
          <div class="rounded-lg overflow-hidden shadow-sm border"
            :class="isDarkMode ? 'bg-red-900/20 border-red-800/30' : 'bg-red-50 border-red-200'">
            <div class="p-4">
              <h4 class="font-medium mb-2" :class="isDarkMode ? 'text-red-400' : 'text-red-700'">
                发现以下格式问题：
              </h4>
              <ul class="list-disc pl-5 space-y-2">
                <li v-for="(error, index) in formatErrors" :key="index" class="text-sm p-2 rounded-md"
                  :class="isDarkMode ? 'text-red-300' : 'text-red-700'">
                  {{ error.message }}
                  <div v-if="error.location" class="text-xs mt-1"
                    :class="isDarkMode ? 'text-zinc-400' : 'text-gray-600'">
                    位置: {{ error.location }}
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <!-- 对话区域 -->
        <div class="flex-1 flex flex-col rounded-lg border overflow-hidden"
          :class="isDarkMode ? 'bg-zinc-800 border-zinc-700' : 'bg-white border-gray-200'">
          
          <!-- 对话历史记录 -->
          <div class="flex-1 overflow-y-auto p-4 space-y-4">
            <div v-for="(message, index) in messages" :key="index" class="flex flex-col">
              <div class="flex items-start" :class="{'justify-end': message.sender === 'user'}">
                <div class="max-w-[80%] rounded-lg p-3 shadow-sm" 
                  :class="message.sender === 'user' ? 
                    (isDarkMode ? 'bg-blue-700 text-white' : 'bg-blue-500 text-white') : 
                    (isDarkMode ? 'bg-zinc-700 text-zinc-100' : 'bg-gray-100 text-gray-900')">
                  <p class="whitespace-pre-wrap">{{ message.content }}</p>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 输入框区域 -->
          <div class="border-t p-4" :class="isDarkMode ? 'border-zinc-700' : 'border-gray-200'">
            <div class="relative">
              <textarea 
                v-model="messageInput" 
                @keydown.enter.prevent="sendMessage"
                class="w-full pr-10 rounded-lg border resize-none focus:ring-2 transition-colors leading-normal"
                :class="isDarkMode ? 
                  'bg-zinc-700 border-zinc-600 text-zinc-100 focus:border-blue-500 focus:ring-blue-500/50' : 
                  'bg-white border-gray-300 text-gray-900 focus:border-blue-500 focus:ring-blue-500/50'"
                placeholder="输入您的问题..."
                rows="2"
              ></textarea>
              <button 
                @click="sendMessage" 
                class="absolute right-2 bottom-2 p-2 rounded-full transition-colors"
                :class="isDarkMode ? 'hover:bg-zinc-600 text-blue-400' : 'hover:bg-gray-100 text-blue-500'"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13"></line>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Dialogue',
  data() {
    return {
      messageInput: '',
      messages: [],
      formatErrors: [
        // 示例错误数据
        { message: '文档标题不符合格式要求', location: '第1页，第1段' },
        { message: '引用格式不正确', location: '第5页，参考文献部分' },
        { message: '图表标题不符合规范', location: '第8页，图3' }
      ]
    }
  },
  computed: {
    isDarkMode() {
      // 从父组件或状态管理中获取
      return document.documentElement.classList.contains('dark');
    },
  },
  methods: {
    sendMessage() {
      if (!this.messageInput.trim()) return;
      
      // 添加用户消息
      this.messages.push({
        sender: 'user',
        content: this.messageInput.trim()
      });
      
      const userQuestion = this.messageInput.trim();
      this.messageInput = '';
      
      // 模拟回复
      setTimeout(() => {
        this.messages.push({
          sender: 'system',
          content: `您的问题是关于"${userQuestion}"的。这是一个自动回复示例。实际实现中，您可以连接到后端API获取响应。`
        });
      }, 1000);
    }
  }
}
</script>