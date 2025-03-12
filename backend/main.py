from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
from typing import List, Dict, Optional
import os
import json
from format_agent import LLMs
from format_checker import check_paper_format, remark_para_type
from datetime import datetime

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# 创建一个全局的LLMs实例
llm = LLMs()

# 配置静态文件服务
app.config['UPLOAD_FOLDER'] = 'uploads'
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

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

# 获取页面标题
@app.route('/api/get-title')
def get_title():
    return jsonify({"title": page_title})

# 发送消息并获取回复
@app.route('/api/send-message', methods=['POST'])
def send_message():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "消息不能为空"}), 400
    
    try:
        # 使用全局的LLMs实例
        system_reply = "收到您的消息：" + data['message']
        
        # 保存消息历史
        timestamp = data.get('timestamp') or datetime.now().isoformat()
        user_message = {
            "sender": "user",
            "content": data['message'],
            "timestamp": timestamp
        }
        system_message = {
            "sender": "system",
            "content": system_reply,
            "timestamp": timestamp
        }
        
        messages.append(user_message)
        messages.append(system_message)
        
        # 通过WebSocket广播消息
        socketio.emit('message', system_message)
        
        return jsonify({
            "reply": system_reply,
            "timestamp": timestamp
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 上传文件
@app.route('/api/upload-files', methods=['POST'])
def upload_files():
    if 'docx_file' not in request.files:
        return jsonify({"error": "未找到上传的文件"}), 400
    
    docx_file = request.files['docx_file']
    if docx_file.filename == '':
        return jsonify({"error": "未选择文件"}), 400
    
    try:
        if allowed_file(docx_file.filename):
            filename = secure_filename(docx_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            docx_file.save(file_path)
            
            # 更新执行步骤状态
            execution_steps[0]["status"] = "completed"
            socketio.emit('step_update', execution_steps[0])
            
            return jsonify({"message": "文件上传成功", "file_path": file_path})
        else:
            return jsonify({"error": "不支持的文件类型"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 获取执行步骤状态
@app.route('/api/get-execution-steps')
def get_execution_steps():
    return jsonify({"steps": execution_steps})

# 获取历史消息
@app.route('/api/get-messages')
def get_messages():
    return jsonify({"messages": messages})

# 开始文档分析
@app.route('/api/analyze-document', methods=['POST'])
def analyze_document():
    data = request.get_json()
    if not data or 'file_path' not in data:
        return jsonify({"error": "未提供文件路径"}), 400
    
    try:
        # 更新状态为分析中
        execution_steps[1]["status"] = "in_progress"
        socketio.emit('step_update', execution_steps[1])
        
        # 使用全局的LLMs实例
        paragraph_manager = remark_para_type(data['file_path'], llm)
        
        # 更新状态为完成
        execution_steps[1]["status"] = "completed"
        execution_steps[2]["status"] = "in_progress"
        
        socketio.emit('step_update', execution_steps[1])
        
        # 检查文档格式
        format_errors = check_paper_format(paragraph_manager.to_dict(), {})
        
        # 更新状态
        execution_steps[2]["status"] = "completed"
        execution_steps[3]["status"] = "completed"
        
        socketio.emit('step_update', execution_steps[2])
        
        return jsonify({
            "message": "文档分析完成",
            "errors": format_errors,
            "paragraphs": paragraph_manager.to_chinese_dict()
        })
    except Exception as e:
        # 更新状态为错误
        for step in execution_steps[1:]:
            if step["status"] == "in_progress":
                step["status"] = "error"
        
        return jsonify({"error": str(e)}), 500

# WebSocket连接事件
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('message')
def handle_message(data):
    emit('message', {"message": f"Message received: {data}"})

# 获取所有可用模型
@app.route('/api/models')
def get_models():
    try:
        # 使用全局的LLMs实例
        models_config = llm.models_config
        models_list = [{'name': name} for name in models_config.keys()]
        return jsonify({'models': models_list})
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

@socketio.on('message')
def handle_message(data):
    emit('message', {"message": f"Message received: {data}"})

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8000, debug=True)