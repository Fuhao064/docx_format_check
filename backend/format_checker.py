import docx 
from docx import Document
import extract_para_info, docx_parser
import json
from typing import Dict, List, Tuple, Union, Optional
from agents.format_agent import FormatAgent
from para_type import ParagraphManager,ParsedParaType
import os,concurrent,re
from utils import are_values_equal, extract_number_from_string
from config_utils import load_config, save_config, update_config

def is_value_equal(expected, actual, key):
    """比较两个值是否相等，考虑到不同表示形式的数值"""
    # 对特定的key做特殊处理
    if key.lower() == 'size':
        # 处理字号的特殊情况
        expected_num = extract_number(expected)
        actual_num = extract_number(actual)
        if expected_num is not None and actual_num is not None:
            return abs(expected_num - actual_num) < 0.5  # 允许0.5pt的误差
    
    # 检查字符串类型的相等性
    if isinstance(expected, str) and isinstance(actual, str):
        # 清除单位并转为小写进行比较
        expected_clean = expected.lower().strip()
        actual_clean = actual.lower().strip()
        
        # 如果完全相等，直接返回True
        if expected_clean == actual_clean:
            return True
        
        # 尝试提取数值部分进行比较
        expected_num = extract_number(expected)
        actual_num = extract_number(actual)
        if expected_num is not None and actual_num is not None:
            return abs(expected_num - actual_num) < 0.1
    
    # 处理数值类型或混合类型
    elif isinstance(expected, (int, float)) or isinstance(actual, (int, float)):
        expected_num = extract_number(expected)
        actual_num = extract_number(actual)
        if expected_num is not None and actual_num is not None:
            return abs(expected_num - actual_num) < 0.1
    
    # 默认使用原有方法
    return are_values_equal(expected, actual, key)

def extract_number(value):
    """从字符串中提取数字值，支持多种单位和格式"""
    # 如果已经是数字类型，直接返回
    if isinstance(value, (int, float)):
        return float(value)
    
    # 转换为字符串
    value_str = str(value).lower().strip()
    
    # 常见单位与对应的换算系数（相对于厘米）
    unit_factors = {
        'cm': 1.0,    # 厘米
        'mm': 0.1,    # 毫米
        'dm': 10.0,   # 分米
        'm': 100.0,   # 米
        'pt': 1.0,    # 点，对于字体大小不进行换算
        'in': 2.54,   # 英寸
        'inch': 2.54, # 英寸
        '寸': 3.33     # 中国传统单位
    }
    
    # 尝试提取数字和单位
    match = re.search(r'([-+]?\d*\.?\d+)\s*([a-z寸]+)?', value_str)
    if not match:
        return extract_number_from_string(value)
    
    num_value = float(match.group(1))
    unit = match.group(2) if match.group(2) else ''  # 无单位的情况
    
    # 如果没有单位，直接返回数值
    if not unit:
        return num_value
    
    # 应用单位转换系数
    factor = unit_factors.get(unit, 1.0)
    return num_value * factor

