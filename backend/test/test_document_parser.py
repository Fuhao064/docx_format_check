"""
测试文档信息抽取和段落位置匹配
"""
import sys
import os
import json
from pathlib import Path

# 添加backend目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from preparation.para_type import ParagraphManager, ParsedParaType
from preparation.extract_para_info import extract_para_format_info


def normalize_for_comparison(value):
    """标准化值以便比较"""
    if isinstance(value, set):
        value = list(value)
    if isinstance(value, list):
        # 对列表进行排序
        try:
            return sorted(value)
        except TypeError:
            return value
    if isinstance(value, dict):
        return {k: normalize_for_comparison(v) for k, v in value.items()}
    if isinstance(value, float):
        # 浮点数比较时考虑精度问题
        return round(value, 2)
    return value


def compare_fonts(actual_fonts, expected_fonts, para_id):
    """比较字体信息"""
    errors = []

    # 检查size
    if 'size' in expected_fonts:
        actual_size = normalize_for_comparison(actual_fonts.get('size', []))
        expected_size = normalize_for_comparison(expected_fonts['size'])
        if actual_size != expected_size:
            errors.append(f"  字号不匹配: 期望 {expected_size}, 实际 {actual_size}")

    # 检查bold
    if 'bold' in expected_fonts:
        actual_bold = normalize_for_comparison(actual_fonts.get('bold', []))
        expected_bold = normalize_for_comparison(expected_fonts['bold'])
        if actual_bold != expected_bold:
            errors.append(f"  加粗不匹配: 期望 {expected_bold}, 实际 {actual_bold}")

    # 检查italic
    if 'italic' in expected_fonts:
        actual_italic = normalize_for_comparison(actual_fonts.get('italic', []))
        expected_italic = normalize_for_comparison(expected_fonts['italic'])
        if actual_italic != expected_italic:
            errors.append(f"  斜体不匹配: 期望 {expected_italic}, 实际 {actual_italic}")

    # 检查color
    if 'color' in expected_fonts:
        actual_color = normalize_for_comparison(actual_fonts.get('color', []))
        expected_color = normalize_for_comparison(expected_fonts['color'])
        # 标准化颜色格式
        def normalize_color(c):
            if isinstance(c, str):
                c = c.lower()
                if c in ['auto', '000000', '0', '#0', 'black']:
                    return '#black'
                if not c.startswith('#'):
                    return f'#{c}'
            return c

        actual_color = [normalize_color(c) for c in actual_color if c]
        expected_color = [normalize_color(c) for c in expected_color if c]
        if actual_color != expected_color:
            errors.append(f"  颜色不匹配: 期望 {expected_color}, 实际 {actual_color}")

    # 检查zh_family
    if 'zh_family' in expected_fonts:
        actual_zh = normalize_for_comparison(actual_fonts.get('zh_family', []))
        expected_zh = normalize_for_comparison(expected_fonts['zh_family'])
        if actual_zh != expected_zh:
            errors.append(f"  中文字体不匹配: 期望 {expected_zh}, 实际 {actual_zh}")

    # 检查en_family
    if 'en_family' in expected_fonts:
        actual_en = normalize_for_comparison(actual_fonts.get('en_family', []))
        expected_en = normalize_for_comparison(expected_fonts['en_family'])
        if actual_en != expected_en:
            errors.append(f"  英文字体不匹配: 期望 {expected_en}, 实际 {actual_en}")

    return errors


def compare_paragraph_format(actual, expected, para_id):
    """比较段落格式"""
    errors = []

    if 'paragraph_format' not in actual:
        errors.append(f"  缺少paragraph_format字段")
        return errors

    actual_pf = actual['paragraph_format']
    expected_pf = expected['paragraph_format']

    for key in ['alignment', 'first_line_indent', 'left_indent', 'right_indent',
                'before_spacing', 'after_spacing', 'line_spacing']:
        if key in expected_pf:
            actual_val = actual_pf.get(key)
            expected_val = expected_pf[key]

            # 特殊处理line_spacing
            if key == 'line_spacing':
                # 提取数字部分进行比较
                if isinstance(actual_val, str):
                    import re
                    match = re.search(r'(\d+\.?\d*)', actual_val)
                    if match:
                        actual_val = float(match.group(1))
                if isinstance(expected_val, str):
                    import re
                    match = re.search(r'(\d+\.?\d*)', expected_val)
                    if match:
                        expected_val = float(match.group(1))

            if actual_val != expected_val:
                errors.append(f"  {key}不匹配: 期望 {expected_val}, 实际 {actual_val}")

    return errors


