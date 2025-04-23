# Scriptor

<div align="center">
  <img src="frontend/src/assets/favicon.png" alt="Scriptor Logo" width="120" height="120">
  <h1>Scriptor - 智能文档格式检查与修正系统</h1>
  <p>专业的文档格式分析与自动修正解决方案</p>
</div>

[English](#english) | [中文](#中文)

---

<a name="中文"></a>
## 中文

### 项目介绍

Scriptor 是一款专为学术论文、技术文档和正式报告设计的智能文档格式检查与修正工具。系统利用先进的自然语言处理技术和文档分析算法，能够自动识别文档中的格式问题，并提供修正建议或自动修正。

无论您是学生、研究人员、技术作者还是企业用户，Scriptor 都能帮助您确保文档符合特定的格式规范，提高文档的专业性和一致性，节省手动检查和修正格式的时间。

### 核心功能

- **自动格式检测**：智能识别文档中的格式问题，包括字体、段落、标题、引用等
- **自定义规范检查**：根据用户自定义的格式规范检查文档
- **详细分析报告**：生成全面的格式分析报告，清晰标记所有问题
- **一键格式修正**：自动修正文档中的格式问题，保留原有内容
- **多种格式模板**：支持多种常见的学术和商业文档格式规范
- **智能段落识别**：自动识别文档中的不同段落类型（摘要、正文、引用等）
- **交互式修改建议**：提供智能的修改建议，用户可选择性应用

### 技术特点

- **基于大型语言模型**：利用先进的AI模型进行文档分析和处理
- **精确的文档结构分析**：深入分析文档结构，准确识别各部分内容
- **智能段落类型识别**：自动识别不同类型的段落，应用相应的格式规则
- **高效的格式修正算法**：快速准确地修正各类格式问题
- **用户友好的界面**：直观易用的Web界面，支持拖放上传和实时预览
- **安全的文档处理**：本地处理文档，保护用户隐私和数据安全

### 安装与使用

#### 环境要求

- Python 3.8+
- Node.js 14+
- npm 6+

#### 后端安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/Scriptor.git
cd Scriptor

# 安装后端依赖
pip install -r requirements.txt

# 启动后端服务
cd backend
python app.py
```

#### 前端安装

```bash
# 安装前端依赖
cd frontend
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

#### 使用方法

1. 在浏览器中访问 `http://localhost:3000`（前端开发服务器）
2. 上传需要检查的Word文档（.docx格式）
3. 系统会自动分析文档格式并显示结果
4. 查看分析报告，了解文档中存在的格式问题
5. 选择自动修正文档格式或下载带有标记的文档
6. 下载修正后的文档

### 系统架构

Scriptor 采用前后端分离的架构设计：

- **前端**：Vue.js 3 + Vite + Tailwind CSS，提供现代化的用户界面
- **后端**：Flask + SocketIO，处理文档分析和格式修正
- **AI引擎**：集成多种大型语言模型，支持文档分析和智能建议
- **数据存储**：客户端使用IndexedDB存储用户数据和段落管理器

### 贡献指南

我们欢迎各种形式的贡献，包括但不限于：

- 提交问题和功能请求
- 改进文档
- 提交代码修复或新功能
- 分享使用经验和案例

请遵循以下步骤：

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开一个 Pull Request

### 许可证

本项目采用 Apache 2.0 许可证 - 详情请参见 [LICENSE](LICENSE) 文件

---

<a name="english"></a>
## English

### Project Introduction

Scriptor is an intelligent document format checking and correction tool designed specifically for academic papers, technical documents, and formal reports. The system utilizes advanced natural language processing technology and document analysis algorithms to automatically identify format issues in documents and provide correction suggestions or automatic fixes.

Whether you are a student, researcher, technical writer, or corporate user, Scriptor can help you ensure that your documents comply with specific format specifications, enhance the professionalism and consistency of your documents, and save time on manual format checking and correction.

### Core Features

- **Automatic Format Detection**: Intelligently identifies format issues in documents, including fonts, paragraphs, headings, citations, etc.
- **Custom Specification Checking**: Checks documents according to user-defined format specifications
- **Detailed Analysis Reports**: Generates comprehensive format analysis reports, clearly marking all issues
- **One-Click Format Correction**: Automatically corrects format issues in documents while preserving original content
- **Multiple Format Templates**: Supports various common academic and business document format specifications
- **Intelligent Paragraph Recognition**: Automatically identifies different paragraph types in documents (abstract, body, citations, etc.)
- **Interactive Modification Suggestions**: Provides intelligent modification suggestions that users can selectively apply

### Technical Features

- **Based on Large Language Models**: Utilizes advanced AI models for document analysis and processing
- **Precise Document Structure Analysis**: In-depth analysis of document structure, accurately identifying various content sections
- **Intelligent Paragraph Type Recognition**: Automatically recognizes different types of paragraphs and applies appropriate format rules
- **Efficient Format Correction Algorithms**: Quickly and accurately corrects various format issues
- **User-Friendly Interface**: Intuitive and easy-to-use web interface, supporting drag-and-drop uploads and real-time previews
- **Secure Document Processing**: Processes documents locally, protecting user privacy and data security

### Installation and Usage

#### Requirements

- Python 3.8+
- Node.js 14+
- npm 6+

#### Backend Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/Scriptor.git
cd Scriptor

# Install backend dependencies
pip install -r requirements.txt

# Start the backend service
cd backend
python app.py
```

#### Frontend Installation

```bash
# Install frontend dependencies
cd frontend
npm install

# Start the development server
npm run dev

# Build for production
npm run build
```

#### How to Use

1. Access `http://localhost:3000` in your browser (frontend development server)
2. Upload the Word document (.docx format) you want to check
3. The system will automatically analyze the document format and display the results
4. View the analysis report to understand the format issues in the document
5. Choose to automatically correct the document format or download a marked document
6. Download the corrected document

### System Architecture

Scriptor adopts a front-end and back-end separated architecture design:

- **Frontend**: Vue.js 3 + Vite + Tailwind CSS, providing a modern user interface
- **Backend**: Flask + SocketIO, handling document analysis and format correction
- **AI Engine**: Integrates various large language models, supporting document analysis and intelligent suggestions
- **Data Storage**: Client-side uses IndexedDB to store user data and paragraph managers

### Contribution Guidelines

We welcome contributions of all forms, including but not limited to:

- Submitting issues and feature requests
- Improving documentation
- Submitting code fixes or new features
- Sharing usage experiences and case studies

Please follow these steps:

1. Fork this repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details
