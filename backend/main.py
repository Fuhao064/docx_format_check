from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
from typing import List, Dict, Optional
import os
import json
from agents.setting import LLMs
from format_checker import check_paper_format, remark_para_type, format_check_with_tools
from format_editor import format_document
from datetime import datetime
import docx_parser
from agents.advice_agent import AdviceAgent
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# 创建一个全局的LLMs实例
llm = LLMs()

# 配置上传文件夹
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'docx'}  # 允许的文件类型
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 确保上传目录存在
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 配置允许的文件类型
ALLOWED_EXTENSIONS = {'docx'}

# 初始化全局变量
page_title = "文档格式分析系统"
messages = []
execution_steps = [
    {"id": 1, "text": "上传文件", "status": "pending"},
    {"id": 2, "text": "分析文档格式", "status": "pending"},
    {"id": 3, "text": "检查格式规范", "status": "pending"},
    {"id": 4, "text": "生成分析报告", "status": "pending"}
]

# 检查文件类型是否允许
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 文件上传路由
@app.route('/api/upload-files', methods=['POST'])
def upload_file():
    try:
        # 检查是否有文件在请求中
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '没有上传文件'
            }), 400

        file = request.files['file']

        # 检查文件名是否为空或文件类型是否允许
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '没有选择文件'
            }), 400

        if file and allowed_file(file.filename):
            # 确保文件名安全并生成唯一文件名
            filename = secure_filename(file.filename)
            unique_filename = f"{os.path.splitext(filename)[0]}_{int(os.time.time())}{os.path.splitext(filename)[1]}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            # 保存文件
            file.save(file_path)

            # 返回成功响应
            return jsonify({
                'success': True,
                'message': '文件上传成功',
                'file': {
                    'filename': unique_filename,
                    'originalname': filename,
                    'path': file_path,
                    'size': os.path.getsize(file_path)
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '只支持上传 .docx 文件'
            }), 400

    except Exception as e:
        print(f"文件上传错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"文件上传失败: {str(e)}"
        }), 500

# 获取所有可用模型
@app.route('/api/models')
def get_models():
    try:
        # 使用全局的LLMs实例
        models_config = llm.models_config
        return jsonify({"models": models_config})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 获取当前使用的模型
@app.route('/api/current-model')
def get_current_model():
    try:
        # 使用全局的LLMs实例
        current_model = llm.current_model
        return jsonify({'current_model': current_model})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 设置当前使用的模型
@app.route('/api/set-model', methods=['POST'])
def set_model():
    data = request.get_json()
    if not data or 'model_name' not in data:
        return jsonify({'error': '未提供模型名称'}), 400
    
    try:
        # 使用全局的LLMs实例
        llm.set_model(data['model_name'])
        return jsonify({'message': f'已切换到模型 {data["model_name"]}'})    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 添加新模型
@app.route('/api/add-model', methods=['POST'])
def add_model():
    data = request.get_json()
    required_fields = ['name', 'base_url', 'api_key', 'model_name']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': '缺少必要的模型信息'}), 400
    
    try:
        # 使用全局的LLMs实例
        llm.add_model(data['name'], data['base_url'], data['api_key'], data['model_name'])
        return jsonify({'message': f'模型 {data["name"]} 添加成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 删除模型
@app.route('/api/delete-model/<model_name>', methods=['DELETE'])
def delete_model(model_name):
    try:
        # 使用全局的LLMs实例
        llm.delete_model(model_name)
        return jsonify({'message': f'模型 {model_name} 删除成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 获取完整模型配置
@app.route('/keys.json')
def get_keys():
    try:
        # 使用全局的LLMs实例
        models_config = llm.models_config
        return jsonify(models_config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 创建配置文件
@app.route('/api/create-config', methods=['POST'])
def create_config():
    data = request.get_json()
    if not data or 'config_path' not in data or 'config_data' not in data:
        return jsonify({"error": "缺少必要参数"}), 400
    
    try:
        config_path = data['config_path']
        config_data = data['config_data']
        
        # 确保目录存在
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # 保存配置文件
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        
        return jsonify({
            "success": True,
            "message": f"配置文件已保存到 {config_path}"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"发生错误：{str(e)}"
        }), 500

# 获取示例配置文件
@app.route('/api/get-config-example')
def get_config_example():
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config_example.json')
        if not os.path.exists(config_path):
            return jsonify({"error": "示例配置文件不存在"}), 404
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return jsonify({
            "success": True,
            "config": config_data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"发生错误：{str(e)}"
        }), 500

# 获取配置文件
@app.route('/api/get-config')
def get_config():
    try:
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../config.json'))  # 配置文件路径
        if not os.path.exists(config_path):
            return jsonify({"error": "配置文件不存在"}), 404
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return jsonify(config_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 保存配置文件
@app.route('/api/set-config', methods=['POST'])
def set_config():
    data = request.get_json()
    if not data:
        return jsonify({'error': '配置数据不能为空'}), 400
    
    try:
        config_path = 'config.json'  # 配置文件路径
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        return jsonify({'message': '配置保存成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 上传格式文件
@app.route('/api/upload-format', methods=['POST'])
def upload_format():
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "未找到上传的文件"}), 400
    
    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return jsonify({"success": False, "message": "未选择文件"}), 400
    
    try:
        filename = secure_filename(uploaded_file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if file_ext == 'json':
            # 直接保存JSON文件
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            uploaded_file.save(file_path)
            
            return jsonify({
                "success": True,
                "message": "格式文件上传成功",
                "file_path": file_path,
                "filename": filename
            })
        elif file_ext == 'docx':
            # 处理docx格式文件
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            uploaded_file.save(file_path)
            
            # 使用format_agent处理docx文件，提取格式信息
            format_json = llm.parse_format(file_path, '{}')
            
            # 保存提取的格式信息
            json_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{filename.rsplit('.', 1)[0]}_format.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                f.write(format_json)
            
            return jsonify({
                "success": True,
                "message": "格式文件上传并处理成功",
                "file_path": json_path,
                "filename": f"{filename.rsplit('.', 1)[0]}_format.json"
            })
        else:
            return jsonify({
                "success": False,
                "message": f"不支持的文件类型，仅支持 .docx 或 .json 文件"
            }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"格式文件上传失败: {str(e)}"
        }), 500

# 获取文档修改建议
@app.route('/api/get-advice', methods=['POST'])
def process_file():
    try:
        data = request.get_json()
        if not data or 'doc_path' not in data:
            return jsonify({"error": "缺少必要参数"}), 400
        file_path = data.get('doc_path')
        # 处理文件信息
        doc_content = docx_parser.extract_doc_content(file_path)
        # 初始化advice_agent
        advice_agent = AdviceAgent('qwen-plus')
        # 传送给格式建议
        result = advice_agent.get_advice(doc_content)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8000, debug=True)