def check_paper_format(doc_info: Dict, required_format: Dict) -> List[Dict]:
    """检查文档基本格式"""
    errors = []
    
    # 获取纸张设置
    paper_format = required_format.get('paper_format', {})
    if not paper_format:
        return errors
    
    # 检查页面大小
    expected_page_size = paper_format.get('page_size', None)
    if expected_page_size:
        actual_width = doc_info.get('page_width', None)
        actual_height = doc_info.get('page_height', None)
        
        expected_width = extract_number(expected_page_size.get('width', '0'))
        expected_height = extract_number(expected_page_size.get('height', '0'))
        
        if expected_width and expected_height:
            if actual_width and actual_height:
                width_diff = abs(actual_width - expected_width)
                height_diff = abs(actual_height - expected_height)
                
                if width_diff > 0.5 or height_diff > 0.5:  # 允许0.5cm的误差
                    errors.append({
                        'message': f'页面大小不符合要求，要求{expected_width}×{expected_height}厘米，实际为{actual_width}×{actual_height}厘米',
                        'location': '文档全局设置'
                    })
    
    # 检查页边距
    expected_margins = paper_format.get('margins', None)
    if expected_margins:
        margin_keys = ['top', 'bottom', 'left', 'right']
        
        for key in margin_keys:
            expected_value = extract_number(expected_margins.get(key, '0'))
            actual_value = doc_info.get(f'margin_{key}', None)
            
            if expected_value and actual_value:
                margin_diff = abs(actual_value - expected_value)
                
                if margin_diff > 0.1:  # 允许0.1cm的误差
                    margin_name = {
                        'top': '上边距',
                        'bottom': '下边距',
                        'left': '左边距',
                        'right': '右边距'
                    }.get(key, key)
                    
                    errors.append({
                        'message': f'{margin_name}不符合要求，要求{expected_value}厘米，实际为{actual_value}厘米',
                        'location': '文档全局设置'
                    })
    
    return errors

def check_reference_format(doc_path: str, required_format: Dict) -> List[Dict]:
    """检查引用和参考文献格式"""
    errors = []
    
    try:
        doc = docx.Document(doc_path)
        
        # 获取参考文献格式要求
        reference_format = required_format.get('reference_format', {})
        if not reference_format:
            return errors
        
        # 获取引用样式
        citation_style = reference_format.get('citation_style', '').lower()
        if not citation_style:
            return errors
        
        # 查找参考文献部分
        references_start = False
        references = []
        
        for para in doc.paragraphs:
            text = para.text.strip()
            
            # 标识参考文献部分的开始
            if text.startswith('参考文献') or text.lower().startswith('references'):
                references_start = True
                continue
            
            # 收集参考文献条目
            if references_start and text:
                references.append(text)
        
        # 检查是否有参考文献
        if not references:
            errors.append({
                'message': '未找到参考文献部分或参考文献为空',
                'location': '文档末尾部分'
            })
            return errors
        
        # 根据不同引用样式检查参考文献格式
        if 'gb' in citation_style or 'gbt' in citation_style:
            # 检查GB/T格式
            ref_errors = _check_gbt_references(references, citation_style)
            for i, error in enumerate(ref_errors):
                if isinstance(error, dict):
                    errors.append(error)
                else:
                    errors.append({
                        'message': error,
                        'location': f"参考文献[{i+1}]"
                    })
        
        elif 'apa' in citation_style:
            # 检查APA格式
            ref_errors = _check_apa_references(references)
            for i, error in enumerate(ref_errors):
                if isinstance(error, dict):
                    errors.append(error)
                else:
                    errors.append({
                        'message': error,
                        'location': f"参考文献[{i+1}]"
                    })
        
        elif 'mla' in citation_style:
            # 检查MLA格式
            ref_errors = _check_mla_references(references)
            for i, error in enumerate(ref_errors):
                if isinstance(error, dict):
                    errors.append(error)
                else:
                    errors.append({
                        'message': error,
                        'location': f"参考文献[{i+1}]"
                    })
        
        else:
            errors.append({
                'message': f"不支持的引用样式: {citation_style}",
                'location': '参考文献格式设置'
            })
    
    except Exception as e:
        errors.append({
            'message': f"检查参考文献格式时出错: {str(e)}",
            'location': '参考文献部分'
        })
    
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
    # 更灵活的正则表达式，允许一些常见变体
    pattern = r'^\[\d+\]\s+[\w\s,]+\.\s+.+\[J(/OL)?\]\.\s+.+,\s+\d{4}(,\s+\d+(\(\d+\))?)?(\:\s*\d+(-\d+)?)?\.?$'
    return bool(re.match(pattern, ref, re.UNICODE))

