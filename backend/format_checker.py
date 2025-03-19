import docx 
import extract_para_info, docx_parser
import json
from typing import Dict, List, Tuple
from format_analysis import FormatAuxiliary
from para_type import ParagraphManager,ParsedParaType
import os,concurrent,re
from utils import are_values_equal, extract_number_from_string
from config_utils import load_config, save_config, update_config

def is_value_equal(expected, actual, key):
    return are_values_equal(expected, actual, key)

def extract_number(value):
    return extract_number_from_string(value)

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

def check_reference_format(doc_path: str, required_format: Dict) -> List[str]:
    """
    检查参考文献格式是否符合指定标准
    支持检查GB/T 7714-2005、GB/T 7714-2015、APA、MLA等多种标准
    """
    errors = []
    doc = docx.Document(doc_path)
    
    # 获取参考文献部分的要求格式
    reference_required_format = required_format.get('references', {})
    reference_standard = reference_required_format.get('standard', 'GB/T 7714-2015')
    
    # 查找参考文献部分
    references_paragraphs = []
    found_references_section = False
    
    for para in doc.paragraphs:
        # 检查是否是参考文献标题段落
        if not found_references_section and re.search(r'参考文献|REFERENCES', para.text, re.IGNORECASE):
            found_references_section = True
            continue
        
        # 收集参考文献段落
        if found_references_section and para.text.strip():
            references_paragraphs.append(para.text.strip())
    
    if not references_paragraphs:
        errors.append("未找到参考文献部分")
        return errors
    
    # 根据不同标准检查参考文献格式
    if reference_standard.startswith('GB/T 7714'):
        gbt_errors = _check_gbt_references(references_paragraphs, reference_standard)
        errors.extend(gbt_errors)
    elif reference_standard == 'APA':
        apa_errors = _check_apa_references(references_paragraphs)
        errors.extend(apa_errors)
    elif reference_standard == 'MLA':
        mla_errors = _check_mla_references(references_paragraphs)
        errors.extend(mla_errors)
    else:
        errors.append(f"不支持的参考文献标准: {reference_standard}")
    
    # 打印错误信息
    if errors:
        print("\n参考文献格式检查错误:")
        for err in errors:
            print(f"- {err}")
    
    return errors

def _check_gbt_references(references: List[str], standard: str) -> List[str]:
    """
    检查参考文献是否符合GB/T 7714标准
    """
    errors = []
    
    # 检查每条参考文献
    for i, ref in enumerate(references):
        # 检查编号格式 [1] 或 [1]
        if not re.match(r'^\[\d+\]', ref):
            errors.append(f"参考文献 #{i+1} 编号格式错误，应以[数字]开头")
            continue
        
        # 检查作者与题名之间的分隔符
        if '. ' not in ref and '．' not in ref:
            errors.append(f"参考文献 #{i+1} 作者与题名之间缺少正确的分隔符")
        
        # 检查不同类型文献的格式
        if '[J]' in ref or '[J/OL]' in ref:  # 期刊论文
            if not _check_journal_format(ref, standard):
                errors.append(f"参考文献 #{i+1} 期刊论文格式不符合{standard}标准")
        elif '[M]' in ref:  # 专著
            if not _check_book_format(ref, standard):
                errors.append(f"参考文献 #{i+1} 专著格式不符合{standard}标准")
        elif '[D]' in ref:  # 学位论文
            if not _check_thesis_format(ref, standard):
                errors.append(f"参考文献 #{i+1} 学位论文格式不符合{standard}标准")
        elif '[C]' in ref or '[C/OL]' in ref:  # 会议论文
            if not _check_conference_format(ref, standard):
                errors.append(f"参考文献 #{i+1} 会议论文格式不符合{standard}标准")
        elif '[EB/OL]' in ref:  # 电子资源
            if not _check_electronic_format(ref, standard):
                errors.append(f"参考文献 #{i+1} 电子资源格式不符合{standard}标准")
        else :errors.append(f"不符合的参考文献类型: {ref}")
    
    return errors

