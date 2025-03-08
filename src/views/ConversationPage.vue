<template>
  <div class="conversation-container">
    <!-- 左侧对话区 -->
    <div class="chat-section">
      <div class="header">
        <h1>{{ pageTitle }}</h1>
      </div>
      
      <div class="messages-container" ref="messagesContainer">
        <div 
          v-for="(message, index) in messages" 
          :key="index"
          :class="['message', message.sender === 'user' ? 'user-message' : 'agent-message']"
        >
          <div class="message-header">
            <span class="sender-name">{{ message.sender === 'user' ? '用户' : 'Agent' }}</span>
            <span class="message-time">{{ formatTime(message.timestamp) }}</span>
          </div>
          <div class="message-content" v-html="formatMessage(message.content)"></div>
        </div>
      </div>
      
      <div class="input-container">
        <div class="input-wrapper">
          <textarea 
            v-model="userInput" 
            placeholder="请输入您的问题或指令..."
            @keydown.enter.prevent="sendMessage"
            class="message-input"
          ></textarea>
          <button @click="sendMessage" class="send-button" :disabled="!userInput.trim()">
            发送
          </button>
        </div>
      </div>
      
      <!-- 执行步骤展示 -->
      <div class="execution-steps" v-if="executionSteps.length > 0">
        <h3>执行步骤</h3>
        <div class="steps-container">
          <div 
            v-for="(step, index) in executionSteps" 
            :key="index"
            :class="['step', { 'active': step.active, 'completed': step.completed }]"
          >
            <div class="step-number">{{ index + 1 }}</div>
            <div class="step-content">
              <div class="step-title">{{ step.title }}</div>
              <div class="step-description" v-if="step.description">{{ step.description }}</div>
              <div class="step-progress" v-if="step.progress !== undefined">
                <div class="progress-bar">
                  <div 
                    class="progress-fill" 
                    :style="{ width: `${step.progress}%` }"
                  ></div>
                </div>
                <span class="progress-text">{{ step.progress }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 右侧预览区 -->
    <div class="preview-section">
      <div class="preview-controls">
        <div class="slider-container">
          <div class="slider-track">
            <div 
              class="slider-handle" 
              :style="{ left: `${previewRatio * 100}%` }"
              @mousedown="startDrag"
            ></div>
          </div>
        </div>
        <div class="preview-tabs">
          <button 
            @click="activePreview = 'json'"
            :class="['tab-button', { active: activePreview === 'json' }]"
          >
            JSON 配置
          </button>
          <button 
            @click="activePreview = 'docx'"
            :class="['tab-button', { active: activePreview === 'docx' }]"
          >
            DOCX 预览
          </button>
        </div>
      </div>
      
      <div class="preview-content">
        <!-- JSON 编辑器 -->
        <div v-show="activePreview === 'json'" class="json-editor">
          <div ref="monacoContainer" class="monaco-container"></div>
          <div class="editor-actions">
            <button @click="saveJsonChanges" class="action-button save-button">
              保存更改
            </button>
          </div>
        </div>
        
        <!-- DOCX 预览 -->
        <div v-show="activePreview === 'docx'" class="docx-preview">
          <div v-if="docxUrl" class="docx-container">
            <vue-office-docx
              :src="docxUrl"
              @loaded="handleDocxLoaded"
              @error="handleDocxError"
            />
          </div>
          <div v-else class="no-preview">
            <p>暂无文档可预览</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { VueOfficeDocx } from 'vue-office';
import * as monaco from 'monaco-editor';

// 页面标题（从后端获取）
const pageTitle = ref('开始');

// 对话相关
const messages = ref([]);
const userInput = ref('');
const messagesContainer = ref(null);

// 预览相关
const activePreview = ref('json');
const previewRatio = ref(0.5); // 滑块位置比例
const isDragging = ref(false);
const docxUrl = ref('');
const jsonData = ref({});
const monacoContainer = ref(null);
let editor = null;

// 执行步骤
const executionSteps = ref([]);

// 格式化消息内容（支持简单的Markdown语法）
const formatMessage = (content) => {
  if (!content) return '';
  
  // 处理代码块
  let formatted = content.replace(/```([\s\S]*?)```/g, '<pre class="code-block">$1</pre>');
  
  // 处理行内代码
  formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
  
  // 处理换行
  formatted = formatted.replace(/\n/g, '<br>');
  
  return formatted;
};

// 格式化时间
const formatTime = (timestamp) => {
  const date = new Date(timestamp);
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
};

// 发送消息
const sendMessage = async () => {
  if (!userInput.value.trim()) return;
  
  // 添加用户消息到对话列表
  const userMessage = {
    sender: 'user',
    content: userInput.value,
    timestamp: Date.now()
  };
  
  messages.value.push(userMessage);
  
  // 清空输入框
  const inputContent = userInput.value;
  userInput.value = '';
  
  // 滚动到底部
  scrollToBottom();
  
  try {
    // 发送消息到后端
    const response = await axios.post('/api/send-message', {
      message: inputContent
    });
    
    // 添加系统回复到对话列表
    const agentMessage = {
      sender: 'agent',
      content: response.data.reply,
      timestamp: Date.now()
    };
    
    messages.value.push(agentMessage);
    
    // 更新执行步骤
    if (response.data.steps) {
      updateExecutionSteps(response.data.steps);
    }
    
    // 滚动到底部
    scrollToBottom();
  } catch (error) {
    console.error('发送消息失败:', error);
    // 添加错误消息
    messages.value.push({
      sender: 'agent',
      content: '消息发送失败，请重试。',
      timestamp: Date.now()
    });
  }
};

// 滚动到对话底部
const scrollToBottom = () => {
  setTimeout(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
  }, 50);
};