def _check_book_format(ref: str, standard: str) -> bool:
    """检查专著格式"""
    # GB/T 7714-2015格式: [序号] 作者. 书名[M]. 版本(第1版不标注). 出版地: 出版社, 出版年: 起止页码.
    # 更灵活的模式
    pattern = r'^\[\d+\]\s+[\w\s,]+\.\s+.+\[M\]\.\s+.*(\:\s+.+,\s+\d{4}(\:\s*\d+(-\d+)?)?)?\.?$'
    return bool(re.match(pattern, ref, re.UNICODE))

def _check_thesis_format(ref: str, standard: str) -> bool:
    """检查学位论文格式"""
    # GB/T 7714-2015格式: [序号] 作者. 题名[D]. 保存地: 保存单位, 出版年.
    # 更灵活的模式
    pattern = r'^\[\d+\]\s+[\w\s,]+\.\s+.+\[D\]\.\s+.*(\:\s+.+,\s+\d{4})?\.?$'
    return bool(re.match(pattern, ref, re.UNICODE))

def _check_conference_format(ref: str, standard: str) -> bool:
    """检查会议论文格式"""
    # GB/T 7714-2015格式: [序号] 作者. 题名[C]. 会议名, 会议地点, 会议年份. 出版地: 出版者, 出版年: 起止页码.
    # 更灵活的模式
    pattern = r'^\[\d+\]\s+[\w\s,]+\.\s+.+\[C(/OL)?\]\.\s+.+(,\s+.+,\s+\d{4})?\.(\s+.+\:\s+.+,\s+\d{4}(\:\s*\d+(-\d+)?)?)?\.?$'
    return bool(re.match(pattern, ref, re.UNICODE))

def _check_electronic_format(ref: str, standard: str) -> bool:
    """检查电子资源格式"""
    # GB/T 7714-2015格式: [序号] 作者. 题名[EB/OL]. 出版地: 出版者, 出版年[引用日期]. 获取和访问路径.
    # 更灵活的模式，网址部分可选
    pattern = r'^\[\d+\]\s+[\w\s,]+\.\s+.+\[EB/OL\]\.(\s+.+\:\s+.+,\s+\d{4})?\s*(\[\d{4}-\d{2}-\d{2}\])?\.(\s+https?://.*)?$'
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

def check_table_format(doc_path: str, required_format: Dict) -> List[Dict]:
    """检查表格格式"""
    errors = []
    
    try:
        doc = docx.Document(doc_path)
        
        # 获取表格格式要求
        table_format = required_format.get('table_format', {})
        if not table_format:
            return errors
        
        # 遍历文档中的表格
        table_count = 0
        for table in doc.tables:
            table_count += 1
            
            # 检查表格内容格式
            content_errors = _check_table_content_format(table)
            for error in content_errors:
                if isinstance(error, dict):
                    error['location'] = f"表{table_count}: {error.get('location', '')}"
                    errors.append(error)
                else:
                    errors.append({
                        'message': error,
                        'location': f"表{table_count}"
                    })
        
        # 遍历文档中的段落，查找表格标题
        for i, para in enumerate(doc.paragraphs):
            text = para.text.strip()
            
            # 检查是否为表格标题
            if text.startswith('表') or text.lower().startswith('table'):
                # 检查标题格式
                caption_errors = _check_caption_format(para, table_format, 'table')
                
                # 匹配表格编号
                match = re.search(r'表\s*(\d+[-.]?\d*)', text)
                table_num = match.group(1) if match else f"{i+1}"
                
                for error in caption_errors:
                    if isinstance(error, dict):
                        error['location'] = f"表{table_num}标题: {error.get('location', '')}"
                        errors.append(error)
                    else:
                        errors.append({
                            'message': error,
                            'location': f"表{table_num}标题"
                        })
                
                # 检查表格编号格式
                number_errors = _check_table_number_format(text)
                for error in number_errors:
                    if isinstance(error, dict):
                        error['location'] = f"表{table_num}编号: {error.get('location', '')}"
                        errors.append(error)
                    else:
                        errors.append({
                            'message': error,
                            'location': f"表{table_num}编号"
                        })
    
    except Exception as e:
        errors.append({
            'message': f"检查表格格式时出错: {str(e)}",
            'location': '全文表格'
        })
    
    return errors

