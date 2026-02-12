"""
简洁版 docx2python 测试 - 提取文档层级结构
用于对比和替换原有的 XML 解析方式
"""
import sys
from pathlib import Path
from docx2python import docx2python


def extract_hierarchy_with_docx2python(docx_path):
    """
    使用 docx2python 提取文档层级结构
    返回：层级化的段落结构
    """
    print("=" * 70)
    print("使用 docx2python 提取文档层级结构")
    print("=" * 70)

    result = docx2python(str(docx_path))

    print(f"\n【文档基本信息】")
    print(f"  总段落数: {len(result.body)}")
    print(f"  页眉段落: {len(result.header) if result.header else 0}")
    print(f"  页脚段落: {len(result.footer) if result.footer else 0}")

    print(f"\n【层级结构提取】")
    hierarchy = []

    def process_node(node, level=0, parent_index=0):
        """递归处理节点，提取层级结构"""
        indent = "  " * level

        if isinstance(node, str):
            # 纯文本段落
            text = node.strip()
            if text:
                print(f"{indent}[L{level}] [TEXT] {text[:80]}...")
                hierarchy.append({
                    "level": level,
                    "type": "paragraph",
                    "text": text
                })

        elif isinstance(node, list):
            # 嵌套列表 = 层级结构
            for i, item in enumerate(node):
                if isinstance(item, list):
                    # 子列表 = 进入下一层级
                    print(f"{indent}[L{level}] [DIR] 进入子层级 ({len(item)} 项)")
                    for sub_item in item:
                        process_node(sub_item, level + 1, i)
                elif isinstance(item, str):
                    # 字符串 = 当前层级段落
                    text = item.strip()
                    if text:
                        print(f"{indent}[L{level}] [TEXT] {text[:80]}...")
                        hierarchy.append({
                            "level": level,
                            "type": "paragraph",
                            "text": text
                        })

    # 处理文档体
    print(f"\n遍历文档结构...\n")
    for node in result.body:
        process_node(node, level=0)

    return hierarchy


def compare_with_extract_para_info(docx_path):
    """
    对比现有的 extract_para_info 提取方式
    """
    print("\n" + "=" * 70)
    print("与现有 extract_para_info 方式对比")
    print("=" * 70)

    print("""
【现有方式 (extract_para_info.py)】
1. 使用 python-docx 逐段解析
2. 手动提取每段的字体、段落格式
3. 通过样式名称猜测段落类型
4. 难以获取层级关系（Heading 1, 2, 3 的嵌套关系）
5. 需要大量代码处理 XML 和样式映射

【docx2python 方式】
1. 直接获取层级化的嵌套列表结构
2. 层级关系通过列表嵌套自动体现
3. 自动提取页眉页脚、表格
4. 不需要手动解析 XML
5. 代码更简洁，结构更清晰

【建议替换方案】
1. 使用 docx2python 提取文档层级结构
2. 保留现有 extract_para_info 提取具体格式信息（字体、间距等）
3. 结合两者：层级结构 + 详细格式 = 完整的段落信息
""")


def main():
    """主函数"""
    test_dir = Path(__file__).parent
    docx_path = test_dir / "测试引擎.docx"

    if not docx_path.exists():
        print(f"错误: 测试文档不存在: {docx_path}")
        return 1

    print("=" * 70)
    print(f"测试 docx2python 文档提取功能")
    print(f"文档: {docx_path.name}")
    print("=" * 70)

    # 使用 docx2python 提取层级结构
    hierarchy = extract_hierarchy_with_docx2python(docx_path)

    print(f"\n\n提取完成！共 {len(hierarchy)} 个段落/层级节点")

    # 对比现有方式
    compare_with_extract_para_info(docx_path)

    return 0


if __name__ == '__main__':
    sys.exit(main())