def _check_journal_format(ref: str, standard: str) -> bool:
    """检查期刊论文格式"""
    # GB/T 7714-2015格式: [序号] 作者. 题名[J]. 刊名, 出版年, 卷号(期号): 起止页码.
    pattern = r'^\[\d+\]\s+[\w\s,]+\.\s+.+\[J(/OL)?\]\.\s+.+,\s+\d{4},\s+\d+(\(\d+\))?\:\s*\d+(-\d+)?\.?$'
    return bool(re.match(pattern, ref, re.UNICODE))

def _check_book_format(ref: str, standard: str) -> bool:
    """检查专著格式"""
    # GB/T 7714-2015格式: [序号] 作者. 书名[M]. 版本(第1版不标注). 出版地: 出版社, 出版年: 起止页码.
    pattern = r'^\[\d+\]\s+[\w\s,]+\.\s+.+\[M\]\.\s+.*\:\s+.+,\s+\d{4}(\:\s*\d+(-\d+)?)?\.?$'
    return bool(re.match(pattern, ref, re.UNICODE))

def _check_thesis_format(ref: str, standard: str) -> bool:
    """检查学位论文格式"""
    # GB/T 7714-2015格式: [序号] 作者. 题名[D]. 保存地: 保存单位, 出版年.
    pattern = r'^\[\d+\]\s+[\w\s,]+\.\s+.+\[D\]\.\s+.+\:\s+.+,\s+\d{4}\.?$'
    return bool(re.match(pattern, ref, re.UNICODE))

def _check_conference_format(ref: str, standard: str) -> bool:
    """检查会议论文格式"""
    # GB/T 7714-2015格式: [序号] 作者. 题名[C]. 会议名, 会议地点, 会议年份. 出版地: 出版者, 出版年: 起止页码.
    pattern = r'^\[\d+\]\s+[\w\s,]+\.\s+.+\[C(/OL)?\]\.\s+.+,\s+.+,\s+\d{4}\.\s+.+\:\s+.+,\s+\d{4}(\:\s*\d+(-\d+)?)?\.?$'
    return bool(re.match(pattern, ref, re.UNICODE))

def _check_electronic_format(ref: str, standard: str) -> bool:
    """检查电子资源格式"""
    # GB/T 7714-2015格式: [序号] 作者. 题名[EB/OL]. 出版地: 出版者, 出版年[引用日期]. 获取和访问路径.
    pattern = r'^\[\d+\]\s+[\w\s,]+\.\s+.+\[EB/OL\]\.(\s+.+\:\s+.+,\s+\d{4})?\s*\[\d{4}-\d{2}-\d{2}\]\.\s+https?://.*$'
    return bool(re.match(pattern, ref, re.UNICODE))

def _check_apa_references(references: List[str]) -> List[str]:
    """
    检查参考文献是否符合APA标准
    """
    errors = []
    # APA格式检查逻辑
    for i, ref in enumerate(references):
        # 检查作者格式
        if not re.match(r'^[\w\s,]+\s+\(\d{4}\)', ref):
            errors.append(f"参考文献 #{i+1} 作者和年份格式不符合APA标准")
    
    return errors

def _check_mla_references(references: List[str]) -> List[str]:
    """
    检查参考文献是否符合MLA标准
    """
    errors = []
    # MLA格式检查逻辑
    for i, ref in enumerate(references):
        # 检查作者格式
        if not re.match(r'^[\w\s,]+\.', ref):
            errors.append(f"参考文献 #{i+1} 作者格式不符合MLA标准")
    
    return errors