def _check_caption_format(caption_para, required_format: Dict, caption_type: str) -> List[Dict]:
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
            errors.append({
                'message': f"{caption_type}标题中文字体不符合要求，应为{required_zh_font}",
                'location': '标题字体'
            })
        
        # 检查字体大小
        font_size = run.font.size
        required_size = required_format.get('fonts', {}).get('size')
        if required_size and font_size:
            required_pt = extract_number(required_size)
            actual_pt = font_size.pt
            if abs(actual_pt - required_pt) > 0.5:
                errors.append({
                    'message': f"{caption_type}标题字体大小不符合要求，应为{required_size}",
                    'location': '标题字体大小'
                })
    
    # 检查对齐方式
    alignment = caption_para.alignment
    required_alignment = required_format.get('paragraph_format', {}).get('alignment')
    if required_alignment and required_alignment.lower() == 'center' and alignment != 1:  # 1表示居中
        errors.append({
            'message': f"{caption_type}标题未居中显示",
            'location': '标题对齐'
        })
    
    # 检查是否同时包含中英文标题
    if not (re.search(r'[\u4e00-\u9fa5]', caption_para.text) and 
            re.search(r'[a-zA-Z]', caption_para.text)):
        errors.append({
            'message': f"{caption_type}标题应同时包含中英文",
            'location': '标题语言'
        })
    
    return errors

def _check_table_content_format(table) -> List[Dict]:
    """检查表格内容格式"""
    errors = []
    
    try:
        row_count = len(table.rows)
        col_count = len(table.columns)
        
        # 检查表格是否为空
        if row_count == 0 or col_count == 0:
            errors.append({
                'message': '表格为空',
                'location': '表格内容'
            })
            return errors
        
        # 检查表格单元格是否为空
        empty_cells = []
        for i, row in enumerate(table.rows):
            for j, cell in enumerate(row.cells):
                if not cell.text.strip():
                    empty_cells.append(f"行{i+1}列{j+1}")
        
        if empty_cells:
            if len(empty_cells) <= 3:
                cell_str = '、'.join(empty_cells)
            else:
                cell_str = f"{empty_cells[0]}、{empty_cells[1]}等{len(empty_cells)}处"
            
            errors.append({
                'message': f'表格存在空单元格',
                'location': f"表格内容: {cell_str}"
            })
        
        # 检查表格行列一致性
        inconsistent_rows = []
        first_row_cell_count = len(table.rows[0].cells)
        
        for i, row in enumerate(table.rows):
            if len(row.cells) != first_row_cell_count:
                inconsistent_rows.append(i+1)
        
        if inconsistent_rows:
            if len(inconsistent_rows) <= 3:
                rows_str = '、'.join(map(str, inconsistent_rows))
            else:
                rows_str = f"{inconsistent_rows[0]}、{inconsistent_rows[1]}等{len(inconsistent_rows)}行"
            
            errors.append({
                'message': '表格行列不一致',
                'location': f"表格内容: 第{rows_str}"
            })
    
    except Exception as e:
        errors.append({
            'message': f"检查表格内容时出错: {str(e)}",
            'location': '表格内容'
        })
    
    return errors