def compare_paragraphs(actual_data, expected_data):
    """比较实际输出和期望输出"""
    errors = []

    if len(actual_data) != len(expected_data):
        errors.append(f"段落数量不匹配: 期望 {len(expected_data)}, 实际 {len(actual_data)}")
        return errors

    for i, (actual, expected) in enumerate(zip(actual_data, expected_data)):
        para_id = actual.get('id', f'para{i}')
        expected_id = expected.get('id', f'para{i}')

        if para_id != expected_id:
            errors.append(f"{para_id}: ID不匹配, 期望 {expected_id}")

        # 比较type
        actual_type = actual.get('type')
        expected_type = expected.get('type')
        if actual_type != expected_type:
            errors.append(f"{para_id}: type不匹配, 期望 {expected_type}, 实际 {actual_type}")

        # 比较content
        actual_content = actual.get('content', '')
        expected_content = expected.get('content', '')
        if actual_content != expected_content:
            errors.append(f"{para_id}: content不匹配")
            errors.append(f"  期望: {expected_content[:50]}...")
            errors.append(f"  实际: {actual_content[:50]}...")

        # 比较meta
        actual_meta = actual.get('meta', {})
        expected_meta = expected.get('meta', {})

        # 比较段落格式
        pf_errors = compare_paragraph_format(actual_meta, expected_meta, para_id)
        errors.extend(pf_errors)

        # 比较字体信息
        if 'fonts' in expected_meta:
            actual_fonts = actual_meta.get('fonts', {})
            expected_fonts = expected_meta['fonts']
            font_errors = compare_fonts(actual_fonts, expected_fonts, para_id)
            errors.extend(font_errors)

    return errors


def main():
    # 获取当前目录
    test_dir = Path(__file__).parent
    doc_path = test_dir / "测试引擎.docx"
    ground_truth_path = test_dir / "ground_truth.json"

    if not doc_path.exists():
        print(f"错误: 测试文档不存在: {doc_path}")
        return 1

    if not ground_truth_path.exists():
        print(f"错误: ground_truth文件不存在: {ground_truth_path}")
        return 1

    # 加载ground_truth
    with open(ground_truth_path, 'r', encoding='utf-8') as f:
        ground_truth = json.load(f)

    print("=" * 60)
    print("开始测试文档信息抽取和段落位置匹配")
    print("=" * 60)
    print(f"测试文档: {doc_path}")
    print(f"期望段落数: {len(ground_truth.get('paragraphs', []))}")
    print("=" * 60)

    # 创建ParagraphManager并提取信息
    manager = ParagraphManager()
    extract_para_format_info(str(doc_path), manager)

    # 转换为字典格式
    actual_data = manager.to_dict()

    print("\n" + "=" * 60)
    print("实际提取结果")
    print("=" * 60)
    print(f"实际段落数: {len(actual_data)}")

    # 显示前几个段落的摘要信息
    for i, para in enumerate(actual_data[:5]):
        print(f"\n段落 {i} ({para.get('id')}):")
        print(f"  类型: {para.get('type')}")
        print(f"  内容: {para.get('content', '')[:50]}...")
        if 'meta' in para and 'paragraph_format' in para['meta']:
            pf = para['meta']['paragraph_format']
            print(f"  对齐: {pf.get('alignment')}")
        if 'meta' in para and 'fonts' in para['meta']:
            fonts = para['meta']['fonts']
            print(f"  字号: {fonts.get('size')}")
            print(f"  加粗: {fonts.get('bold')}")

    print("\n" + "=" * 60)
    print("对比结果")
    print("=" * 60)

    expected_paragraphs = ground_truth.get('paragraphs', [])
    errors = compare_paragraphs(actual_data, expected_paragraphs)

    if errors:
        print(f"\n发现 {len(errors)} 个错误:")
        for error in errors[:20]:  # 只显示前20个错误
            print(error)
        if len(errors) > 20:
            print(f"... 还有 {len(errors) - 20} 个错误未显示")

        # 保存实际结果用于调试
        output_path = test_dir / "actual_output.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(actual_data, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n实际结果已保存到: {output_path}")

        return 1
    else:
        print("\n✓ 所有测试通过!")
        return 0


if __name__ == '__main__':
    sys.exit(main())