def check_table_format(doc_path: str, required_format: Dict) -> List[str]:
    """
    检查表格格式是否符合要求
    """
    errors = []
    doc = docx.Document(doc_path)
    
    # 获取表格部分的要求格式
    table_required_format = required_format.get('tables', {})
    
    # 检查表格标题和内容
    table_count = 0
    for i, table in enumerate(doc.tables):
        table_count += 1
        
        # 查找表格标题段落（通常在表格前的段落）
        table_caption = None
        for j, para in enumerate(doc.paragraphs):
            # 尝试定位表格标题
            if re.search(r'表\s*\d+[-－]\d+|Table\s*\d+[-－]\d+', para.text, re.IGNORECASE):
                # 检查标题是否在表格前面
                if j < len(doc.paragraphs) - 1:
                    # 简单检查：如果下一段是空的，可能表示表格位置
                    if not doc.paragraphs[j+1].text.strip():
                        table_caption = para
                        break
        
        # 检查是否找到表格标题
        if not table_caption:
            errors.append(f"表格 #{i+1} 缺少标题或标题格式不正确")
            continue
        
        # 检查表格标题格式
        caption_errors = _check_caption_format(table_caption, table_required_format.get('caption', {}), "表格")
        errors.extend(caption_errors)
        
        # 检查表格内容格式
        content_errors = _check_table_content_format(table)
        errors.extend(content_errors)
        
        # 检查表格编号是否按章节顺序
        number_errors = _check_table_number_format(table_caption.text)
        errors.extend(number_errors)
    
    # 检查是否有表格
    if table_count == 0:
        errors.append("文档中未找到表格")
    
    # 打印错误信息
    if errors:
        print("\n表格格式检查错误:")
        for err in errors:
            print(f"- {err}")
    
    return errors

def _check_caption_format(caption_para, required_format: Dict, caption_type: str) -> List[str]:
    """
    检查标题格式
    """
    errors = []
    
    # 检查字体
    if hasattr(caption_para, 'runs') and caption_para.runs:
        run = caption_para.runs[0]
        
        # 检查字体名称
        font_name = run.font.name
        required_zh_font = required_format.get('fonts', {}).get('zh_family')
        required_en_font = required_format.get('fonts', {}).get('en_family')
        
        if required_zh_font and not any(font in font_name for font in [required_zh_font, '黑体']):
            errors.append(f"{caption_type}标题中文字体不符合要求，应为{required_zh_font}")
        
        # 检查字体大小
        font_size = run.font.size
        required_size = required_format.get('fonts', {}).get('size')
        if required_size and font_size:
            required_pt = extract_number(required_size)
            actual_pt = font_size.pt
            if abs(actual_pt - required_pt) > 0.5:
                errors.append(f"{caption_type}标题字体大小不符合要求，应为{required_size}")
    
    # 检查对齐方式
    alignment = caption_para.alignment
    required_alignment = required_format.get('paragraph_format', {}).get('alignment')
    if required_alignment and required_alignment.lower() == 'center' and alignment != 1:  # 1表示居中
        errors.append(f"{caption_type}标题未居中显示")
    
    # 检查是否同时包含中英文标题
    if not (re.search(r'[\u4e00-\u9fa5]', caption_para.text) and 
            re.search(r'[a-zA-Z]', caption_para.text)):
        errors.append(f"{caption_type}标题应同时包含中英文")
    
    return errors

def _check_table_content_format(table) -> List[str]:
    """
    检查表格内容格式
    """
    errors = []
    
    # 检查表头是否使用黑体
    if table.rows and table.rows[0].cells:
        for cell in table.rows[0].cells:
            for para in cell.paragraphs:
                for run in para.runs:
                    if not any(font in run.font.name for font in ['黑体', 'SimHei']):
                        errors.append("表格表头应使用黑体")
                        break
    
    # 检查表格内容字体大小
    for row_idx, row in enumerate(table.rows):
        if row_idx == 0:  # 跳过表头
            continue
        for cell in row.cells:
            for para in cell.paragraphs:
                for run in para.runs:
                    # 检查中文字体
                    if re.search(r'[\u4e00-\u9fa5]', run.text) and not any(font in run.font.name for font in ['宋体', 'SimSun']):
                        errors.append("表格内容中文应使用宋体")
                    
                    # 检查英文字体
                    if re.search(r'[a-zA-Z]', run.text) and 'Times New Roman' not in run.font.name:
                        errors.append("表格内容英文应使用Times New Roman")
                    
                    # 检查字体大小
                    if run.font.size and (run.font.size.pt < 9 or run.font.size.pt > 10.5):
                        errors.append("表格内容字体大小应为5号或小5号（约10.5pt或9pt）")
    
    return errors

