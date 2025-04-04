import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# 添加父级目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入被测试的模块
import format_checker

class TestFormatCheckerSimple(unittest.TestCase):
    """简化版format_checker模块测试"""
    
    def test_extract_number(self):
        """测试extract_number函数"""
        self.assertEqual(format_checker.extract_number("2.5cm"), 2.5)
        self.assertEqual(format_checker.extract_number("2.5"), 2.5)
        self.assertEqual(format_checker.extract_number(2.5), 2.5)
        self.assertEqual(format_checker.extract_number("-2.5"), -2.5)
        self.assertIsNone(format_checker.extract_number("no-number"))
    
    def test_check_journal_format(self):
        """测试_check_journal_format函数"""
        # 测试正确的期刊论文格式
        valid_journal = "[1] 作者. 论文题目[J]. 期刊名称, 2020, 40(1): 100-110."
        self.assertTrue(format_checker._check_journal_format(valid_journal, "GB/T 7714"))
        
        # 测试错误的期刊论文格式
        invalid_journal = "[1] 作者. 论文题目[J] 期刊名称, 2020, 40(1): 100-110."  # 缺少句点
        self.assertFalse(format_checker._check_journal_format(invalid_journal, "GB/T 7714"))
    
    def test_check_book_format(self):
        """测试_check_book_format函数"""
        # 测试正确的专著格式
        valid_book = "[1] 作者. 书名[M]. 北京: 出版社, 2019."
        self.assertTrue(format_checker._check_book_format(valid_book, "GB/T 7714"))
        
        # 测试错误的专著格式
        invalid_book = "[1] 作者. 书名[M] 北京: 出版社, 2019."  # 缺少句点
        self.assertFalse(format_checker._check_book_format(invalid_book, "GB/T 7714"))
    
    def test_check_thesis_format(self):
        """测试_check_thesis_format函数"""
        # 测试正确的学位论文格式
        valid_thesis = "[1] 作者. 学位论文题目[D]. 北京: 北京大学, 2018."
        self.assertTrue(format_checker._check_thesis_format(valid_thesis, "GB/T 7714"))
        
        # 测试错误的学位论文格式
        invalid_thesis = "[1] 作者. 学位论文题目[D] 北京: 北京大学, 2018."  # 缺少句点
        self.assertFalse(format_checker._check_thesis_format(invalid_thesis, "GB/T 7714"))
    
    def test_check_conference_format(self):
        """测试_check_conference_format函数"""
        # 测试正确的会议论文格式
        valid_conference = "[1] 作者. 会议论文题目[C]. 会议名称, 北京, 2017. 北京: 出版社, 2017: 200-210."
        self.assertTrue(format_checker._check_conference_format(valid_conference, "GB/T 7714"))
        
        # 测试错误的会议论文格式
        invalid_conference = "[1] 作者. 会议论文题目[C] 会议名称, 北京, 2017."  # 缺少句点
        self.assertFalse(format_checker._check_conference_format(invalid_conference, "GB/T 7714"))
    
    def test_check_electronic_format(self):
        """测试_check_electronic_format函数"""
        # 测试正确的电子资源格式
        valid_electronic = "[1] 作者. 网页标题[EB/OL]. 2016[2020-01-01]. https://example.com."
        self.assertTrue(format_checker._check_electronic_format(valid_electronic, "GB/T 7714"))
        
        # 测试错误的电子资源格式
        invalid_electronic = "[1] 作者. 网页标题[EB/OL] 2016[2020-01-01]. https://example.com."  # 缺少句点
        self.assertFalse(format_checker._check_electronic_format(invalid_electronic, "GB/T 7714"))
    
    def test_figure_number_format(self):
        """测试_check_figure_number_format函数"""
        # 测试正确的图片编号格式
        valid_caption = "图2-3 这是一个图片"
        errors = format_checker._check_figure_number_format(valid_caption)
        self.assertEqual(len(errors), 0)
        
        # 测试错误的图片编号格式
        invalid_caption = "图片2-3 这是一个图片"  # 不符合"图x-y"格式
        errors = format_checker._check_figure_number_format(invalid_caption)
        self.assertGreater(len(errors), 0)

if __name__ == '__main__':
    unittest.main()
