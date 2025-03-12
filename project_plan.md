# Excel到Word API文档转换应用 - 项目计划

## 项目概述

开发一个基于Web的应用，允许用户上传Excel文件，通过Python后端进行处理并转换为Word格式的API文档。应用将采用Vue.js作为前端框架，FastAPI作为后端框架，并提供对话式界面显示转换进度。

## 技术栈

### 前端
- Vue.js 3
- Tailwind CSS
- Axios
- vue-office (用于文档预览)

### 后端
- FastAPI
- Python 3.9+
- python-docx
- pandas
- openpyxl
- WebSockets (用于实时进度更新)

## 项目结构

```
DocxTest/
├── frontend/                # Vue.js前端应用
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/      # Vue组件
│   │   ├── App.vue          # 主应用组件
│   │   └── main.js          # 入口文件
│   ├── package.json
│   └── vite.config.js       # Vite配置
├── backend/                 # FastAPI后端应用
│   ├── app.py               # 主应用入口
│   ├── format_agent.py      # 已有的格式代理
│   ├── format_checker.py    # 已有的格式检查器
│   ├── docx_parser.py       # 已有的文档解析器
│   └── extract_para_info.py # 已有的段落信息提取
├── uploads/                 # 上传文件存储目录
└── requirements.txt         # 项目依赖
```

## 开发计划

### 1. 后端开发

1. 将现有的Flask应用转换为FastAPI应用
   - 创建FastAPI应用实例
   - 配置CORS和静态文件服务
   - 实现文件上传端点

2. 集成现有的文档处理功能
   - 整合format_checker.py中的格式检查功能
   - 整合format_agent.py中的LLM集成

3. 实现WebSocket支持
   - 添加WebSocket端点用于实时进度更新
   - 实现分步处理逻辑并发送进度更新

### 2. 前端开发

1. 创建Vue.js项目
   - 使用Vite初始化项目
   - 配置Tailwind CSS

2. 实现UI组件
   - 顶部标题栏和下载按钮
   - 对话式界面组件
   - 文件上传组件
   - 进度显示组件
   - 文档预览组件

3. 实现与后端的通信
   - 使用Axios进行HTTP请求
   - 实现WebSocket连接获取实时进度

### 3. 集成与测试

1. 前后端集成
   - 连接前端UI与后端API
   - 测试文件上传和处理流程

2. 功能测试
   - 测试文档格式检查功能
   - 测试进度显示功能
   - 测试文档预览功能

3. UI/UX优化
   - 实现暗色主题
   - 优化响应式布局
   - 添加加载动画和过渡效果

## 功能清单

1. 用户可以通过对话式界面上传Excel文件
2. 系统分析Excel文件并转换为Word文档
3. 实时显示处理进度和步骤
4. 提供Word文档预览功能
5. 允许下载生成的Word文档
6. 支持中文本地化
7. 提供暗色主题界面

## 下一步行动

1. 设置前端Vue.js项目
2. 将后端从Flask迁移到FastAPI
3. 实现基本的文件上传和处理功能