def _check_table_number_format(caption_text: str) -> List[str]:
    """
    检查表格编号是否按章节顺序
    """
    errors = []
    
    # 匹配表格编号格式：表x-y 或 Table x-y
    match = re.search(r'表\s*(\d+)[-－](\d+)|Table\s*(\d+)[-－](\d+)', caption_text, re.IGNORECASE)
    if not match:
        errors.append(f"表格编号格式不正确，应为'表x-y'或'Table x-y'格式")
        return errors
    
    # 提取章节号和表格序号
    if match.group(1) and match.group(2):  # 中文格式
        chapter_num = int(match.group(1))
        table_num = int(match.group(2))
    else:  # 英文格式
        chapter_num = int(match.group(3))
        table_num = int(match.group(4))
    
    # 检查章节号和表格序号是否合理
    if chapter_num <= 0 or table_num <= 0:
        errors.append(f"表格编号中章节号和表格序号应为正整数")
    
    return errors

def check_figure_format(doc_path: str, required_format: Dict) -> List[str]:
    """
    检查图片格式是否符合要求
    """
    errors = []
    doc = docx.Document(doc_path)
    
    # 获取图片部分的要求格式
    figure_required_format = required_format.get('figures', {})
    
    # 检查图片标题和内容
    figure_count = 0
    
    # 遍历段落查找图片标题
    for i, para in enumerate(doc.paragraphs):
        # 查找图片标题段落
        if re.search(r'图\s*\d+[-－]\d+|Figure\s*\d+[-－]\d+', para.text, re.IGNORECASE):
            figure_count += 1
            
            # 检查图片标题格式
            caption_errors = _check_caption_format(para, figure_required_format.get('caption', {}), "图片")
            errors.extend(caption_errors)
            
            # 检查图片编号是否按章节顺序
            number_errors = _check_figure_number_format(para.text)
            errors.extend(number_errors)
            
            # 检查图片标题位置（应在图片下方）
            position = figure_required_format.get('caption', {}).get('position')
            if position == 'below':
                # 简单检查：如果上一段是空的，可能表示图片位置
                if i > 0 and not doc.paragraphs[i-1].text.strip():
                    pass  # 符合要求
                else:
                    errors.append(f"图片标题'{para.text}'应位于图片下方")
    
    # 检查是否有图片
    if figure_count == 0:
        errors.append("文档中未找到图片")
    
    # 打印错误信息
    if errors:
        print("\n图片格式检查错误:")
        for err in errors:
            print(f"- {err}")
    
    return errors

def _check_figure_number_format(caption_text: str) -> List[str]:
    """
    检查图片编号是否按章节顺序
    """
    errors = []
    
    # 匹配图片编号格式：图x-y 或 Figure x-y
    match = re.search(r'图\s*(\d+)[-－](\d+)|Figure\s*(\d+)[-－]\d+', caption_text, re.IGNORECASE)
    if not match:
        errors.append(f"图片编号格式不正确，应为'图x-y'或'Figure x-y'格式")
        return errors
    
    # 提取章节号和图片序号
    if match.group(1) and match.group(2):  # 中文格式
        chapter_num = int(match.group(1))
        figure_num = int(match.group(2))
    else:  # 英文格式
        chapter_num = int(match.group(3))
        figure_num = int(match.group(4))
    
    # 检查章节号和图片序号是否合理
    if chapter_num <= 0 or figure_num <= 0:
        errors.append(f"图片编号中章节号和图片序号应为正整数")
    
    return errors

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
        
        # 如果段落类型为other，则跳过格式检查
        if para_type == "other":
            continue

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
            if len(actual_value) == 0:
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

