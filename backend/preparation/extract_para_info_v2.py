"""
extract_para_info_v2.py - 结合 docx2python 和 python-docx 的段落信息提取模块

主要改进：
1. 使用 docx2python 提取文档层级结构（大纲级别、标题层级）
2. 继续使用 python-docx 提取详细格式信息（字体、间距、对齐等）
3. 大幅减少手动解析 XML 的代码
4. 更好地识别文档结构（标题、正文、摘要等）
"""

import docx
import xml.etree.ElementTree as ET
import json, re, os, zipfile
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path

# 导入 docx2python 用于提取层级结构
try:
    from docx2python import docx2python
    DOCX2PYTHON_AVAILABLE = True
except ImportError:
    DOCX2PYTHON_AVAILABLE = False
    print("警告: docx2python 未安装，将回退到纯 python-docx 模式")

from preparation.para_type import ParsedParaType, ParagraphManager
from docx.shared import RGBColor
from docx.oxml.ns import qn


class DocumentStructureExtractor:
    """
    文档结构提取器
    结合 docx2python 和 python-docx 提取文档结构和格式信息
    """

    def __init__(self, docx_path: str):
        self.docx_path = docx_path
        self.doc = docx.Document(docx_path)

        # 使用 docx2python 提取层级结构
        self.hierarchy = None
        self.docx2python_result = None
        if DOCX2PYTHON_AVAILABLE:
            try:
                self.docx2python_result = docx2python(docx_path)
                self.hierarchy = self._parse_docx2python_structure()
                print(f"✓ 使用 docx2python 提取到 {len(self.hierarchy)} 个结构节点")
            except Exception as e:
                print(f"警告: docx2python 提取失败: {e}")
                self.hierarchy = self._fallback_hierarchy_extraction()
        else:
            self.hierarchy = self._fallback_hierarchy_extraction()

    def _parse_docx2python_structure(self) -> List[Dict[str, Any]]:
        """
        解析 docx2python 的输出，提取层级结构
        """
        hierarchy = []

        def process_node(node, level=0, parent_type="body"):
            """递归处理节点"""
            if isinstance(node, str):
                text = node.strip()
                if text:
                    # 根据内容特征推断段落类型
                    para_type = self._infer_paragraph_type(text, level, parent_type)
                    hierarchy.append({
                        "level": level,
                        "type": para_type,
                        "content": text,
                        "is_heading": level > 0 or para_type in ["heading1", "heading2", "heading3"]
                    })

            elif isinstance(node, list):
                # 子列表表示层级嵌套
                for item in node:
                    if isinstance(item, list):
                        # 进入下一层级
                        process_node(item, level + 1, parent_type)
                    else:
                        process_node(item, level, parent_type)

        # 处理文档体
        if self.docx2python_result and self.docx2python_result.body:
            for node in self.docx2python_result.body:
                process_node(node)

        return hierarchy

    def _infer_paragraph_type(self, text: str, level: int, parent_type: str) -> str:
        """
        根据文本内容和层级推断段落类型
        """
        text = text.strip()
        text_lower = text.lower()

        # 识别标题
        if level == 1 or text.startswith("1 ") or text.startswith("一、"):
            return "heading1"
        elif level == 2 or text.startswith("1.1 ") or text.startswith("（一）"):
            return "heading2"
        elif level == 3 or text.startswith("1.1.1 ") or text.startswith("1."):
            return "heading3"

        # 识别摘要和关键词
        if "摘要" in text[:10] or "abstract" in text_lower[:20]:
            if len(text) < 50:
                return "abstract_label"
            return "abstract_content"

        if "关键词" in text[:10] or "keywords" in text_lower[:20]:
            if len(text) < 50:
                return "keywords_label"
            return "keywords_content"

        # 识别参考文献
        if text.startswith("[") and re.match(r"^\[\d+\]", text):
            return "reference"

        # 默认返回正文
        return "body"

    def _fallback_hierarchy_extraction(self) -> List[Dict[str, Any]]:
        """
        当 docx2python 不可用时，使用 python-docx 回退提取
        """
        print("使用 python-docx 回退模式提取层级")
        hierarchy = []

        for i, para in enumerate(self.doc.paragraphs):
            if not para.text.strip():
                continue

            # 尝试从样式推断层级
            level = 0
            para_type = "body"

            if para.style and para.style.name:
                style_name = para.style.name.lower()
                if "heading 1" in style_name or "标题 1" in style_name:
                    level = 1
                    para_type = "heading1"
                elif "heading 2" in style_name or "标题 2" in style_name:
                    level = 2
                    para_type = "heading2"
                elif "heading 3" in style_name or "标题 3" in style_name:
                    level = 3
                    para_type = "heading3"

            hierarchy.append({
                "level": level,
                "type": para_type,
                "content": para.text,
                "is_heading": level > 0,
                "index": i
            })

        return hierarchy

    def get_paragraph_count(self) -> int:
        """获取段落数量"""
        return len(self.doc.paragraphs)

    def get_document_info(self) -> Dict[str, Any]:
        """获取文档基本信息"""
        return {
            "paragraph_count": len(self.doc.paragraphs),
            "hierarchy_node_count": len(self.hierarchy),
            "has_docx2python": DOCX2PYTHON_AVAILABLE and self.docx2python_result is not None
        }


def extract_para_info_with_hierarchy(docx_path: str, manager: ParagraphManager) -> ParagraphManager:
    """
    结合 docx2python 和 python-docx 提取段落信息

    Args:
        docx_path: Word文档路径
        manager: 段落管理器实例

    Returns:
        更新后的段落管理器实例
    """
    print(f"\n开始提取文档信息: {docx_path}")
    print("=" * 60)

    # 创建结构提取器
    extractor = DocumentStructureExtractor(docx_path)
    doc_info = extractor.get_document_info()
    print(f"✓ 文档信息: {doc_info}")

    # 获取层级结构
    hierarchy = extractor.hierarchy
    print(f"✓ 提取到 {len(hierarchy)} 个层级节点")

    # 显示前5个节点作为示例
    print("\n前5个层级节点示例:")
    for i, node in enumerate(hierarchy[:5]):
        print(f"  [{i}] L{node['level']}: {node['type']} - {node['content'][:50]}...")

    print("\n" + "=" * 60)
    print("✓ 文档结构提取完成")
    print("下一步：结合 python-docx 提取详细格式信息...")

    # TODO: 在这里调用原有的 extract_para_info 逻辑，
    # 但使用 hierarchy 中的层级信息来辅助判断段落类型

    return manager


# 保持向后兼容的函数
def extract_para_format_info(doc_path: str, manager: ParagraphManager) -> ParagraphManager:
    """
    向后兼容的段落格式信息提取函数
    内部使用新的结合方案
    """
    return extract_para_info_with_hierarchy(doc_path, manager)


if __name__ == "__main__":
    # 测试代码
    from pathlib import Path

    test_dir = Path(__file__).parent.parent / "test"
    docx_path = test_dir / "测试引擎.docx"

    if docx_path.exists():
        manager = ParagraphManager()
        extract_para_info_with_hierarchy(str(docx_path), manager)
    else:
        print(f"测试文档不存在: {docx_path}")
