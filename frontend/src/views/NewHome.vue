<template>
    <div class="flex flex-col h-screen">
        <!-- 对话界面 -->
        <div class="flex-1 flex overflow-hidden w-1/2 mx-auto">
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

                <!-- 上传文件区域 -->
                <div v-if="!hasUploadedFile" class="flex-1 flex flex-col items-center justify-center p-6">
                    <div class="w-16 h-16 mb-4" :class="isDarkMode ? 'text-blue-400' : 'text-blue-700'">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                            stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                            <polyline points="14 2 14 8 20 8"></polyline>
                            <line x1="16" y1="13" x2="8" y2="13"></line>
                            <line x1="16" y1="17" x2="8" y2="17"></line>
                            <polyline points="10 9 9 9 8 9"></polyline>
                        </svg>
                    </div>
                    <p class="text-lg font-medium" :class="isDarkMode ? 'text-zinc-100' : 'text-gray-900'">开始文档处理</p>
                    <p class="text-sm mt-2 mb-6" :class="isDarkMode ? 'text-zinc-400' : 'text-gray-700'">请上传文档开始与Agent交互
                    </p>

                    <!-- 上传按钮 -->
                    <button @click="triggerFileUpload"
                        class="flex items-center justify-center gap-2 px-4 py-2 rounded-md transition-colors"
                        :class="isDarkMode ? 'bg-blue-600 hover:bg-blue-700 text-white' : 'bg-blue-600 hover:bg-blue-700 text-white'">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="17 8 12 3 7 8"></polyline>
                            <line x1="12" y1="3" x2="12" y2="15"></line>
                        </svg>
                        <span>上传文档</span>
                    </button>
                </div>

                <!-- 上传格式要求区域 -->
                <div v-if="hasUploadedFile && !hasUploadedFormat"
                    class="flex-1 flex flex-col items-center justify-center p-6">
                    <p class="text-lg font-medium" :class="isDarkMode ? 'text-zinc-100' : 'text-gray-900'">上传格式要求</p>
                    <p class="text-sm mt-2 mb-6" :class="isDarkMode ? 'text-zinc-400' : 'text-gray-700'">请上传格式要求文档以继续处理
                    </p>

                    <!-- 上传格式要求按钮 -->
                    <button @click="triggerFormatUpload"
                        class="flex items-center justify-center gap-2 px-4 py-2 rounded-md transition-colors"
                        :class="isDarkMode ? 'bg-blue-600 hover:bg-blue-700 text-white' : 'bg-blue-600 hover:bg-blue-700 text-white'">
                        <span>上传格式要求</span>
                    </button>

                    <!-- 使用默认格式按钮 -->
                    <button @click="useDefaultFormat"
                        class="flex items-center justify-center gap-2 px-4 py-2 mt-4 rounded-md transition-colors"
                        :class="isDarkMode ? 'bg-gray-600 hover:bg-gray-700 text-white' : 'bg-gray-600 hover:bg-gray-700 text-white'">
                        <span>使用默认格式</span>
                    </button>
                </div>

                <!-- 对话区域 -->
                <div v-else class="flex-1 flex flex-col rounded-lg border overflow-hidden"
                    :class="isDarkMode ? 'bg-zinc-800 border-zinc-700' : 'bg-white border-gray-200'">

                    <!-- 处理步骤显示 -->
                    <div v-if="currentStep >= 0 && currentStep < 5" class="p-4 border-b"
                        :class="isDarkMode ? 'border-zinc-700' : 'border-gray-200'">
                        <h2 class="text-lg font-semibold mb-4" :class="isDarkMode ? 'text-zinc-100' : 'text-gray-900'">
                            文档处理进度</h2>

                        <!-- 处理步骤UI -->
                        <div class="flex flex-col space-y-4">
                            <div v-for="(step, index) in processingSteps" :key="index"
                                class="flex items-center p-3 rounded-lg" :class="[
                step.status === 'completed'
                    ? isDarkMode ? 'bg-green-900/20' : 'bg-green-50'
                    : step.status === 'in_progress'
                        ? isDarkMode ? 'bg-blue-900/20' : 'bg-blue-50'
                        : step.status === 'error'
                            ? isDarkMode ? 'bg-red-900/20' : 'bg-red-50'
                            : isDarkMode ? 'bg-zinc-800/50' : 'bg-gray-100'
            ]">
                                <div class="w-8 h-8 rounded-full flex items-center justify-center mr-3" :class="[
                step.status === 'completed'
                    ? isDarkMode ? 'bg-green-600 text-white' : 'bg-green-600 text-white'
                    : step.status === 'in_progress'
                        ? isDarkMode ? 'bg-blue-600 text-white' : 'bg-blue-600 text-white'
                        : step.status === 'error'
                            ? isDarkMode ? 'bg-red-600 text-white' : 'bg-red-600 text-white'
                            : isDarkMode ? 'bg-zinc-700 text-zinc-400' : 'bg-gray-300 text-gray-700',
                'transition-colors duration-300' // 添加过渡动画
            ]">
                                    <svg v-if="step.status === 'completed'" xmlns="http://www.w3.org/2000/svg"
                                        width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                        stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                    <svg v-else-if="step.status === 'in_progress'" xmlns="http://www.w3.org/2000/svg"
                                        width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                        stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <circle cx="12" cy="12" r="10"></circle>
                                        <polyline points="12 6 12 12 16 14"></polyline>
                                    </svg>
                                    <svg v-else-if="step.status === 'error'" xmlns="http://www.w3.org/2000/svg"
                                        width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                        stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <line x1="18" y1="6" x2="6" y2="18"></line>
                                        <line x1="6" y1="6" x2="18" y2="18"></line>
                                    </svg>
                                    <span v-else>{{ index + 1 }}</span>
                                </div>
                                <div class="flex-1">
                                    <p class="font-medium" :class="isDarkMode ? 'text-zinc-100' : 'text-gray-900'">{{
                step.title }}</p>
                                    <p class="text-sm" :class="isDarkMode ? 'text-zinc-400' : 'text-gray-700'">{{
                step.description }}
                                    </p>
                                </div>
                                <div class="ml-4">
                                    <span class="text-sm font-medium" :class="[
                step.status === 'completed'
                    ? isDarkMode ? 'text-green-400' : 'text-green-700'
                    : step.status === 'in_progress'
                        ? isDarkMode ? 'text-blue-400' : 'text-blue-700'
                        : step.status === 'error'
                            ? isDarkMode ? 'text-red-400' : 'text-red-700'
                            : isDarkMode ? 'text-zinc-500' : 'text-gray-600'
            ]">
                                        {{
                step.status === 'completed' ? '已完成' :
                    step.status === 'in_progress' ? '处理中' :
                        step.status === 'error' ? '错误' : '等待中'
            }}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <!-- 操作按钮 -->
                        <div class="flex flex-wrap gap-3 mt-4">
                            <button v-if="processingComplete" @click="downloadReport"
                                class="flex items-center justify-center gap-2 px-4 py-2 rounded-md transition-colors"
                                :class="isDarkMode ? 'bg-green-600 hover:bg-green-700 text-white' : 'bg-green-600 hover:bg-green-700 text-white'">
                                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
                                    fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                                    stroke-linejoin="round">
                                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                    <polyline points="7 10 12 15 17 10"></polyline>
                                    <line x1="12" y1="15" x2="12" y2="3"></line>
                                </svg>
                                <span>下载报告</span>
                            </button>

                            <button v-if="processingComplete" @click="downloadMarkedDocument"
                                class="flex items-center justify-center gap-2 px-4 py-2 rounded-md transition-colors"
                                :class="isDarkMode ? 'bg-blue-600 hover:bg-blue-700 text-white' : 'bg-blue-600 hover:bg-blue-700 text-white'">
                                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
                                    fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                                    stroke-linejoin="round">
                                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                    <polyline points="14 2 14 8 20 8"></polyline>
                                    <line x1="16" y1="13" x2="8" y2="13"></line>
                                    <line x1="16" y1="17" x2="8" y2="17"></line>
                                    <polyline points="10 9 9 9 8 9"></polyline>
                                </svg>
                                <span>下载修正文档</span>
                            </button>

                            <button @click="resetProcess"
                                class="flex items-center justify-center gap-2 px-4 py-2 rounded-md transition-colors"
                                :class="isDarkMode ? 'bg-zinc-700 hover:bg-zinc-600 text-white' : 'bg-gray-200 hover:bg-gray-300 text-gray-900'">
                                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
                                    fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                                    stroke-linejoin="round">
                                    <path d="M3 2v6h6"></path>
                                    <path d="M3 13a9 9 0 1 0 3-7.7L3 8"></path>
                                </svg>
                                <span>重新开始</span>
                            </button>
                        </div>
                    </div>

                    <!-- 对话历史记录 -->
                    <div class="flex-1 overflow-y-auto p-4 space-y-4" ref="messagesContainer">
                        <!-- 欢迎消息 -->
                        <div v-if="messages.length === 0 && currentStep >= 5"
                            class="flex flex-col items-center justify-center h-full">
                            <div class="text-center p-6 rounded-lg" :class="isDarkMode ? 'bg-zinc-800' : 'bg-gray-100'">
                                <h3 class="text-lg font-medium mb-2"
                                    :class="isDarkMode ? 'text-zinc-100' : 'text-gray-900'">文档已上传成功</h3>
                                <p class="mb-4" :class="isDarkMode ? 'text-zinc-400' : 'text-gray-600'">
                                    您可以开始与文档处理Agent交流，提出您的需求</p>
                                <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                                    <div v-for="(suggestion, index) in suggestions" :key="index"
                                        @click="sendMessage(suggestion)"
                                        class="p-2 rounded cursor-pointer text-left transition-colors"
                                        :class="isDarkMode ? 'bg-zinc-700 hover:bg-zinc-600' : 'bg-white hover:bg-gray-200 border border-gray-200'">
                                        {{ suggestion }}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- 消息列表 -->
                        <div v-for="(message, index) in messages" :key="index" :class="[
                'flex flex-col',
                message.sender === 'user' ? 'items-end' : 'items-start',
                'mb-4' // 增加行间距
            ]">
                            <!-- 时间戳 -->
                            <div class="text-xs opacity-60 mb-1"
                                :class="isDarkMode ? 'text-zinc-500' : 'text-gray-500'">
                                {{ formatTimestamp(message.timestamp) }}
                            </div>

                            <div :class="[
                'max-w-3/4 rounded-lg p-3',
                message.sender === 'user'
                    ? isDarkMode ? 'bg-blue-600 text-white' : 'bg-blue-500 text-white'
                    : isDarkMode ? 'bg-zinc-800' : 'bg-gray-100'
            ]">
                                <div class="whitespace-pre-wrap" v-html="formatMessage(message.content)"></div>
                            </div>
                        </div>

                        <!-- 加载指示器 -->
                        <div v-if="isLoading" class="flex justify-start">
                            <div class="flex items-center space-x-2 p-3 rounded-lg"
                                :class="isDarkMode ? 'bg-zinc-800' : 'bg-gray-100'">
                                <div class="flex space-x-1">
                                    <div class="w-2 h-2 rounded-full animate-bounce"
                                        :class="isDarkMode ? 'bg-zinc-400' : 'bg-gray-500'" style="animation-delay: 0s">
                                    </div>
                                    <div class="w-2 h-2 rounded-full animate-bounce"
                                        :class="isDarkMode ? 'bg-zinc-400' : 'bg-gray-500'"
                                        style="animation-delay: 0.2s"></div>
                                    <div class="w-2 h-2 rounded-full animate-bounce"
                                        :class="isDarkMode ? 'bg-zinc-400' : 'bg-gray-500'"
                                        style="animation-delay: 0.4s"></div>
                                </div>
                                <span class="text-sm"
                                    :class="isDarkMode ? 'text-zinc-400' : 'text-gray-500'">Agent正在思考...</span>
                            </div>
                        </div>
                    </div>

                    <!-- 输入区域 -->
                    <div class="border-t p-4" :class="isDarkMode ? 'border-zinc-700' : 'border-gray-200'">
                        <div class="flex space-x-2">
                            <textarea v-model="userInput" @keydown.enter.prevent="handleEnterKey"
                                placeholder="输入您的问题或需求..."
                                class="flex-1 resize-none rounded-lg p-3 focus:outline-none focus:ring-1"
                                :class="isDarkMode ? 'bg-zinc-700 text-zinc-100 focus:ring-zinc-600' : 'bg-gray-100 text-gray-900 focus:ring-blue-500'"
                                rows="2"></textarea>
                            <button @click="sendMessage()" :disabled="isLoading || !userInput.trim()"
                                class="self-end p-3 rounded-lg transition-colors flex items-center justify-center"
                                :class="[
                isDarkMode
                    ? isLoading || !userInput.trim() ? 'bg-zinc-800 text-zinc-600' : 'bg-blue-600 hover:bg-blue-700 text-white'
                    : isLoading || !userInput.trim() ? 'bg-gray-200 text-gray-400' : 'bg-blue-500 hover:bg-blue-600 text-white'
                ]">
                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
                                    fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                                    stroke-linejoin="round">
                                    <line x1="22" y1="2" x2="11" y2="13"></line>
                                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 隐藏的文件上传输入 -->
        <input type="file" ref="fileInput" @change="handleFileUpload" accept=".docx" class="hidden" />
        <!-- 隐藏的格式要求上传输入 -->
        <input type="file" ref="formatInput" @change="handleFormatUpload" accept=".json" class="hidden" />
    </div>
