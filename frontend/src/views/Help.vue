<template>
  <div class="p-6 max-w-4xl mx-auto">
    <div class="mb-6">
      <h1 class="text-2xl font-semibold mb-2">帮助中心</h1>
      <p class="text-zinc-400">了解如何使用文档格式检查与修正系统</p>
    </div>
    
    <div class="bg-zinc-800 rounded-lg p-6 mb-6">
      <div class="prose prose-invert max-w-none">
        <h2>快速入门</h2>
        <p>欢迎使用文档格式检查与修正系统。本系统可以帮助您检查和修正文档的格式，确保文档符合特定的格式规范。</p>
        
        <h3>基本使用流程</h3>
        <ol>
          <li>在主页面上传您需要检查的 Word 文档（.docx 格式）</li>
          <li>系统会自动分析文档的格式</li>
          <li>您可以查看分析结果，了解文档中存在的格式问题</li>
          <li>根据需要，您可以选择自动修正文档格式</li>
          <li>下载修正后的文档</li>
        </ol>
        
        <h3>功能说明</h3>
        <h4>文档上传与分析</h4>
        <p>在主页面，您可以通过点击上传按钮或拖放文件的方式上传 Word 文档。上传完成后，系统会自动分析文档格式，并显示分析结果。</p>
        
        <h4>格式配置</h4>
        <p>在"格式"页面，您可以查看和修改格式配置。系统会根据这些配置来检查和修正文档格式。您可以根据需要调整以下设置：</p>
        <ul>
          <li>纸张设置：包括纸张大小、方向和页边距</li>
          <li>标题设置：包括字体、大小、样式等</li>
          <li>正文设置：包括字体、大小、行间距等</li>
        </ul>
        
        <h4>模型管理</h4>
        <p>在"模型"页面，您可以管理用于文档分析的 AI 模型。您可以：</p>
        <ul>
          <li>查看可用的模型</li>
          <li>选择要使用的模型</li>
          <li>添加新的模型</li>
          <li>删除不需要的模型</li>
        </ul>
        
        <h3>常见问题</h3>
        <h4>支持哪些文档格式？</h4>
        <p>目前系统仅支持 Microsoft Word 文档（.docx 格式）。</p>
        
        <h4>如何修改格式配置？</h4>
        <p>在"格式"页面，您可以通过表单界面修改各项配置，也可以直接编辑 JSON 格式的配置文件。修改完成后，点击"保存配置"按钮即可。</p>
        
        <h4>如何添加新的模型？</h4>
        <p>在"模型"页面，填写模型名称、API 基础 URL、API Key 和模型标识符，然后点击"添加模型"按钮即可。</p>
        
        <h4>文档分析需要多长时间？</h4>
        <p>文档分析的时间取决于文档的大小和复杂度，以及所选模型的处理速度。通常情况下，分析一个中等大小的文档需要几秒到几十秒不等。</p>
      </div>
    </div>
    
    <div class="bg-zinc-800 rounded-lg p-6">
      <h2 class="text-xl font-semibold mb-4">联系我们</h2>
      <p class="mb-4">如果您在使用过程中遇到任何问题，或者有任何建议和反馈，请通过以下方式联系我们：</p>
      
      <div class="flex items-center space-x-2 text-zinc-400">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
          <polyline points="22,6 12,13 2,6"></polyline>
        </svg>
        <span>support@example.com</span>
      </div>
    </div>
  </div>
</template>

<script setup>
// 帮助页面不需要特殊的逻辑
</script>

<style>
/* Tailwind Typography 样式 */
.prose {
  color: #e4e4e7;
  max-width: 65ch;
}

.prose h2 {
  color: white;
  font-weight: 600;
  margin-top: 2em;
  margin-bottom: 1em;
  font-size: 1.5em;
}

.prose h3 {
  color: white;
  font-weight: 600;
  margin-top: 1.5em;
  margin-bottom: 0.75em;
  font-size: 1.25em;
}

.prose h4 {
  color: white;
  font-weight: 600;
  margin-top: 1.25em;
  margin-bottom: 0.5em;
  font-size: 1em;
}

.prose p {
  margin-top: 1em;
  margin-bottom: 1em;
}

.prose ul {
  margin-top: 1em;
  margin-bottom: 1em;
  padding-left: 1.5em;
  list-style-type: disc;
}

.prose ol {
  margin-top: 1em;
  margin-bottom: 1em;
  padding-left: 1.5em;
  list-style-type: decimal;
}

.prose li {
  margin-top: 0.5em;
  margin-bottom: 0.5em;
}
</style>