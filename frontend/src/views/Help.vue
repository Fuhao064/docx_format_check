<template>
  <div class="min-h-screen p-6 overflow-y-auto" :class="{ 'bg-white text-black': !isDarkMode, 'bg-zinc-950 text-zinc-100': isDarkMode }">
    <!-- 头部 -->
    <div class="max-w mx-auto mb-8">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-3">帮助中心</h1>
      <p class="text-gray-600 dark:text-gray-400 text-lg">了解如何使用文档格式检查与修正系统</p>
    </div>

    <!-- 主要内容 -->
    <div class="max-w mx-auto space-y-6">
      <!-- 快速入门卡片 -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow">
        <div class="prose max-w-none">
          <h2 class="text-2xl font-semibold text-gray-900 dark:text-gray-100">快速入门</h2>
          <p class="text-gray-600 dark:text-gray-400">欢迎使用文档格式检查与修正系统。本系统可以帮助您检查和修正文档的格式，确保文档符合特定的格式规范。</p>

          <div class="mt-6 space-y-6">
            <div>
              <h3 class="text-xl font-medium text-gray-900 dark:text-gray-100">基本使用流程</h3>
              <ol class="mt-2 list-decimal list-inside space-y-2 text-gray-700 dark:text-gray-300">
                <li>在主页面上传您需要检查的 Word 文档（.docx 格式）</li>
                <li>系统会自动分析文档的格式</li>
                <li>查看分析结果，了解文档中存在的格式问题</li>
                <li>选择自动修正文档格式</li>
                <li>下载修正后的文档</li>
              </ol>
            </div>

            <div>
              <h3 class="text-xl font-medium text-gray-900 dark:text-gray-100">功能说明</h3>
              <div class="mt-4 space-y-4">
                <div>
                  <h4 class="font-medium text-gray-900 dark:text-gray-100">文档上传与分析</h4>
                  <p class="text-gray-600 dark:text-gray-400">通过点击上传按钮或拖放文件的方式上传 Word 文档，系统将自动分析并显示结果。</p>
                </div>
                <div>
                  <h4 class="font-medium text-gray-900 dark:text-gray-100">格式配置</h4>
                  <p class="text-gray-600 dark:text-gray-400">在"格式"页面调整纸张设置、标题样式和正文格式等配置。</p>
                </div>
                <div>
                  <h4 class="font-medium text-gray-900 dark:text-gray-100">模型管理</h4>
                  <p class="text-gray-600 dark:text-gray-400">在"模型"页面管理AI模型，包括查看、选择和添加新模型。</p>
                </div>
              </div>
            </div>

            <div>
              <h3 class="text-xl font-medium text-gray-900 dark:text-gray-100">常见问题</h3>
              <div class="mt-4 space-y-4">
                <div>
                  <h4 class="font-medium text-gray-900 dark:text-gray-100">支持哪些文档格式？</h4>
                  <p class="text-gray-600 dark:text-gray-400">目前仅支持 .docx 格式的 Microsoft Word 文档。</p>
                </div>
                <div>
                  <h4 class="font-medium text-gray-900 dark:text-gray-100">如何修改格式配置？</h4>
                  <p class="text-gray-600 dark:text-gray-400">在"格式"页面通过表单或编辑 JSON 文件修改配置后保存。</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 联系卡片 -->
      <div class="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow">
        <h2 class="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">联系我们</h2>
        <p class="text-gray-600 dark:text-gray-400 mb-4">如有任何问题或建议，请通过以下方式联系：</p>
        <div class="flex items-center space-x-3 text-gray-700 dark:text-gray-300 hover:text-blue-600 transition-colors">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
            <polyline points="22,6 12,13 2,6"></polyline>
          </svg>
          <a href="mailto:fuhaolv@outlook.com" class="font-medium">fuhaolv@outlook.com</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 无需特殊逻辑
</script>

<style scoped>
/* 可选：添加自定义动画 */
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

.prose {
  animation: fadeIn 0.5s ease-out;
}
</style>