def _check_table_number_format(caption_text: str) -> List[Dict]:
    """
    检查表格编号是否按章节顺序
    """
    errors = []
    
    # 匹配表格编号格式：表x-y 或 Table x-y
    match = re.search(r'表\s*(\d+)[-－](\d+)|Table\s*(\d+)[-－](\d+)', caption_text, re.IGNORECASE)
    if not match:
        errors.append({
            'message': f"表格编号格式不正确，应为'表x-y'或'Table x-y'格式",
            'location': '表格编号'
        })
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
        errors.append({
            'message': f"表格编号中章节号和表格序号应为正整数",
            'location': '表格编号'
        })
    
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
    """检查摘要格式"""
    errors = []
    
    # 查找摘要段落
    abstract_paras = []
    abstract_content_paras = []
    
    for para in paragraph_manager.paragraphs:
        if para.type == ParsedParaType.ABSTRACT_ZH or para.content.strip().startswith('摘要'):
            abstract_paras.append(para)
        elif para.type == ParsedParaType.ABSTRACT_CONTENT_ZH:
            abstract_content_paras.append(para)
    
    # 检查是否存在摘要
    if not abstract_paras:
        errors.append({
            'message': '文档中缺少摘要',
            'location': '文档开头部分'
        })
        return errors
    
    # 检查是否有摘要内容
    if not abstract_content_paras:
        errors.append({
            'message': '文档中缺少摘要内容',
            'location': '摘要标题后'
        })
        return errors
    
    # 检查摘要内容长度
    for content_para in abstract_content_paras:
        abstract_text = content_para.content.strip()
        if len(abstract_text) < 10:  # 假设摘要至少应该有10个字符
            errors.append({
                'message': '摘要内容过短',
                'location': '摘要部分'
            })
    
    return errors

def check_keywords(paragraph_manager:ParagraphManager):
    """检查关键词格式"""
    errors = []
    
    # 查找关键词段落
    keyword_paras = []
    for para in paragraph_manager.paragraphs:
        para_text = para.content.strip()
        if para_text.startswith('关键词') or para_text.startswith('Keywords'):
            keyword_paras.append(para)
    
    # 检查是否存在关键词
    if not keyword_paras:
        errors.append({
            'message': '文档中缺少关键词',
            'location': '摘要之后'
        })
        return errors
    
    # 检查关键词内容
    keyword_para = keyword_paras[0]
    keyword_text = keyword_para.content.strip()
    
    # 检查是否有足够的关键词（假设至少3个）
    if '：' in keyword_text:
        keywords = keyword_text.split('：')[1].split('；')
    elif ':' in keyword_text:
        keywords = keyword_text.split(':')[1].split(';')
    else:
        keywords = []
    
    if len(keywords) < 3:
        errors.append({
            'message': '关键词数量不足，建议至少提供3个关键词',
            'location': '关键词部分'
        })
    
    return errors

def check_main_format(paragraph_manager:ParagraphManager, required_format:Dict, check_abstract_keywords:bool=True) -> List[Dict]:
    """
    检查主要文档格式
    
    参数:
    paragraph_manager: 段落管理器
    required_format: 格式要求
    check_abstract_keywords: 是否检查摘要和关键词，默认为True
    """
    errors = []
    
    # 检查摘要格式
    if check_abstract_keywords:
        abstract_errors = check_abstract(paragraph_manager)
        if abstract_errors:
            errors.extend(abstract_errors)
        
        # 检查关键词格式
        keyword_errors = check_keywords(paragraph_manager)
        if keyword_errors:
            errors.extend(keyword_errors)
    
    # 获取段落格式要求
    paragraph_format = required_format.get('paragraph_format', {})
    if not paragraph_format:
        return errors
    
    # 获取各类型段落的格式要求
    title_format = paragraph_format.get('title', {})
    heading1_format = paragraph_format.get('heading1', {})
    heading2_format = paragraph_format.get('heading2', {})
    heading3_format = paragraph_format.get('heading3', {})
    body_format = paragraph_format.get('body', {})
    
    # 遍历所有段落，检查格式 - 修改为正确的列表迭代方式
    for para in paragraph_manager.paragraphs:
        para_type = para.type.value if hasattr(para, 'type') else ''
        para_text = para.content if hasattr(para, 'content') else ''
        para_attributes = para.meta if hasattr(para, 'meta') else {}
        
        # 根据段落类型选择相应的格式要求
        expected_format = {}
        location_prefix = ""
        
        if para_type == 'title_zh' or para_type == 'title_en':
            expected_format = title_format
            location_prefix = "标题"
        elif para_type == 'heading1':
            expected_format = heading1_format
            location_prefix = "一级标题"
        elif para_type == 'heading2':
            expected_format = heading2_format
            location_prefix = "二级标题"
        elif para_type == 'heading3':
            expected_format = heading3_format
            location_prefix = "三级标题"
        elif para_type == 'body':
            expected_format = body_format
            location_prefix = "正文"
        
        if not expected_format:
            continue
        
        # 递归检查格式
        format_errors = _recursive_check(para_attributes, expected_format)
        for error_path, error_msg in format_errors:
            location = f"{location_prefix}: \"{para_text[:20]}{'...' if len(para_text) > 20 else ''}\""
            errors.append({
                'message': error_msg,
                'location': location
            })
    
    return errors

