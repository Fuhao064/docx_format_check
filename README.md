# Scriptor - Intelligent Document Format Checker and Corrector

<div align="center">
  <img src="frontend/src/assets/favicon.png" alt="Scriptor Logo" width="120" height="120">
  <h1>Scriptor - Intelligent Document Format Checker and Corrector</h1>
  <p>Professional document format analysis and automatic correction solution</p>
</div>

## Project Introduction

Scriptor is an intelligent document format checking and correction tool specifically designed for academic papers, technical documents, and formal reports. The system utilizes advanced natural language processing technology and document analysis algorithms to automatically identify format issues in documents and provide correction suggestions or automatic fixes.

Whether you are a student, researcher, technical writer, or corporate user, Scriptor can help you ensure your documents comply with specific format specifications, enhance the professionalism and consistency of your documents, and save time on manual checking and format correction.

## Core Features

### 1. Automatic Format Detection

- Intelligently identifies format issues in documents, including fonts, paragraphs, headings, citations, etc.
- Supports checking against various format specifications, such as academic papers, technical reports, etc.
- Precisely locates problem areas and provides clear error descriptions

### 2. Custom Specification Checking

- Supports user-defined format specifications to meet different scenario requirements
- Flexible setting of checking rules through configuration files
- Supports saving and sharing custom specification templates

### 3. Detailed Analysis Reports

- Generates comprehensive format analysis reports, clearly marking all issues
- Provides problem severity grading to help users prioritize important issues
- Supports exporting analysis reports for sharing and archiving

### 4. One-Click Format Correction

- Automatically corrects format issues in documents while preserving original content
- Intelligently handles complex formats such as tables, images, formulas, etc.
- Supports batch correction of multiple issues to improve efficiency

### 5. Intelligent Paragraph Recognition

- Automatically identifies different paragraph types in documents (abstract, body text, citations, etc.)
- Applies corresponding format rules to different paragraph types
- Supports custom paragraph types and rules

### 6. Interactive Modification Suggestions

- Provides intelligent modification suggestions that users can selectively apply
- Real-time preview of modification effects for comparison and selection
- Supports undo and redo operations to ensure safe modifications

## Technical Features

### 1. Based on Large Language Models

- Utilizes advanced AI models for document analysis and processing
- Supports various large language models such as Qwen, DeepSeek, etc.
- Continuously updates and optimizes models to improve analysis accuracy

### 2. Precise Document Structure Analysis

- In-depth analysis of document structure, accurately identifying each content section
- Supports complex document formats such as multi-level headings, cross-references, etc.
- Intelligently handles special elements such as tables, images, formulas, etc.

### 3. Intelligent Paragraph Type Recognition

- Automatically recognizes different types of paragraphs and applies appropriate format rules
- Intelligent classification based on content and context
- Supports manual adjustment and correction of recognition results

### 4. Efficient Format Correction Algorithms

- Quickly and accurately corrects various format issues
- Optimized performance for processing large documents
- Supports batch processing of multiple documents

### 5. User-Friendly Interface

- Intuitive and easy-to-use web interface with drag-and-drop upload and real-time preview
- Responsive design, adapting to different devices and screen sizes
- Supports dark mode and custom themes

### 6. Secure Document Processing

- Local document processing to protect user privacy and data security
- Supports document encryption and secure storage
- Complies with data protection and privacy regulation requirements

## Installation and Usage

### Environment Requirements

- Python 3.8+
- Node.js 14+
- npm 6+

### Backend Installation

```bash
# Clone repository
git clone https://github.com/yourusername/Scriptor.git
cd Scriptor

# Install backend dependencies
pip install -r requirements.txt

# Start backend service
cd backend
python app.py
```

### Frontend Installation

```bash
# Install frontend dependencies
cd frontend
npm install

# Start development server
npm run dev

# Build production version
npm run build
```

### Create keys.json in the project root directory

Example:
{
  "deepseek-r1": {
    "base_url":"https://dashscope.aliyuncs.com/compatible-mode/v1",
    "api_key":"YOUR-API-KEY",
    "model_name": "deepseek-r1"
  }
}

### Usage Instructions

1. Access `http://localhost:3000` in your browser (frontend development server)
2. Upload the Word document (.docx format) you want to check
3. The system will automatically analyze the document format and display the results
4. View the analysis report to understand the format issues in the document
5. Choose to automatically correct the document format or download a marked document
6. Download the corrected document

## System Architecture

Scriptor adopts a front-end and back-end separated architecture design:

### Frontend Architecture

- **Framework**: Vue.js 3 + Vite
- **UI Library**: Tailwind CSS + HeadlessUI
- **State Management**: Pinia
- **Router**: Vue Router
- **HTTP Client**: Axios
- **Real-time Communication**: Socket.IO Client
- **Local Storage**: IndexedDB (Dexie.js)

### Backend Architecture

- **Web Framework**: Flask
- **Real-time Communication**: Flask-SocketIO
- **Document Processing**: python-docx
- **AI Engine**: Integration of various large language models
- **Format Checking**: Custom checker modules
- **Format Correction**: Custom editor modules

### Core Modules

- **FormatAgent**: Responsible for document format analysis and specification checking
- **EditorAgent**: Responsible for document content editing and format correction
- **AdviceAgent**: Provides intelligent modification suggestions
- **CommunicateAgent**: Handles user queries and interactions

## Configuration Instructions

The system is configured through the `config.json` file, supporting customization of the following:

- Document page settings (paper size, margins, etc.)
- Paragraph formats (line spacing, alignment, indentation, etc.)
- Font settings (font family, size, style, etc.)
- Heading formats (level, style, numbering, etc.)
- Citation formats (standard, style, etc.)
- Table and image formats (captions, numbering, style, etc.)
- Required paragraph requirements (abstract, keywords, conclusion, etc.)


## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details

## Contact Us

If you have any questions or suggestions, please contact me through:

- Submit a GitHub Issue

---
