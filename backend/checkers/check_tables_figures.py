import re, docx
from typing import Dict, List
from backend.utils.utils import extract_number

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
