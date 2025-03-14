<template>
  <div class="p-6 max-w-4xl mx-auto">
    <div class="mb-6">
      <h1 class="text-2xl font-semibold mb-2">关于我</h1>
      <p class="text-zinc-400">了解文档格式检查与修正系统的背景</p>
    </div>
    
    <div class="bg-zinc-800 rounded-lg p-6 mb-6">
      <h2 class="text-xl font-semibold mb-4">系统介绍</h2>
      <p class="mb-4 text-zinc-300">
        文档格式检查与修正系统（Putain le format）是一款专为学术论文、技术文档和正式报告设计的格式检查与修正工具。
        系统利用先进的自然语言处理技术和文档分析算法，能够自动识别文档中的格式问题，并提供修正建议或自动修正。
      </p>
      
      <p class="mb-4 text-zinc-300">
        无论您是学生、研究人员、技术作者还是企业用户，本系统都能帮助您确保文档符合特定的格式规范，
        提高文档的专业性和一致性，节省手动检查和修正格式的时间。
      </p>
      
      <h3 class="text-lg font-semibold mt-6 mb-3">核心功能</h3>
      <ul class="list-disc pl-6 space-y-2 text-zinc-300">
        <li>自动检测文档格式问题</li>
        <li>根据自定义规范检查文档格式</li>
        <li>提供详细的格式分析报告</li>
        <li>一键修正文档格式</li>
        <li>支持多种格式规范模板</li>
        <li>可自定义格式规范</li>
      </ul>
      
      <h3 class="text-lg font-semibold mt-6 mb-3">技术特点</h3>
      <ul class="list-disc pl-6 space-y-2 text-zinc-300">
        <li>基于先进的大型语言模型</li>
        <li>精确的文档结构分析</li>
        <li>智能段落类型识别</li>
        <li>高效的格式修正算法</li>
        <li>用户友好的界面设计</li>
        <li>安全的文档处理机制</li>
      </ul>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
      <div class="bg-zinc-800 rounded-lg p-6">
        <h2 class="text-xl font-semibold mb-4">版本信息</h2>
        <div class="space-y-2">
          <div class="flex justify-between">
            <span class="text-zinc-400">系统版本</span>
            <span class="text-zinc-300">v1.0.0</span>
          </div>
          <div class="flex justify-between">
            <span class="text-zinc-400">发布日期</span>
            <span class="text-zinc-300">2023年12月15日</span>
          </div>
          <div class="flex justify-between">
            <span class="text-zinc-400">最后更新</span>
            <span class="text-zinc-300">2024年3月10日</span>
          </div>
          <div class="flex justify-between">
            <span class="text-zinc-400">许可证</span>
            <span class="text-zinc-300">MIT</span>
          </div>
        </div>
      </div>
      
      <div class="bg-zinc-800 rounded-lg p-6">
        <h2 class="text-xl font-semibold mb-4">技术栈</h2>
        <div class="grid grid-cols-2 gap-3">
          <div class="bg-zinc-700/50 rounded-md p-3 flex items-center">
            <span class="text-indigo-400 mr-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="16 18 22 12 16 6"></polyline>
                <polyline points="8 6 2 12 8 18"></polyline>
              </svg>
            </span>
            <span class="text-zinc-300">Vue.js</span>
          </div>
          
          <div class="bg-zinc-700/50 rounded-md p-3 flex items-center">
            <span class="text-indigo-400 mr-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20.24 12.24a6 6 0 0 0-8.49-8.49L5 10.5V19h8.5z"></path>
                <line x1="16" y1="8" x2="2" y2="22"></line>
                <line x1="17.5" y1="15" x2="9" y2="15"></line>
              </svg>
            </span>
            <span class="text-zinc-300">Tailwind CSS</span>
          </div>
          
          <div class="bg-zinc-700/50 rounded-md p-3 flex items-center">
            <span class="text-indigo-400 mr-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
              </svg>
            </span>
            <span class="text-zinc-300">Flask</span>
          </div>
          
          <div class="bg-zinc-700/50 rounded-md p-3 flex items-center">
            <span class="text-indigo-400 mr-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
                <line x1="12" y1="22.08" x2="12" y2="12"></line>
              </svg>
            </span>
            <span class="text-zinc-300">大型语言模型</span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="bg-zinc-800 rounded-lg p-6">
      <h2 class="text-xl font-semibold mb-4">版权声明</h2>
      <p class="text-zinc-300">
        © 2023-2024 Putain le format 开发者。保留所有权利。
      </p>
      <p class="mt-2 text-zinc-400 text-sm">
        本系统仅用于文档格式检查与修正，不存储或使用用户上传的文档内容用于其他目的。
        用户对上传文档的内容负有完全责任，系统开发者不对用户上传的文档内容承担任何法律责任。
      </p>
    </div>
  </div>
</template>

<script setup>
// 关于页面不需要特殊的逻辑
</script> 