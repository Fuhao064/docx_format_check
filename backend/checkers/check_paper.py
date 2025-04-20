from typing import Dict, List
from utils.utils import extract_number

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