def remark_para_type(doc_path: str, model_name) -> ParagraphManager:
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
            # 使用大模型预测段落类型
            format_auxiliary = FormatAuxiliary(model = model_name)
            # 调用大模型预测类型
            response = format_auxiliary.predict_location(doc_content, para_string, doc_content_sent)
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
    
    # 使用线程池并发处理，限制最大线程数为10
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        doc_content_sent = False
        
        # 创建任务列表
        tasks = []
        for i, para in enumerate(paras_info_json_zh):
            tasks.append((i, para, doc_content_sent, paragraph_manager))
            doc_content_sent = True  # 更新全文标志
        
        # 分批提交任务，每批最多5个任务
        batch_size = 5
        for i in range(0, len(tasks), batch_size):
            batch_tasks = tasks[i:i+batch_size]
            batch_futures = [executor.submit(process_paragraph, *task) for task in batch_tasks]
            futures.extend(batch_futures)
            
            # 等待当前批次完成
            for future in concurrent.futures.as_completed(batch_futures):
                try:
                    future.result()  # 确保任务完成
                except Exception as e:
                    print(f"Error in thread pool task: {e}")
    
    return paragraph_manager


# debug
# def check_format(doc_path:str, required_format:dict, llm:LLMs):
#     print(f"[LOG] 当前工作目录: {os.getcwd()}")
#     doc_path_full = os.path.abspath(doc_path)
#     print(f"[LOG] 尝试打开文档: {doc_path_full}")
#     if not os.path.exists(doc_path_full):
#         print(f"[LOG] 文档文件不存在: {doc_path_full}")
#     doc_info = docx_parser.extract_section_info(doc_path)
#     # 初始化段落管理器
#     paragraph_manager = ParagraphManager()
#     # 读取doc的段落信息
#     paragraph_manager = extract_para_info.extract_para_format_info(doc_path, paragraph_manager)
#     # 重分配段落类型
#     # paragraph_manager = remark_para_type(doc_path, llm)
#     # 修改rusult到英文
#     with open("../result.json", "r", encoding="utf-8") as f:
#         data = json.load(f)
#         result = paragraph_manager.to_english_dict(data)
#     # 写回json
#     with open("../result.json", "w", encoding="utf-8") as f:
#         json.dump(result, f, ensure_ascii=False, indent=4)
#     paragraph_manager = ParagraphManager.build_from_json_file("../result.json")
#     # paras_info_json_zh = paragraph_manager.to_chinese_dict()
#     # 对齐段落信息和格式信息同Config
#     # print(paras_info_dict)
#     # 检查格式是否符合要求
#     check_paper_format(doc_info, required_format)
#     #  检查段落格式
#     check_main_format(paragraph_manager, required_format)
#     #  检查表格样式
#     check_table_format(doc_path, required_format)
#     # 检查图片样式
#     check_figure_format(doc_path, required_format)
#     # 检查引用样式和参考文献
#     check_reference_format(doc_path, required_format)

def check_format(doc_path: str, config_path: str, model_name: str) -> List[str]:
    # 加载配置
    required_format = load_config(config_path)
    
    # 获取文档信息
    doc_info = docx_parser.extract_section_info(doc_path)
    
    # 初始化段落管理器
    paragraph_manager = ParagraphManager()
    paragraph_manager = extract_para_info.extract_para_format_info(doc_path, paragraph_manager)
    
    # 重新标记段落类型
    paragraph_manager = remark_para_type(doc_path, model_name)
    
    # 收集所有错误
    errors = []
    
    # 检查基本格式
    paper_errors = check_paper_format(doc_info, required_format)
    if paper_errors:
        errors.extend(paper_errors)
        
    # 检查段落格式
    para_errors = check_main_format(paragraph_manager, required_format)
    if para_errors:
        errors.extend(para_errors)
        
    # 检查表格格式
    table_errors = check_table_format(doc_path, required_format)
    if table_errors:
        errors.extend(table_errors)
        
    # 检查图片格式
    figure_errors = check_figure_format(doc_path, required_format)
    if figure_errors:
        errors.extend(figure_errors)
        
    # 检查引用格式
    ref_errors = check_reference_format(doc_path, required_format)
    if ref_errors:
        errors.extend(ref_errors)
    
    print(f"[LOG] 文件格式检查结果: {errors}")
    return errors

# llm = LLMs()
# llm.set_model('qwen-plus')
# required_format = load_config('..//config.json')
# check_format('..//test.docx', required_format, llm)
