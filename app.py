from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import os
import json
from werkzeug.utils import secure_filename
from para_type import ParagraphManager, ParsedParaType

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)  # 启用CORS支持跨域请求

# 配置文件上传目录
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
RESULT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'result.json')

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'docx', 'json'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    # 检查是否有文件部分
    if 'file' not in request.files:
        return jsonify({'error': '没有文件部分'}), 400
    
    file = request.files['file']
    file_type = request.form.get('type', 'docx')  # 获取文件类型，默认为docx
    
    # 如果用户没有选择文件，浏览器也会提交一个空的文件部分
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # 如果是配置文件，则保存到config.json
        if file_type == 'config' and filename.endswith('.json'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=4)
                
                return jsonify({
                    'message': '配置文件上传成功',
                    'filename': filename
                })
            except Exception as e:
                return jsonify({'error': f'配置文件处理失败: {str(e)}'}), 500
        
        return jsonify({
            'message': '文件上传成功',
            'filename': filename,
            'path': f'/uploads/{filename}'
        })
    
    return jsonify({'error': '不允许的文件类型'}), 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/config', methods=['GET'])
def get_config():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        return jsonify(config_data)
    except Exception as e:
        return jsonify({'error': f'获取配置失败: {str(e)}'}), 500

@app.route('/api/config', methods=['POST'])
def update_config():
    try:
        config_data = request.json
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        return jsonify({'message': '配置更新成功'})
    except Exception as e:
        return jsonify({'error': f'更新配置失败: {str(e)}'}), 500

@app.route('/api/paragraphs', methods=['GET'])
def get_paragraphs():
    try:
        with open(RESULT_FILE, 'r', encoding='utf-8') as f:
            paragraphs_data = json.load(f)
        return jsonify(paragraphs_data)
    except Exception as e:
        return jsonify({'error': f'获取段落数据失败: {str(e)}'}), 500

@app.route('/api/paragraphs/<para_id>', methods=['PUT'])
def update_paragraph(para_id):
    try:
        para_data = request.json
        
        # 读取现有段落数据
        with open(RESULT_FILE, 'r', encoding='utf-8') as f:
            paragraphs_data = json.load(f)
        
        # 查找并更新指定ID的段落
        for i, para in enumerate(paragraphs_data):
            if para['id'] == para_id:
                # 更新内容和元数据
                if 'content' in para_data:
                    paragraphs_data[i]['content'] = para_data['content']
                if 'meta' in para_data:
                    paragraphs_data[i]['meta'] = para_data['meta']
                if 'type' in para_data:
                    paragraphs_data[i]['type'] = para_data['type']
                
                # 保存更新后的数据
                with open(RESULT_FILE, 'w', encoding='utf-8') as f:
                    json.dump(paragraphs_data, f, ensure_ascii=False, indent=4)
                
                return jsonify({'message': '段落更新成功'})
        
        return jsonify({'error': '未找到指定ID的段落'}), 404
    except Exception as e:
        return jsonify({'error': f'更新段落失败: {str(e)}'}), 500

@app.route('/api/paragraph_types', methods=['GET'])
def get_paragraph_types():
    try:
        # 获取所有段落类型
        types = [member.value for member in ParsedParaType]
        return jsonify(types)
    except Exception as e:
        return jsonify({'error': f'获取段落类型失败: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
CORS(app)