</template>

<script setup>
import { ref, computed, onMounted, inject, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'

// 获取主题模式和通知函数
const isDarkMode = inject('isDarkMode', ref(true))
const showNotification = inject('showNotification', null)
const updateChatHistory = inject('updateChatHistory', null)

// 路由
const router = useRouter()
const route = useRoute()

// 文件上传相关
const fileInput = ref(null)
const formatInput = ref(null)
const hasUploadedFile = ref(false)
const hasUploadedFormat = ref(false)
const uploadedFile = ref(null)
const uploadedFileName = ref('')

// 对话相关
const messagesContainer = ref(null)
const userInput = ref('')
const messages = ref([])
const adviceMessages = ref([])
const isLoading = ref(false)
// 是否需要内容修改建议
const isneedAdvice = ref(flase)
// 当前处理的文档
const currentDocumentPath = ref('')
// 当前配置文件
const currentConfigPath = ref('')
// 处理步骤
const currentStep = ref(0)
const processingComplete = ref(false)
const processingSteps = ref([
    { id: 1, title: '上传文档', description: '上传需要检查格式的文档', status: 'pending' },
    { id: 2, title: '上传格式要求', description: '上传格式要求文档或使用默认格式', status: 'pending' },
    { id: 3, title: '检查格式规范', description: '根据格式要求检查文档格式', status: 'pending' },
    { id: 4, title: '生成分析报告', description: '生成格式检查报告', status: 'pending' }
])

// 格式错误信息
const formatErrors = ref(null)

// 对话建议
const suggestions = [
    '请分析文档中的格式问题',
    '如何修复文档中的格式错误？',
    '生成格式修正报告',
    '帮我优化文档的整体格式'
]

// 监听消息变化，自动滚动到底部
watch(messages, () => {
    nextTick(() => {
        if (messagesContainer.value) {
            messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
        }
    })
}, { deep: true })

// 格式化时间戳
function formatTimestamp(timestamp) {
    if (!timestamp) return ''
    const date = new Date(timestamp)
    return date.toLocaleTimeString()
}

// 格式化消息内容（可以处理换行、链接等）
function formatMessage(content) {
    if (!content) return ''
    // 将换行符转换为<br>
    return content.replace(/\n/g, '<br>')
}

// 触发文件上传
function triggerFileUpload() {
    fileInput.value.click()
}

// 触发格式要求上传
function triggerFormatUpload() {
    formatInput.value.click()
}

// 处理文件上传
async function handleFileUpload(event) {
    const file = event.target.files[0]
    if (!file) return

    uploadedFileName.value = file.name
    const formData = new FormData()
    formData.append('file', file)

    try {
        showNotification('info', '文件上传中', '正在上传文档，请稍候...', 0)

        // 调用 Flask 后端 API
        const response = await axios.post('/api/upload-files', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        })

        // 检查后端返回的成功状态
        if (response.data.success) {
            uploadedFile.value = file
            hasUploadedFile.value = true
            processingSteps.value[0].status = 'completed'
            currentStep.value = 1
            // 设置当前处理文档
            currentDocumentPath.value = response.data.file.path
            // TODO:侧边消息记录

            showNotification('success', '上传成功', `文件 "${file.name}" 已成功上传`, 3000)
            //继续进行下一步
            Processing(currentDocumentPath.value)

        } else {
            throw new Error(response.data.message || '上传失败')
        }
    } catch (error) {
        console.error('上传文件时出错:', error)
        showNotification('error', '上传失败', `上传文件时出错: ${error.message || error}`, 5000)
        processingSteps.value[0].status = 'error'
    }

    event.target.value = '' // 清空 input
}
// 处理格式文件上传
async function handleFormatUpload(event) {
    const file = event.target.files[0]
    if (!file) return

    const formData = new FormData()
    formData.append('format_file', file)

    try {
        showNotification('info', '格式要求上传中', '正在上传格式要求，请稍候...', 0)
        // 调用 Flask 后端 API
        const response = await axios.post('/api/upload-format', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        })
        if(response.data.success) {
            hasUploadedFormat.value = true
            currentConfigPath.value = response.data.file.file_path
            processingSteps.value[1].status = 'completed'
            currentStep.value = 2
            showNotification('success', '上传成功', `格式要求 "${file.name}" 已成功上传`, 3000)
        } else {
            throw new Error(response.data.message || '上传失败')
        }
    }
    catch (error) {
        console.error('上传格式文件时出错:', error)
        showNotification('error', '上传失败', `上传格式文件时出错: ${error.message || error}`, 5000)
        processingSteps.value[1].status = 'error'
    }
}
// 处理流程
function Processing() {
    //发送给后端处理
    try {
        //showNotification('info', '文档处理中', '正在处理文档，请稍候...', 0)
        // 是否需要内容修改建议，调用 Flask 后端 API
        if (isneedAdvice){
            const response = axios.post('/api/get-advice', {
            doc_path: currentDocumentPath.value
            })
            // 后端返回的处理结果
            if (response.data.success) {
                //格式修改建议
                adviceMessages.value.append(response.data.result)
            }
        }
        // 解析文档段落
        const response = axios.post('/api/check-format', {
            doc_path: currentDocumentPath.value,
            config_path: currentConfig.value
        })
        // 后端返回的处理结果
        if (response.data.success) {
            // 格式错误信息
            processingSteps.value[2].status = 'completed'
            currentStep.value = 3
        } else {
            throw new Error(response.data.message || '解析失败')
        }
        
    }
    catch (error) {
        console.error('处理文档时出错:', error)
        showNotification('error', '处理失败', `处理文档时出错: ${error.message || error}`, 5000)
        processingSteps.value[0].status = 'error'
    }
    // 模拟格式要求上传完成
    setTimeout(() => {
        processingSteps.value[1].status = 'completed'
        currentStep.value = 2

        // 模拟文档解析
        processingSteps.value[2].status = 'in_progress'
        setTimeout(() => {
            processingSteps.value[2].status = 'completed'

            // 模拟格式检查
            processingSteps.value[3].status = 'in_progress'
            setTimeout(() => {
                processingSteps.value[3].status = 'completed'

                // 模拟报告生成
                processingSteps.value[4].status = 'in_progress'
                setTimeout(() => {
                    processingSteps.value[4].status = 'completed'
                    processingComplete.value = true
                    currentStep.value = 5

                    // 添加系统欢迎消息
                    messages.value.push({
                        content: '文档格式分析已完成，我发现了一些格式问题。您可以询问我关于文档格式的任何问题，或者请我帮您修复这些问题。',
                        sender: 'system',
                        timestamp: new Date()
                    })

                    showNotification('success', '处理完成', '文档格式分析已完成', 3000)
                }, 1000)
            }, 1000)
        }, 1000)
    }, 1000)
}