// 更新执行步骤
const updateExecutionSteps = (steps) => {
  executionSteps.value = steps.map(step => ({
    ...step,
    active: step.status === 'active',
    completed: step.status === 'completed'
  }));
};

// 滑块拖动相关
const startDrag = (event) => {
  isDragging.value = true;
  document.addEventListener('mousemove', handleDrag);
  document.addEventListener('mouseup', stopDrag);
};

const handleDrag = (event) => {
  if (!isDragging.value) return;
  
  const sliderTrack = document.querySelector('.slider-track');
  if (!sliderTrack) return;
  
  const rect = sliderTrack.getBoundingClientRect();
  let ratio = (event.clientX - rect.left) / rect.width;
  
  // 限制在0-1范围内
  ratio = Math.max(0, Math.min(1, ratio));
  previewRatio.value = ratio;
};

const stopDrag = () => {
  isDragging.value = false;
  document.removeEventListener('mousemove', handleDrag);
  document.removeEventListener('mouseup', stopDrag);
};

// 初始化Monaco编辑器
const initMonacoEditor = () => {
  if (monacoContainer.value && !editor) {
    editor = monaco.editor.create(monacoContainer.value, {
      value: JSON.stringify(jsonData.value, null, 2),
      language: 'json',
      theme: 'vs',
      automaticLayout: true,
      minimap: { enabled: false },
      scrollBeyondLastLine: false
    });
  }
};

// 保存JSON更改
const saveJsonChanges = async () => {
  try {
    const editorContent = editor.getValue();
    const parsedContent = JSON.parse(editorContent);
    
    // 发送更新后的JSON到后端
    await axios.post('/api/update-json', {
      json: parsedContent
    });
    
    // 更新本地数据
    jsonData.value = parsedContent;
    
    // 添加成功消息
    messages.value.push({
      sender: 'agent',
      content: 'JSON配置已成功更新。',
      timestamp: Date.now()
    });
  } catch (error) {
    console.error('保存JSON失败:', error);
    // 添加错误消息
    messages.value.push({
      sender: 'agent',
      content: '保存JSON失败，请检查格式是否正确。',
      timestamp: Date.now()
    });
  }
};

// 处理DOCX加载事件
const handleDocxLoaded = () => {
  console.log('DOCX文档加载成功');
};

// 处理DOCX错误事件
const handleDocxError = (error) => {
  console.error('DOCX文档加载失败:', error);
};

// 获取初始数据
const fetchInitialData = async () => {
  try {
    // 获取页面标题
    const titleResponse = await axios.get('/api/get-title');
    pageTitle.value = titleResponse.data.title;
    
    // 获取JSON数据
    const jsonResponse = await axios.get('/api/get-json');
    jsonData.value = jsonResponse.data;
    
    // 更新编辑器内容
    if (editor) {
      editor.setValue(JSON.stringify(jsonData.value, null, 2));
    }
    
    // 获取DOCX URL
    const docxResponse = await axios.get('/api/get-docx-url');
    docxUrl.value = docxResponse.data.url;
    
    // 获取执行步骤
    const stepsResponse = await axios.get('/api/get-execution-steps');
    updateExecutionSteps(stepsResponse.data.steps);
    
    // 获取历史消息
    const messagesResponse = await axios.get('/api/get-messages');
    messages.value = messagesResponse.data.messages;
    
    // 滚动到底部
    scrollToBottom();
  } catch (error) {
    console.error('获取初始数据失败:', error);
  }
};

// 监听预览类型变化
watch(activePreview, (newValue) => {
  if (newValue === 'json' && !editor) {
    // 延迟初始化编辑器，确保DOM已更新
    setTimeout(initMonacoEditor, 100);
  }
});

// 组件挂载时
onMounted(() => {
  // 获取初始数据
  fetchInitialData();
  
  // 初始化编辑器（如果默认显示JSON）
  if (activePreview.value === 'json') {
    setTimeout(initMonacoEditor, 100);
  }
});

