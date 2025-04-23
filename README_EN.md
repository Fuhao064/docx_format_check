# Scriptor - Intelligent Document Format Checking and Correction System

<div align="center">
  <img src="frontend/src/assets/favicon.png" alt="Scriptor Logo" width="120" height="120">
  <h1>Scriptor</h1>
  <p>Professional Document Format Analysis and Automatic Correction Solution</p>
</div>

## Project Introduction

Scriptor is an intelligent document format checking and correction tool designed specifically for academic papers, technical documents, and formal reports. The system utilizes advanced natural language processing technology and document analysis algorithms to automatically identify format issues in documents and provide correction suggestions or automatic fixes.

Whether you are a student, researcher, technical writer, or corporate user, Scriptor can help you ensure that your documents comply with specific format specifications, enhance the professionalism and consistency of your documents, and save time on manual format checking and correction.

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
- Intelligently handles complex formats, such as tables, images, formulas, etc.
- Supports batch correction of multiple issues, improving efficiency

### 5. Intelligent Paragraph Recognition

- Automatically identifies different paragraph types in documents (abstract, body, citations, etc.)
- Applies appropriate format rules for different paragraph types
- Supports custom paragraph types and rules

### 6. Interactive Modification Suggestions

- Provides intelligent modification suggestions that users can selectively apply
- Real-time preview of modification effects for comparison and selection
- Supports undo and redo operations to ensure safe modifications

## Technical Features

### 1. Based on Large Language Models

- Utilizes advanced AI models for document analysis and processing
- Supports various large language models, such as Qwen, DeepSeek, etc.
- Continuously updates and optimizes models to improve analysis accuracy

### 2. Precise Document Structure Analysis

- In-depth analysis of document structure, accurately identifying various content sections
- Supports complex document formats, such as multi-level headings, cross-references, etc.
- Intelligently handles special elements, such as tables, images, formulas, etc.

### 3. Intelligent Paragraph Type Recognition

- Automatically recognizes different types of paragraphs and applies appropriate format rules
- Intelligent classification based on content and context
- Supports manual adjustment and correction of recognition results by users

### 4. Efficient Format Correction Algorithms

- Quickly and accurately corrects various format issues
- Optimized performance for processing large documents
- Supports batch processing of multiple documents

### 5. User-Friendly Interface

- Intuitive and easy-to-use web interface, supporting drag-and-drop uploads and real-time previews
- Responsive design, adapting to different devices and screen sizes
- Supports dark mode and custom themes

### 6. Secure Document Processing

- Processes documents locally, protecting user privacy and data security
- Supports document encryption and secure storage
- Complies with data protection and privacy regulation requirements

## Installation and Usage

### Requirements

- Python 3.8+
- Node.js 14+
- npm 6+

### Backend Installation

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

### Frontend Installation

```bash
# Install frontend dependencies
cd frontend
npm install

# Start the development server
npm run dev

# Build for production
npm run build
```

### How to Use

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
- **Routing**: Vue Router
- **HTTP Client**: Axios
- **Real-time Communication**: Socket.IO Client
- **Local Storage**: IndexedDB (Dexie.js)

### Backend Architecture

- **Web Framework**: Flask
- **Real-time Communication**: Flask-SocketIO
- **Document Processing**: python-docx
- **AI Engine**: Integrates various large language models
- **Format Checking**: Custom checker modules
- **Format Correction**: Custom editor modules

### Core Modules

- **FormatAgent**: Responsible for document format analysis and specification checking
- **EditorAgent**: Responsible for document content editing and format correction
- **AdviceAgent**: Provides intelligent modification suggestions
- **CommunicateAgent**: Handles user queries and interactions

## Configuration Guide

The system is configured through the `config.json` file, supporting customization of the following:

- Document page settings (paper size, margins, etc.)
- Paragraph formats (line spacing, alignment, indentation, etc.)
- Font settings (font family, size, style, etc.)
- Heading formats (level, style, numbering, etc.)
- Citation formats (standard, style, etc.)
- Table and image formats (captions, numbering, style, etc.)
- Required paragraph requirements (abstract, keywords, conclusion, etc.)

## Contribution Guidelines

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

## Frequently Asked Questions

### Q: What document formats does the system support?
A: Currently, the system primarily supports Microsoft Word (.docx) format documents.

### Q: How do I customize format specifications?
A: You can customize format specifications in the system's "Format Settings" page or by directly editing the `config.json` file.

### Q: Does the system support multiple languages?
A: Yes, the system interface supports Chinese and English, and it can analyze documents in multiple languages.

### Q: How do I update AI models?
A: You can view, select, and update AI models in the "Model Management" page.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## Contact Us

If you have any questions or suggestions, please contact us through the following channels:

- Submit a GitHub Issue
- Send an email to: [your-email@example.com](mailto:your-email@example.com)
- Visit our website: [https://www.example.com](https://www.example.com)

---

<div align="center">
  <p>© 2023 Scriptor Team. All Rights Reserved.</p>
</div>
