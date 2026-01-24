import unittest
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from preparation.delude_engine import correct_para_type
from preparation.extract_para_info import extract_para_format_info
from preparation.para_type import ParagraphManager, ParsedParaType
from agents.format_agent import FormatAgent


class TestDeludeEngine(unittest.TestCase):
    """测试 DeludeEngine 段落类型识别"""

    def setUp(self):
        """加载测试数据"""
        # 加载 ground_truth
        gt_path = os.path.join(os.path.dirname(__file__), 'ground_truth.json')
        with open(gt_path, 'r', encoding='utf-8') as f:
            self.ground_truth = json.load(f)

        # 测试文档路径
        self.test_doc_path = os.path.join(os.path.dirname(__file__), '测试引擎.docx')

        # 检查测试文档是否存在
        if not os.path.exists(self.test_doc_path):
            self.skipTest(f"测试文档不存在: {self.test_doc_path}")

        # 创建 FormatAgent
        self.format_agent = FormatAgent()

    def test_abstract_content_recognition(self):
        """测试 abstract_content 类型识别"""
        # 提取段落
        manager = ParagraphManager()
        manager = extract_para_format_info(self.test_doc_path, manager)

        # 使用 delude_engine 修正
        corrected_manager = correct_para_type(self.test_doc_path, self.format_agent, manager)

        # 查找 abstract_content_zh 段落
        abstract_content_paras = [
            p for p in corrected_manager.paragraphs
            if p.type == ParsedParaType.ABSTRACT_CONTENT_ZH
        ]

        self.assertGreater(len(abstract_content_paras), 0,
                        "未识别到 abstract_content_zh 段落")

    def test_keywords_content_recognition(self):
        """测试 keywords_content 类型识别"""
        manager = ParagraphManager()
        manager = extract_para_format_info(self.test_doc_path, manager)

        corrected_manager = correct_para_type(self.test_doc_path, self.format_agent, manager)

        keywords_content_paras = [
            p for p in corrected_manager.paragraphs
            if p.type == ParsedParaType.KEYWORDS_CONTENT_ZH
        ]

        self.assertGreater(len(keywords_content_paras), 0,
                        "未识别到 keywords_content_zh 段落")

    def test_overall_accuracy(self):
        """测试整体识别准确率（与 ground_truth 对比）"""
        manager = ParagraphManager()
        manager = extract_para_format_info(self.test_doc_path, manager)

        corrected_manager = correct_para_type(self.test_doc_path, self.format_agent, manager)

        correct = 0
        total = 0

        for gt_para in self.ground_truth['paragraphs']:
            gt_type_str = gt_para['type']
            gt_content = gt_para['content']

            # 找到对应的实际段落
            actual_para = None
            for p in corrected_manager.paragraphs:
                if p.content == gt_content:
                    actual_para = p
                    break

            if actual_para:
                # 映射 ground_truth 类型到 ParsedParaType
                expected_type = self._map_ground_truth_type(gt_type_str)

                if actual_para.type == expected_type:
                    correct += 1
                total += 1
            else:
                print(f"警告：未找到匹配段落: {gt_content[:30]}...")

        if total > 0:
            accuracy = correct / total * 100
            print(f"段落类型识别准确率: {accuracy:.2f}% ({correct}/{total})")
            self.assertGreater(accuracy, 85, "整体准确率应超过 85%")

    def _map_ground_truth_type(self, gt_type):
        """映射 ground_truth 类型到 ParsedParaType"""
        mapping = {
            'title_zh': ParsedParaType.TITLE_ZH,
            'title_en': ParsedParaType.TITLE_EN,
            'abstract_zh': ParsedParaType.ABSTRACT_ZH,
            'abstract_content_zh': ParsedParaType.ABSTRACT_CONTENT_ZH,
            'abstract_en': ParsedParaType.ABSTRACT_EN,
            'abstract_content_en': ParsedParaType.ABSTRACT_CONTENT_EN,
            'keywords_zh': ParsedParaType.KEYWORDS_ZH,
            'keywords_content_zh': ParsedParaType.KEYWORDS_CONTENT_ZH,
            'keywords_en': ParsedParaType.KEYWORDS_EN,
            'keywords_content_en': ParsedParaType.KEYWORDS_CONTENT_EN,
            'heading1': ParsedParaType.HEADING1,
            'heading2': ParsedParaType.HEADING2,
            'heading3': ParsedParaType.HEADING3,
            'body': ParsedParaType.BODY,
            'references': ParsedParaType.REFERENCES,
            'references_content': ParsedParaType.REFERENCES_CONTENT
        }
        return mapping.get(gt_type, ParsedParaType.BODY)


if __name__ == '__main__':
    unittest.main()