// 处理回车键
function handleEnterKey(e) {
    if (!e.shiftKey) {
        sendMessage()
    }
}

// 发送消息
function sendMessage(suggestionText) {
    const messageText = suggestionText || userInput.value.trim()
    if (!messageText) return

    // 添加用户消息
    messages.value.push({
        content: messageText,
        sender: 'user',
        timestamp: new Date()
    })

    // 清空输入框
    userInput.value = ''

    // 显示加载状态
    isLoading.value = true

    // 模拟AI回复
    setTimeout(() => {
        isLoading.value = false

        // 根据用户消息生成回复
        let response
        if (messageText.includes('格式问题')) {
            response = `我分析了您的文档，发现了${formatErrors.value.length}个格式问题：\n\n${formatErrors.value.map((error, index) => `${index + 1}. ${error.message} (${error.location})`).join('\n')}\n\n您想要我帮您修复这些问题吗？`
        } else if (messageText.includes('修复') || messageText.includes('修正')) {
            response = '我可以帮您修复文档中的格式问题。修复过程将自动应用正确的格式规范，您可以在完成后下载修正后的文档。要开始修复，请点击上方的"下载修正文档"按钮。'
        } else if (messageText.includes('报告')) {
            response = '我已经生成了格式分析报告，您可以通过点击上方的"下载报告"按钮获取详细的格式分析结果。报告中包含了所有格式问题的详细描述和修正建议。'
        } else {
            response = `关于"${messageText}"的问题，我可以帮您分析文档中的格式问题并提供修正建议。请问您具体需要了解哪方面的格式问题？`
        }

        // 添加系统回复
        messages.value.push({
            content: response,
            sender: 'system',
            timestamp: new Date()
        })
    }, 1000)
}

