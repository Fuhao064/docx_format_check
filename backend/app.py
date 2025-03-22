from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
from typing import List, Dict, Optional
import os,time,sys
import json
from agents.setting import LLMs
from format_editor import generate_formatted_doc
from para_type import ParagraphManager
from format_checker import check_format
from datetime import datetime
import docx_parser
from agents.advice_agent import AdviceAgent
from docx import Document
from docx.shared import RGBColor
import tempfile
from docx.enum.text import WD_COLOR_INDEX

# 导入agents包中的功能
import agents

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 创建一个全局的LLMs实例
llm = LLMs()

# 配置处理的ParagraphManager和文件名
analysised_para_manager = []

# 配置上传文件夹
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
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

# 初始化代理模型配置
agents.init_agents()

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
            unique_filename = f"{os.path.splitext(filename)[0]}_{int(time.time())}{os.path.splitext(filename)[1]}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename) + ".docx"  # 文件名唯一
            
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

# 获取所有代理的模型配置
@app.route('/api/agent-models')
def get_agent_models():
    try:
        # 获取当前代理配置
        config = {
            "format_model": agents._config.get("format_model", "qwen-plus"),
            "editor_model": agents._config.get("editor_model", "qwen-plus"),
            "advice_model": agents._config.get("advice_model", "qwen-plus"),
            "communicate_model": agents._config.get("communicate_model", "qwen-plus")
        }
        return jsonify(config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 设置指定代理的模型
@app.route('/api/set-agent-model', methods=['POST'])
def set_agent_model():
    data = request.get_json()
    if not data or 'agent_type' not in data or 'model_name' not in data:
        return jsonify({'error': '未提供代理类型或模型名称'}), 400
    
    agent_type = data['agent_type']
    model_name = data['model_name']
    
    if agent_type not in ["format", "editor", "advice", "communicate"]:
        return jsonify({'error': '无效的代理类型'}), 400
    
    try:
        # 更新代理模型配置
        agents.update_model_config(agent_type, model_name)
        return jsonify({'message': f'已将{agent_type}代理的模型更新为 {model_name}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 初始化所有代理
@app.route('/api/init-agents', methods=['POST'])
def initialize_agents():
    data = request.get_json()
    
    try:
        # 使用提供的配置初始化代理，或使用默认配置
        agents.init_agents(data)
        return jsonify({'message': '所有代理初始化成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 获取所有可用模型
@app.route('/api/models')
def get_models():
    try:
        # 使用全局的LLMs实例
        models_config = llm.models_config
        return jsonify({"models": models_config})
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
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename) + '.json'
            uploaded_file.save(file_path)
            return jsonify({
                "success": True,
                "message": "格式Json上传成功",
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

# 使用默认格式
@app.route('/api/use-default-format', methods=['GET'])
def use_default_format():
    try:
        # 获取默认格式文件路径
        default_format_path = os.path.join(os.path.dirname(__file__), 'config_example.json')
        
        # 确保文件存在
        if not os.path.exists(default_format_path):
            return jsonify({
                "success": False,
                "message": "默认格式文件不存在"
            }), 404
            
        # 读取默认配置文件内容
        with open(default_format_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            
        return jsonify({
            "success": True,
            "message": "已应用默认格式",
            "config_path": default_format_path,
            "config_data": config_data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"应用默认格式失败: {str(e)}"
        }), 500

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
        return jsonify({"success": True,
                        "result": result})
    except Exception as e:
        return jsonify({"success": False,
                        "message": str(e)}), 500
# 格式修改Agent
# @app.route('/api/use-format-agent', methods=['POST'])
# def use_format_agent():
#     try:
#         data = request.get_json()
#         if not data or 'messages' not in data:
#             return jsonify({"error": "缺少必要参数"}), 400
        
        
#         return jsonify({"success": True,
#                         "result": result})
#     except Exception as e:
#         return jsonify({"success": False,
#                         "message": str(e)}), 500
# 检查文档格式
@app.route('/api/check-format', methods=['POST'])
def start_check_format():
    try:
        data = request.get_json()
        # 修复逻辑错误，使用正确的条件判断
        if not data or ('doc_path' not in data or 'config_path' not in data):
            return jsonify({"success": False, "message": "缺少必要参数"}), 400
            
        # 获取文件路径
        file_path = data.get('doc_path')
        config_path = data.get('config_path')
        
        # 验证文件存在
        if not os.path.exists(file_path):
            return jsonify({"success": False, "message": "文档文件不存在"}), 404
            
        if not os.path.exists(config_path):
            return jsonify({"success": False, "message": "配置文件不存在"}), 404
            
        # 处理文件信息
        docx_errors, para_manager = check_format(file_path, config_path, llm.model)
        
        # 存储当前的para_manager
        analysised_para_manager.append({"doc_path": file_path, "para_manager": para_manager})

        # 以json格式返回错误信息
        if docx_errors:
            return jsonify({
                "success": True,
                "message": "分析成功",
                "errors": docx_errors  # 修改键名与前端一致
            })
        else:
            return jsonify({
                "success": True,
                "message": "未发现错误",
                "errors": []  # 返回空数组而不是None
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"格式检查失败: {str(e)}"
        }), 500

# 生成分析报告
@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    try:
        data = request.get_json()
        if not data or 'doc_path' not in data:
            return jsonify({"success": False, "message": "缺少必要参数"}), 400
        
        # 获取文件路径
        file_path = data.get('doc_path')
        errors = data.get('errors', [])
        
        # 验证文件存在
        if not os.path.exists(file_path):
            return jsonify({"success": False, "message": "文档文件不存在"}), 404
            
        # 为了保持与之前功能兼容，如果没有提供错误列表，则调用check_format
        if not errors and 'config_path' in data:
            config_path = data.get('config_path')
            if not config_path or not os.path.exists(config_path):
                return jsonify({"success": False, "message": "配置文件不存在"}), 404
            errors = check_format(file_path, config_path, llm.model)
            
            # 确保errors是列表类型
            if errors is None:
                errors = []
            elif isinstance(errors, str):
                # 如果返回的是字符串，将其作为单个错误消息添加到列表中
                errors = [{"message": errors, "location": "未知"}]
            elif not isinstance(errors, list):
                # 如果不是列表类型，尝试转换或创建新列表
                try:
                    errors = list(errors)
                except:
                    errors = [{"message": str(errors), "location": "未知"}]
        
        # 创建临时文件用于存储标记错误的文档
        temp_dir = tempfile.gettempdir()
        doc_name = os.path.basename(file_path)
        marked_doc_path = os.path.join(temp_dir, f"marked_{doc_name}")
        
        # 创建一个新文档，并标记错误
        try:
            doc = Document(file_path)
            
            # 获取段落ID到错误的映射
            para_errors = {}
            for error in errors:
                # 检查error是否为字典类型，如果不是则转换为字典
                if not isinstance(error, dict):
                    error = {"message": str(error), "id": None, "location": "未知"}
                
                if 'id' in error:
                    para_id = error['id']
                    if para_id not in para_errors:
                        para_errors[para_id] = []
                    para_errors[para_id].append(error.get('message', '未知错误'))
            
            # 处理段落错误和标记
            for i, para in enumerate(doc.paragraphs):
                para_id = f"para{i}"
                if para_id in para_errors:
                    # 使用红色标记错误段落
                    for run in para.runs:
                        run.font.color.rgb = RGBColor(255, 0, 0)
                    
                    # 在段落后添加错误信息
                    error_paragraph = doc.add_paragraph()
                    error_run = error_paragraph.add_run("错误信息: ")
                    error_run.bold = True
                    error_run.font.color.rgb = RGBColor(255, 0, 0)
                    
                    for j, error_msg in enumerate(para_errors[para_id]):
                        error_run = error_paragraph.add_run(f"{j+1}. {error_msg}")
                        error_run.font.color.rgb = RGBColor(255, 0, 0)
                        if j < len(para_errors[para_id]) - 1:
                            error_run = error_paragraph.add_run("\n")
            
            # 添加表格和图片错误信息（如果有）
            table_errors = []
            image_errors = []
            
            for error in errors:
                if not isinstance(error, dict):
                    continue
                
                error_type = error.get('type', '')
                if error_type == 'table':
                    table_errors.append(error)
                elif error_type == 'image':
                    image_errors.append(error)
            
            if table_errors or image_errors:
                doc.add_paragraph().add_run("").add_break()
                summary = doc.add_paragraph()
                
                if table_errors:
                    table_run = summary.add_run("表格错误:\n")
                    table_run.bold = True
                    for error in table_errors:
                        summary.add_run(f"- {error.get('message', '未知表格错误')}\n").font.color.rgb = RGBColor(255, 0, 0)
                
                if image_errors:
                    image_run = summary.add_run("\n图片错误:\n")
                    image_run.bold = True
                    for error in image_errors:
                        summary.add_run(f"- {error.get('message', '未知图片错误')}\n").font.color.rgb = RGBColor(255, 0, 0)
        
            # 保存标记后的文档
            os.makedirs(os.path.dirname(marked_doc_path), exist_ok=True)
            doc.save(marked_doc_path)
        except Exception as e:
            print(f"标记文档错误: {str(e)}")
            return jsonify({"success": False, "message": f"标记文档错误: {str(e)}"}), 500
        
        # 生成分析报告文本
        report = "文档格式分析报告\n\n"
        report += f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"文档: {os.path.basename(file_path)}\n\n"
        
        # 添加错误摘要
        if errors:
            report += f"发现 {len(errors)} 个格式问题:\n\n"
            for i, error in enumerate(errors):
                if isinstance(error, dict):
                    msg = error.get('message', '未知错误')
                    location = error.get('location', '')
                    report += f"{i+1}. {msg}"
                    if location:
                        report += f" (位置: {location})"
                else:
                    report += f"{i+1}. {str(error)}"
                report += "\n"
        else:
            report += "没有发现格式问题。\n"
        
        return jsonify({
            "success": True,
            "message": "报告生成成功",
            "report": report,
            "marked_doc_path": marked_doc_path
        })
    except Exception as e:
        print(f"报告生成失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"报告生成失败: {str(e)}"
        }), 500

# 下载报告
@app.route('/api/download-report', methods=['GET'])
def download_report():
    try:
        doc_path = request.args.get('doc_path')
        if not doc_path:
            return jsonify({"success": False, "message": "缺少文档路径参数"}), 400
            
        # 获取文件路径
        file_path = doc_path
        errors = []
        
        # 验证文件存在
        if not os.path.exists(file_path):
            return jsonify({"success": False, "message": "文档文件不存在"}), 404
        
        # 创建一个新的Word文档作为报告
        doc = Document()
        
        # 添加标题
        doc.add_heading('文档格式分析报告', 0)
        
        # 添加基本信息
        doc.add_paragraph(f'分析时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n文档: {os.path.basename(file_path)}')
        
        # 添加错误摘要
        if errors:
            doc.add_heading(f'发现 {len(errors)} 个格式问题:', 1)
            for i, error in enumerate(errors):
                p = doc.add_paragraph()
                p.add_run(f"{i+1}. {error.get('message', '')}").bold = True
                if 'location' in error:
                    p.add_run(f" (位置: {error['location']})").italic = True
        else:
            doc.add_paragraph('没有发现格式问题。').bold = True
        
        # 保存报告到临时文件
        temp_dir = tempfile.gettempdir()
        report_path = os.path.join(temp_dir, f"report_{os.path.basename(file_path)}")
        doc.save(report_path)
        
        # 返回文件
        return send_from_directory(
            os.path.dirname(report_path),
            os.path.basename(report_path),
            as_attachment=True,
            download_name=f"report_{os.path.basename(doc_path)}"
        )
    except Exception as e:
        print(f"下载报告失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"下载报告失败: {str(e)}"
        }), 500

# 下载标记的文档
@app.route('/api/download-marked-document', methods=['GET'])
def download_marked_document():
    try:
        doc_path = request.args.get('doc_path')
        if not doc_path:
            return jsonify({"success": False, "message": "缺少文档路径参数"}), 400
            
        # 构造标记文档的路径
        temp_dir = tempfile.gettempdir()
        doc_name = os.path.basename(doc_path)
        marked_doc_path = os.path.join(temp_dir, f"marked_{doc_name}")
        
        # 检查文件是否存在
        if not os.path.exists(marked_doc_path):
            return jsonify({"success": False, "message": "标记文档不存在，请先生成报告"}), 404
            
        # 返回文件
        return send_from_directory(
            os.path.dirname(marked_doc_path),
            os.path.basename(marked_doc_path),
            as_attachment=True,
            download_name=f"marked_{os.path.basename(doc_path)}"
        )
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"下载标记文档失败: {str(e)}"
        }), 500
    
# 应用格式
@app.route('/api/apply-format', methods=['POST'])
def apply_format():
    try:
        data = request.get_json()
        if not data or 'doc_path' not in data or 'config_path' not in data:
            return jsonify({"success": False, "message": "缺少必要参数"}), 400
        
        doc_path = data.get('doc_path')
        config_path = data.get('config_path')
        
        # 验证文件存在
        if not os.path.exists(doc_path):
            return jsonify({"success": False, "message": "文档文件不存在"}), 404
        
        if not os.path.exists(config_path):
            return jsonify({"success": False, "message": "配置文件不存在"}), 404
        
        # 找到对应的para_manager
        para_manager = next((item['para_manager'] for item in analysised_para_manager if item['doc_path'] == doc_path), None)
        if not para_manager:
            return jsonify({"success": False, "message": "未找到对应的段落管理器"}), 404
        
        # 将输出目录输出为doc_path的文件名
        output_path = os.path.join(os.path.dirname(doc_path), os.path.basename(doc_path).split(".")[0] + "_formatted.docx")

        # 应用格式
        output_path = generate_formatted_doc(config_path, para_manager, output_path)
        
        # 返回文件
        return jsonify({"success": True, "message": "格式应用成功", "output_path": output_path})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
                

# 和大模型交互
@app.route('/api/send-message', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"success": False, "message": "缺少必要参数"}), 400
        message = data.get('message')
        
        # 使用大模型处理消息
        response = llm.model.invoke(message)
        
        return jsonify({"success": True, "message": response})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8000, debug=True)