// 组件卸载时
onUnmounted(() => {
  // 清理编辑器实例
  if (editor) {
    editor.dispose();
    editor = null;
  }
  
  // 移除事件监听器
  document.removeEventListener('mousemove', handleDrag);
  document.removeEventListener('mouseup', stopDrag);
});
</script>

<style scoped>
.conversation-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* 左侧对话区样式 */
.chat-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e0e0e0;
  background-color: #fff;
  max-width: 60%;
}

.header {
  padding: 1rem;
  border-bottom: 1px solid #e0e0e0;
  background-color: #f8f8f8;
}

.header h1 {
  font-size: 1.5rem;
  color: #333;
  margin: 0;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.message {
  max-width: 80%;
  padding: 0.8rem 1rem;
  border-radius: 8px;
  position: relative;
  animation: message-appear 0.3s ease;
}

@keyframes message-appear {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-message {
  align-self: flex-end;
  background-color: #e3f2fd;
  border-bottom-right-radius: 2px;
}

.agent-message {
  align-self: flex-start;
  background-color: #f5f5f5;
  border-bottom-left-radius: 2px;
}

.message-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.8rem;
  color: #666;
}

.message-content {
  word-break: break-word;
  line-height: 1.5;
}

.message-content pre.code-block {
  background-color: #f0f0f0;
  padding: 0.5rem;
  border-radius: 4px;
  overflow-x: auto;
  margin: 0.5rem 0;
}

.message-content code {
  background-color: #f0f0f0;
  padding: 0.1rem 0.3rem;
  border-radius: 3px;
  font-family: monospace;
}

.input-container {
  padding: 1rem;
  border-top: 1px solid #e0e0e0;
}

.input-wrapper {
  display: flex;
  gap: 0.5rem;
}

.message-input {
  flex: 1;
  padding: 0.8rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  resize: none;
  height: 80px;
  font-family: inherit;
}

.send-button {
  padding: 0 1rem;
  background-color: #4285f4;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.send-button:hover {
  background-color: #3367d6;
}

.send-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

/* 执行步骤样式 */
.execution-steps {
  padding: 1rem;
  border-top: 1px solid #e0e0e0;
  background-color: #f8f8f8;
}

.execution-steps h3 {
  margin-bottom: 0.8rem;
  font-size: 1rem;
  color: #555;
}

.steps-container {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.step {
  display: flex;
  gap: 0.8rem;
  padding: 0.8rem;
  background-color: #fff;
  border-radius: 4px;
  border-left: 3px solid #ccc;
  transition: all 0.3s ease;
}

.step.active {
  border-left-color: #4285f4;
  background-color: #e3f2fd;
}

.step.completed {
  border-left-color: #34a853;
  background-color: #e6f4ea;
}

.step-number {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #ccc;
  color: white;
  border-radius: 50%;
  font-size: 0.8rem;
}

.step.active .step-number {
  background-color: #4285f4;
}

.step.completed .step-number {
  background-color: #34a853;
}

.step-content {
  flex: 1;
}

.step-title {
  font-weight: bold;
  margin-bottom: 0.3rem;
}

.step-description {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 0.5rem;
}

.step-progress {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background-color: #e0e0e0;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: #4285f4;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.8rem;
  color: #666;
  min-width: 40px;
  text-align: right;
}

/* 右侧预览区样式 */
.preview-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #f5f5f5;
  max-width: 40%;
}

.preview-controls {
  padding: 1rem;
  border-bottom: 1px solid #e0e0e0;
  background-color: #fff;
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.slider-container {
  padding: 0 1rem;
}

.slider-track {
  height: 4px;
  background-color: #e0e0e0;
  border-radius: 2px;
  position: relative;
  cursor: pointer;
}

.slider-handle {
  width: 16px;
  height: 16px;
  background-color: #4285f4;
  border-radius: 50%;
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  cursor: grab;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  transition: transform 0.1s;
}

.slider-handle:hover {
  transform: translate(-50%, -50%) scale(1.1);
}

.preview-tabs {
  display: flex;
  gap: 0.5rem;
}

.tab-button {
  padding: 0.5rem 1rem;
  background-color: #f0f0f0;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.tab-button.active {
  background-color: #4285f4;
  color: white;
}

.preview-content {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.json-editor, .docx-preview {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.monaco-container {
  flex: 1;
  overflow: hidden;
}

.editor-actions {
  padding: 0.8rem;
  background-color: #f8f8f8;
  border-top: 1px solid #e0e0e0;
  display: flex;
  justify-content: flex-end;
}

.action-button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.save-button {
  background-color: #34a853;
  color: white;
}

.save-button:hover {
  background-color: #2d9144;
}

.docx-container {
  width: 100%;
  height: 100%;
  overflow: auto;
}

.no-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
  font-style: italic;
}