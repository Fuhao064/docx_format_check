"""
使用 docx2python 提取文档层级结构的测试脚本
与 python-docx 对比展示
"""
import sys
import os
import json
from pathlib import Path

# 添加backend目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from docx2python import docx2python
from docx import Document
from docx.oxml.ns import qn


def extract_with_docx2python(docx_path):
    """使用 docx2python 提取文档结构和内容"""
    print("=" * 60)
    print("使用 docx2python 提取文档")
    print("=" * 60)

    result = docx2python(docx_path)

    # 提取文档属性
    print("\n【文档属性】")
    print(f"标题: {result.properties.get('title', 'N/A')}")
    print(f"作者: {result.properties.get('author', 'N/A')}")
    print(f"创建时间: {result.properties.get('created', 'N/A')}")

    # 提取正文内容（层级结构）
    print("\n【文档正文 - 层级结构】")
    print(f"总段落数: {len(result.body)}")

    for i, para in enumerate(result.body[:10]):  # 显示前10段
        print(f"\n  [{i}] 类型: {type(para).__name__}")
        if isinstance(para, str):
            print(f"      内容: {para[:100]}...")
        elif isinstance(para, list):
            print(f"      层级内容 (列表长度: {len(para)}):")
            for j, item in enumerate(para[:3]):  # 显示每层的前3项
                if isinstance(item, str):
                    print(f"        - {item[:80]}...")
                else:
                    print(f"        - [复杂结构] {type(item).__name__}")

    if len(result.body) > 10:
        print(f"\n  ... 还有 {len(result.body) - 10} 段内容 ...")

    # 提取表格
    print("\n【表格内容】")
    # docx2python 将表格作为嵌套列表存储在 body 中
    tables = [item for item in result.body if isinstance(item, list) and len(item) > 0 and isinstance(item[0], list)]
    print(f"表格数量: {len(tables)}")
    for i, table in enumerate(tables[:3]):  # 显示前3个表
        print(f"\n  表格 {i+1}:")
        for row in table[:5]:  # 每表显示前5行
            print(f"    {row}")

    # 提取页眉页脚
    print("\n【页眉页脚】")
    # docx2python 的 header 和 footer 属性可能不存在或为 None
    header_content = getattr(result, 'header', None) or []
    footer_content = getattr(result, 'footer', None) or []
    print(f"页眉段落数: {len(header_content) if header_content else 0}")
    print(f"页脚段落数: {len(footer_content) if footer_content else 0}")

    return result


def extract_with_python_docx(docx_path):
    """使用 python-docx 提取文档结构进行对比"""
    print("\n" + "=" * 60)
    print("使用 python-docx 提取文档（对比）")
    print("=" * 60)

    doc = Document(docx_path)

    print("\n【段落结构】")
    print(f"总段落数: {len(doc.paragraphs)}")

    # 显示段落样式信息（层级结构的关键）
    print("\n前10个段落样式信息:")
    for i, para in enumerate(doc.paragraphs[:10]):
        style_name = para.style.name if para.style else "None"
        # 尝试获取大纲级别
        outline_level = None
        if para._p is not None:
            pPr = para._p.get_or_add_pPr()
            if pPr is not None:
                outlineLvl = pPr.find(qn('w:outlineLvl'))
                if outlineLvl is not None:
                    outline_level = outlineLvl.get('w:val')

        # 获取段落缩进和对齐方式
        alignment = para.alignment
        left_indent = para.paragraph_format.left_indent
        first_line_indent = para.paragraph_format.first_line_indent

        print(f"\n  [{i}] 样式: {style_name}")
        if outline_level:
            print(f"      大纲级别: {outline_level}")
        print(f"      对齐: {alignment}, 左缩进: {left_indent}, 首行缩进: {first_line_indent}")
        print(f"      内容: {para.text[:60]}...")

    return doc


def compare_extraction_methods(docx_path):
    """对比两种提取方式的结果"""
    print("\n" + "=" * 60)
    print("【对比总结】")
    print("=" * 60)

    print("""
docx2python 特点：
- 自动提取文档层级结构（标题层级、列表层级）
- 返回嵌套列表结构，保留文档大纲
- 自动提取页眉页脚、表格、图片占位符
- 保留文档属性（作者、标题等）
- 输出为 Python 原生数据结构

python-docx 特点：
- 扁平段落列表，需要手动解析层级
- 可以访问段落的样式名称（Heading 1, Heading 2等）
- 需要手动读取 outlineLvl XML 属性获取大纲级别
- 提供更多底层格式控制

使用建议：
- 快速提取结构化内容 → 使用 docx2python
- 需要精确控制格式/样式 → 使用 python-docx
- 本项目场景：docx2python 更适合提取层级结构用于 AI 分析
""")


def main():
    """主测试函数"""
    # 获取测试文档路径
    test_dir = Path(__file__).parent
    docx_path = test_dir / "测试引擎.docx"

    if not docx_path.exists():
        print(f"错误: 测试文档不存在: {docx_path}")
        # 尝试其他路径
        alt_path = test_dir / "测试文档.docx"
        if alt_path.exists():
            docx_path = alt_path
            print(f"使用替代文档: {docx_path}")
        else:
            return 1

    print("=" * 60)
    print(f"开始测试文档提取: {docx_path.name}")
    print("=" * 60)

    # 方法1: 使用 docx2python
    try:
        result = extract_with_docx2python(docx_path)
    except Exception as e:
        print(f"docx2python 提取失败: {e}")
        import traceback
        traceback.print_exc()

    # 方法2: 使用 python-docx (对比)
    try:
        doc = extract_with_python_docx(docx_path)
    except Exception as e:
        print(f"python-docx 提取失败: {e}")
        import traceback
        traceback.print_exc()

    # 对比总结
    compare_extraction_methods(docx_path)

    return 0


if __name__ == '__main__':
    sys.exit(main())