def _recursive_check(actual, expected):
    """
    递归检查嵌套字典的字段。
    返回格式为[(key, error_message), ...]的列表
    """
    errors = []

    for key, expected_value in expected.items():
        actual_value = actual.get(key)

        # 如果字段不存在
        if actual_value is None:
            errors.append((key, f"缺少必需字段: '{key}'"))
            continue

        # 如果字段是列表类型，优先检查长度
        if isinstance(actual_value, list):
            if len(actual_value) > 1:
                errors.append((key, f"字段 '{key}' 存在多个值: {actual_value}"))
                continue
            if len(actual_value) == 0:
                continue
            actual_value = actual_value[0]  # 取第一个值进行比较

        # 递归处理嵌套字典
        if isinstance(expected_value, dict):
            if not isinstance(actual_value, dict):
                errors.append((key, f"字段类型不匹配: '{key}' 应为字典类型，实际为 {type(actual_value).__name__}"))
                continue

            # 递归检查嵌套字段
            deeper_errors = _recursive_check(actual_value, expected_value)
            for err_key, err_msg in deeper_errors:
                errors.append((f"{key}.{err_key}", err_msg))

        # 检查值是否匹配
        else:
            if not is_value_equal(expected_value, actual_value, key):
                errors.append((key, f"'{key}' 不匹配: 要求 {expected_value}, 实际 {actual_value}"))

    return errors

def remark_para_type(doc_path: str, format_agent: FormatAgent) -> ParagraphManager:
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
            response = format_agent.predict_location(doc_content, para_string, doc_content_sent)
            
            # 直接使用response字典，无需再次解析
            response_dict = response
            
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

def check_format(doc_path: str, config_path: str, format_agent: FormatAgent) -> List[dict]:
    # 加载配置
    required_format = load_config(config_path)
    
    # 获取文档信息
    doc_info = docx_parser.extract_section_info(doc_path)
    
    # 初始化段落管理器
    paragraph_manager = ParagraphManager()
    paragraph_manager = extract_para_info.extract_para_format_info(doc_path, paragraph_manager)
    
    # 重新标记段落类型
    paragraph_manager = remark_para_type(doc_path, format_agent)
    
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
    
    # 转换错误格式为包含message和location的字典
    formatted_errors = []
    for error in errors:
        if isinstance(error, dict) and 'message' in error and 'location' in error:
            # 如果错误已经是正确格式，直接添加
            formatted_errors.append(error)
        elif isinstance(error, str):
            # 尝试从字符串中提取位置信息
            location_match = re.search(r'位置[:：]?\s*(.+?)\s*$', error)
            if location_match:
                message = error[:location_match.start()].strip()
                location = location_match.group(1).strip()
                formatted_errors.append({
                    'message': message,
                    'location': location
                })
            else:
                # 无法提取位置信息，使用通用位置
                formatted_errors.append({
                    'message': error,
                    'location': '未指定位置'
                })
        else:
            # 处理其他类型的错误
            formatted_errors.append({
                'message': str(error),
                'location': '未指定位置'
            })
    
    print(f"[LOG] 文件格式检查结果: {formatted_errors}")
    return formatted_errors, paragraph_manager