// 下载报告
function downloadReport() {
    showNotification('info', '下载中', '正在准备下载报告...', 3000)
    // 实际项目中应该调用后端API
    // window.location.href = '/api/download-report?doc_path=' + encodeURIComponent(uploadedFileName.value)
}

// 下载修正文档
function downloadMarkedDocument() {
    showNotification('info', '下载中', '正在准备下载修正后的文档...', 3000)
    // 实际项目中应该调用后端API
    // window.location.href = '/api/download-marked-document?doc_path=' + encodeURIComponent(uploadedFileName.value)
}

// 重置处理流程
function resetProcess() {
    currentStep.value = 0
    uploadedFile.value = null
    hasUploadedFile.value = false
    uploadedFileName.value = ''
    messages.value = []
    formatErrors.value = null
    processingComplete.value = false

    // 重置所有步骤状态
    processingSteps.value.forEach(step => {
        step.status = 'pending'
    })

    showNotification('info', '已重置', '处理流程已重置，您可以上传新的文档', 3000)
}

// 使用默认格式
function useDefaultFormat() {
    hasUploadedFormat.value = true;
    processingSteps.value[1].status = 'completed';
    currentStep.value = 2;
    showNotification('success', '使用默认格式', '使用默认格式进行处理', 3000);
}
</script>

<style>
/* 自定义滚动条样式 */
.scrollbar-thin::-webkit-scrollbar {
    width: 4px;
}

.scrollbar-thin::-webkit-scrollbar-track {
    background: transparent;
}

.scrollbar-thin::-webkit-scrollbar-thumb {
    background-color: rgba(59, 130, 246, 0.5);
    border-radius: 2px;
}

.scrollbar-thin::-webkit-scrollbar-thumb:hover {
    background-color: rgba(59, 130, 246, 0.8);
}

/* 消息动画 */
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.flex-1>div {
    animation: fadeIn 0.3s ease-out forwards;
}
</style>