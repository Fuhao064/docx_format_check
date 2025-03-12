import docx 
import extract_para_info, docx_parser
import json
from typing import Dict
from format_agent import LLMs
from para_type import ParagraphManager,ParsedParaType
import os,concurrent,re
def load_config(config_path: str) -> Dict:
    """加载JSON配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"配置文件 {config_path} 未找到，将创建新文件")
        return {}

def save_config(config_path: str, config: Dict) -> None:
    """保存配置文件"""
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def update_config(config_path: str, new_config: Dict) -> None:
    """深度更新配置文件"""
    try:
        current_config = load_config(config_path)
        # 实现深度更新（示例为简单实现，复杂情况需要递归函数）
        for key, value in new_config.items():
            if isinstance(value, dict) and key in current_config:
                current_config[key].update(value)
            else:
                current_config[key] = value
        save_config(config_path, current_config)
        print("配置文件更新成功！")
    except json.JSONDecodeError:
        print(f"配置文件 {config_path} 格式错误")
    except Exception as e:
        print(f"发生错误：{e}")

def is_value_equal(expected, actual, key):
    """
    比较两个值是否相等，考虑特殊情况。
    """
    # 特殊处理：字体大小字段
    if key == "size":
        expected_value = extract_number(expected)
        actual_value = extract_number(actual)
        if expected_value is not None and actual_value is not None:
            return abs(expected_value - actual_value) <= 0.01  # 允许小误差

    # 转换为小写进行比较（忽略大小写差异）
    expected_lower = str(expected).lower()
    actual_lower = str(actual).lower()

    # 如果完全相同（忽略大小写），直接返回 True
    if expected_lower == actual_lower:
        return True

    # 特殊处理：颜色字段，忽略 #000000 和 black 的差异
    if key == "color":
        if (expected_lower in ["#000000", "black"] and actual_lower in ["#000000", "black"]):
            return True

    # 特殊处理：布尔值，忽略大小写差异
    if isinstance(expected, bool) and isinstance(actual, bool):
        return expected == actual

    # 特殊处理：方向值
    if key == "orientation":
        return expected_lower == actual_lower

    # 提取数值进行比较
    expected_value = extract_number(expected)
    actual_value = extract_number(actual)

    if expected_value is not None and actual_value is not None:
        # 对于边距值，允许 0.01 厘米的误差
        margin_keys = ('top', 'bottom', 'left', 'right')
        if any(margin_key in key.lower() for margin_key in margin_keys):
            return abs(expected_value - actual_value) <= 0.01

    # 其他情况直接比较
    return False


def extract_number(value):
    """
    从字符串中提取数值部分。
    """
    import re
    match = re.search(r"[-+]?\d*\.\d+|\d+", str(value))
    if match:
        return float(match.group())
    return None

def check_paper_format(doc_info: Dict, required_format: Dict) -> None:
    paper_required_format = required_format.get('paper', {})
    errors = []
    
    # 遍历要求格式中的每个字段
    for key, expected in paper_required_format.items():
        # 检查字段是否存在
        if key not in doc_info:
            errors.append(f"缺少必需字段: '{key}'")
            continue
            
        actual = doc_info[key]
        
        # 递归处理嵌套字典
        if isinstance(expected, dict):
            if not isinstance(actual, dict):
                errors.append(f"字段类型不匹配: '{key}' 应为字典类型，实际为 {type(actual).__name__}")
                continue
                
            # 递归调用检查嵌套字段
            nested_errors = check_paper_format(actual, {"paper": expected})
            errors.extend([f"{key}.{err}" for err in nested_errors])
                
        # 检查值是否匹配
        else:
            if not is_value_equal(expected, actual, key):
                errors.append(f"'{key}' 不匹配: 要求 {expected}, 实际 {actual}")
    
    # 打印错误信息
    if errors:
        print("\n页面格式检查错误:")
        for err in errors:
            print(f"- {err}")
    
    return errors

def remark_para_type(doc_path: str, llm: LLMs) -> ParagraphManager:
    # 初始化段落管理器
    paragraph_manager = ParagraphManager()
    
    # 读取doc的段落信息
    paragraph_manager = extract_para_info.extract_para_format_info(doc_path, paragraph_manager)
    
    # 文档整个内容
    doc_content = docx_parser.extract_doc_content(doc_path)
    
    # 定义任务函数
    def process_paragraph(para_index: int, para: Dict, doc_content_sent: bool, manager: ParagraphManager):
        try:
            if para["type"] != ParsedParaType.BODY:
                pass
            # 提取当前段落信息
            para_string = para["content"]
            
            # 调用大模型预测类型
            response = llm.predict_location(doc_content, para_string, doc_content_sent)
            response = response.strip()  # 去除首尾空白字符
            
            # 解析 JSON 字符串
            response_dict = json.loads(response)
            
            # 将返回的location转换为ParsedParaType枚举类型
            try:
                new_type = ParsedParaType(response_dict["location"])
                # 直接访问paragraphs列表中的对应索引
                manager.paragraphs[para_index].type = new_type
            except ValueError:
                print(f"Invalid paragraph type received: {response_dict['location']}")
                manager.paragraphs[para_index].type = ParsedParaType.BODY
            
        except Exception as e:
            # 如果解析失败，将段落类型设置为 BODY
            print(f"Error processing paragraph: {para_string[:50]}... Error: {e}")
            manager.paragraphs[para_index].type = ParsedParaType.BODY

    # 将段落json转为中文
    paras_info_json_zh = paragraph_manager.to_chinese_dict()
    
    # 使用线程池并发处理
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        doc_content_sent = False
        
        # 提交任务到线程池，同时传入段落索引
        for i, para in enumerate(paras_info_json_zh):
            future = executor.submit(process_paragraph, i, para, doc_content_sent, paragraph_manager)
            futures.append(future)
            doc_content_sent = True  # 更新全文标志
        
        # 等待所有任务完成
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()  # 确保任务完成
            except Exception as e:
                print(f"Error in thread pool task: {e}")
    
    return paragraph_manager

def check_abstract(paragraph_manager:ParagraphManager):
    errors = []
    # 获取摘要的内容
    abstract_content_zh = paragraph_manager.get_by_type(ParsedParaType.ABSTRACT_CONTENT_ZH)
    # 如果没有获取到摘要，则报错
    if abstract_content_zh is None:
        errors.append("中文摘要内容缺失")
    # 统计摘要的字数是否合适
    if abstract_content_zh is not None:        
        if len(abstract_content_zh) < 100 or len(abstract_content_zh) > 500:
            errors.append("中文摘要字数不合适")
    # 获取英文摘要内容
    abstract_content_en = paragraph_manager.get_by_type(ParsedParaType.ABSTRACT_CONTENT_EN)   
    # 如果没有获取到英文摘要，则报错
    if abstract_content_en is None:
        errors.append("英文摘要内容缺失")
    if abstract_content_en is not None:        
        if len(abstract_content_en) < 100 or len(abstract_content_en) > 500:
            errors.append("英文摘要字数不合适")
    return errors

def check_keywords(paragraph_manager:ParagraphManager):
    errors = []
    # 获取关键词的内容
    keywords_content_zh = paragraph_manager.get_by_type(ParsedParaType.KEYWORDS_CONTENT_ZH)
    if keywords_content_zh is None:
        errors.append("中文关键词内容缺失")
    # 对中文关键词按照标点分割(,或、或；)
    if keywords_content_zh is not None:        
        keywords_list = keywords_content_zh.split(',')
        if len(keywords_list) < 2 or len(keywords_list) > 5:
            errors.append("中文关键词个数不合适")
    return errors


def check_main_format(paragraph_manager, required_format):
    """
    主检查函数，整合字体检查和格式检查。
    """
    errors = {}

    # 获取段落信息
    paras_format_info = paragraph_manager.to_dict()

    # 检查每个段落的格式
    for para in paras_format_info:
        para_id = para.get("id")  # 段落唯一标识
        para_type = para.get("type")
        para_meta = para.get("meta", {})
        required_meta = required_format.get(para_type, {})

        # 遍历要求格式中的每个字段
        for key, expected in required_meta.items():
            actual = para_meta.get(key)

            # 如果字段不存在
            if actual is None:
                _add_error(errors, para_id, f"缺少必需字段: '{key}'")
                continue

            # 如果字段是列表类型，优先检查长度
            if isinstance(actual, list):
                if len(actual) > 1:
                    _add_error(errors, para_id, f"字段 '{key}' 存在多个值: {actual}")
                    continue
                actual = actual[0]  # 取第一个值进行比较

            # 递归处理嵌套字典
            if isinstance(expected, dict):
                if not isinstance(actual, dict):
                    _add_error(errors, para_id, f"字段类型不匹配: '{key}' 应为字典类型，实际为 {type(actual).__name__}")
                    continue

                # 递归检查嵌套字段
                nested_errors = _recursive_check(actual, expected)
                for err in nested_errors:
                    _add_error(errors, para_id, f"{key}.{err}")

            # 检查值是否匹配
            else:
                if not is_value_equal(expected, actual, key):
                    _add_error(errors, para_id, f"'{key}' 不匹配: 要求 {expected}, 实际 {actual}")

    # 打印错误信息
    if errors:
        print("\n页面格式检查错误:")
        for para_id, error_list in errors.items():
            print(f"- 段落 ID: {para_id}")
            for err in error_list:
                print(f"  - {err}")
    return errors


def _recursive_check(actual, expected):
    """
    递归检查嵌套字典的字段。
    """
    nested_errors = []

    for key, expected_value in expected.items():
        actual_value = actual.get(key)

        # 如果字段不存在
        if actual_value is None:
            nested_errors.append(f"缺少必需字段: '{key}'")
            continue

        # 如果字段是列表类型，优先检查长度
        if isinstance(actual_value, list):
            if len(actual_value) > 1:
                nested_errors.append(f"字段 '{key}' 存在多个值: {actual_value}")
                continue
            actual_value = actual_value[0]  # 取第一个值进行比较

        # 递归处理嵌套字典
        if isinstance(expected_value, dict):
            if not isinstance(actual_value, dict):
                nested_errors.append(f"字段类型不匹配: '{key}' 应为字典类型，实际为 {type(actual_value).__name__}")
                continue

            # 递归检查嵌套字段
            deeper_errors = _recursive_check(actual_value, expected_value)
            for err in deeper_errors:
                nested_errors.append(f"{key}.{err}")

        # 检查值是否匹配
        else:
            if not is_value_equal(expected_value, actual_value, key):
                nested_errors.append(f"'{key}' 不匹配: 要求 {expected_value}, 实际 {actual_value}")

    return nested_errors



def _add_error(errors, para_id, error_msg):
    """
    添加错误到错误字典中。
    """
    if para_id not in errors:
        errors[para_id] = []
    errors[para_id].append(error_msg)

def check_format(doc_path:str, required_format:dict, llm:LLMs):
    doc_info = docx_parser.extract_section_info(doc_path)
    # 初始化段落管理器
    paragraph_manager = ParagraphManager()
    # 读取doc的段落信息
    paragraph_manager = extract_para_info.extract_para_format_info(doc_path, paragraph_manager)
    # 重分配段落类型
    # paragraph_manager = remark_para_type(doc_path, llm)
    # 修改rusult到英文
    with open("../result.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        result = paragraph_manager.to_english_dict(data)
    # 写回json
    with open("../result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    paragraph_manager = ParagraphManager.build_from_json_file("../result.json")
    # paras_info_json_zh = paragraph_manager.to_chinese_dict()
    # 对齐段落信息和格式信息同Config
    # print(paras_info_dict)
    # 检查格式是否符合要求
    check_paper_format(doc_info, required_format)
    #  检查段落格式
    check_main_format(paragraph_manager, required_format)
    #  检查表格样式
    # check_table_format(doc_path, required_format)
    # # 检查图片样式
    # check_image_format(doc_path, required_format)
    # # 检查引用样式和参考文献
    # check_reference_format(doc_path, required_format)

# llm = LLMs()
# llm.set_model('deepseek-r1')
# required_format = load_config('../config.json')
# check_format('../test.docx', required_format, llm)
