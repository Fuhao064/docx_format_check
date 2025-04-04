import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
import json
import re
import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH

# 添加父级目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入被测试的模块
import format_checker
from para_type import ParagraphManager, ParsedParaType, ParaInfo

class TestFormatCheckerEnhanced(unittest.TestCase):
    """增强版format_checker模块测试"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 模拟文档信息
        self.mock_doc_info = {
            'page_width': 21.0,
            'page_height': 29.7,
            'margin_top': 2.5,
            'margin_bottom': 2.5,
            'margin_left': 3.0,
            'margin_right': 2.0
        }
        
        # 模拟格式要求
        self.mock_format = {
            'paper_format': {
                'page_size': {
                    'width': '21cm',
                    'height': '29.7cm'
                },
                'margins': {
                    'top': '2.5cm',
                    'bottom': '2.5cm',
                    'left': '3.0cm',
                    'right': '2.0cm'
                }
            },
            'paragraph_format': {
                'title': {
                    'fonts': {
                        'zh_family': '黑体',
                        'en_family': 'Times New Roman',
                        'size': '18pt'
                    },
                    'paragraph_format': {
                        'alignment': 'center',
                        'line_spacing': '1.5'
                    }
                },
                'heading1': {
                    'fonts': {
                        'zh_family': '黑体',
                        'size': '16pt'
                    }
                },
                'body': {
                    'fonts': {
                        'zh_family': '宋体',
                        'en_family': 'Times New Roman',
                        'size': '12pt'
                    },
                    'paragraph_format': {
                        'first_line_indent': '2em'
                    }
                }
            },
            'table_format': {
                'caption': {
                    'fonts': {
                        'zh_family': '宋体',
                        'en_family': 'Times New Roman',
                        'size': '10.5pt'
                    },
                    'paragraph_format': {
                        'alignment': 'center'
                    }
                }
            },
            'figures': {
                'caption': {
                    'fonts': {
                        'zh_family': '宋体',
                        'en_family': 'Times New Roman',
                        'size': '10.5pt'
                    },
                    'paragraph_format': {
                        'alignment': 'center'
                    },
                    'position': 'below'
                }
            },
            'reference_format': {
                'citation_style': 'GB/T 7714'
            }
        }
    
    def test_check_gbt_references(self):
        """测试_check_gbt_references函数"""
        # 测试正确的参考文献格式
        valid_references = [
            "[1] 作者. 论文题目[J]. 期刊名称, 2020, 40(1): 100-110.",
            "[2] 作者. 书名[M]. 北京: 出版社, 2019.",
            "[3] 作者. 学位论文题目[D]. 北京: 北京大学, 2018.",
            "[4] 作者. 会议论文题目[C]. 会议名称, 北京, 2017. 北京: 出版社, 2017: 200-210.",
            "[5] 作者. 网页标题[EB/OL]. 2016[2020-01-01]. https://example.com."
        ]
        
        errors = format_checker._check_gbt_references(valid_references, "GB/T 7714")
        self.assertEqual(len(errors), 0, "正确格式的参考文献应该没有错误")
        
        # 测试错误的参考文献格式
        invalid_references = [
            "1 作者. 论文题目[J]. 期刊名称, 2020, 40(1): 100-110.",  # 缺少方括号
            "[2] 作者 书名[M]. 北京: 出版社, 2019.",  # 缺少句点
            "[3] 作者. 学位论文题目[X]. 北京: 北京大学, 2018.",  # 错误的文献类型标识
            "[4] 会议论文题目[C]. 会议名称, 北京, 2017.",  # 缺少作者
        ]
        
        errors = format_checker._check_gbt_references(invalid_references, "GB/T 7714")
        self.assertGreater(len(errors), 0, "错误格式的参考文献应该有错误")
        self.assertEqual(len(errors), 4, "应该有4个错误")
    
    def test_check_journal_format(self):
        """测试_check_journal_format函数"""
        # 测试正确的期刊论文格式
        valid_journal = "[1] 作者. 论文题目[J]. 期刊名称, 2020, 40(1): 100-110."
        self.assertTrue(format_checker._check_journal_format(valid_journal, "GB/T 7714"), 
                        "正确的期刊论文格式应返回True")
        
        # 测试在线期刊格式
        valid_online_journal = "[1] 作者. 论文题目[J/OL]. 期刊名称, 2020, 40(1): 100-110."
        self.assertTrue(format_checker._check_journal_format(valid_online_journal, "GB/T 7714"), 
                        "正确的在线期刊论文格式应返回True")
        
        # 测试错误的期刊论文格式
        invalid_journal = "[1] 作者. 论文题目[J] 期刊名称, 2020, 40(1): 100-110."  # 缺少句点
        self.assertFalse(format_checker._check_journal_format(invalid_journal, "GB/T 7714"), 
                         "错误的期刊论文格式应返回False")
    
    def test_check_book_format(self):
        """测试_check_book_format函数"""
        # 测试正确的专著格式
        valid_book = "[1] 作者. 书名[M]. 北京: 出版社, 2019."
        self.assertTrue(format_checker._check_book_format(valid_book, "GB/T 7714"), 
                        "正确的专著格式应返回True")
        
        # 测试带页码的专著格式
        valid_book_with_pages = "[1] 作者. 书名[M]. 北京: 出版社, 2019: 100-200."
        self.assertTrue(format_checker._check_book_format(valid_book_with_pages, "GB/T 7714"), 
                        "带页码的专著格式应返回True")
        
        # 测试错误的专著格式
        invalid_book = "[1] 作者. 书名[M] 北京: 出版社, 2019."  # 缺少句点
        self.assertFalse(format_checker._check_book_format(invalid_book, "GB/T 7714"), 
                         "错误的专著格式应返回False")
    
    def test_check_thesis_format(self):
        """测试_check_thesis_format函数"""
        # 测试正确的学位论文格式
        valid_thesis = "[1] 作者. 学位论文题目[D]. 北京: 北京大学, 2018."
        self.assertTrue(format_checker._check_thesis_format(valid_thesis, "GB/T 7714"), 
                        "正确的学位论文格式应返回True")
        
        # 测试错误的学位论文格式
        invalid_thesis = "[1] 作者. 学位论文题目[D] 北京: 北京大学, 2018."  # 缺少句点
        self.assertFalse(format_checker._check_thesis_format(invalid_thesis, "GB/T 7714"), 
                         "错误的学位论文格式应返回False")
    
    def test_check_conference_format(self):
        """测试_check_conference_format函数"""
        # 测试正确的会议论文格式
        valid_conference = "[1] 作者. 会议论文题目[C]. 会议名称, 北京, 2017. 北京: 出版社, 2017: 200-210."
        self.assertTrue(format_checker._check_conference_format(valid_conference, "GB/T 7714"), 
                        "正确的会议论文格式应返回True")
        
        # 测试在线会议论文格式
        valid_online_conference = "[1] 作者. 会议论文题目[C/OL]. 会议名称, 北京, 2017. 北京: 出版社, 2017: 200-210."
        self.assertTrue(format_checker._check_conference_format(valid_online_conference, "GB/T 7714"), 
                        "正确的在线会议论文格式应返回True")
        
        # 测试简化的会议论文格式
        valid_simple_conference = "[1] 作者. 会议论文题目[C]. 会议名称, 北京, 2017."
        self.assertTrue(format_checker._check_conference_format(valid_simple_conference, "GB/T 7714"), 
                        "简化的会议论文格式应返回True")
        
        # 测试错误的会议论文格式
        invalid_conference = "[1] 作者. 会议论文题目[C] 会议名称, 北京, 2017."  # 缺少句点
        self.assertFalse(format_checker._check_conference_format(invalid_conference, "GB/T 7714"), 
                         "错误的会议论文格式应返回False")
    
    def test_check_electronic_format(self):
        """测试_check_electronic_format函数"""
        # 测试正确的电子资源格式
        valid_electronic = "[1] 作者. 网页标题[EB/OL]. 2016[2020-01-01]. https://example.com."
        self.assertTrue(format_checker._check_electronic_format(valid_electronic, "GB/T 7714"), 
                        "正确的电子资源格式应返回True")
        
        # 测试简化的电子资源格式
        valid_simple_electronic = "[1] 作者. 网页标题[EB/OL]. https://example.com."
        self.assertTrue(format_checker._check_electronic_format(valid_simple_electronic, "GB/T 7714"), 
                        "简化的电子资源格式应返回True")
        
        # 测试错误的电子资源格式
        invalid_electronic = "[1] 作者. 网页标题[EB/OL] 2016[2020-01-01]. https://example.com."  # 缺少句点
        self.assertFalse(format_checker._check_electronic_format(invalid_electronic, "GB/T 7714"), 
                         "错误的电子资源格式应返回False")
    
    def test_check_apa_references(self):
        """测试_check_apa_references函数"""
        # 测试正确的APA格式参考文献
        valid_apa_references = [
            "Author, A. (2020). Title of the article. Journal Name, 40(1), 100-110.",
            "Author, B. (2019). Title of the book. Publisher."
        ]
        
        errors = format_checker._check_apa_references(valid_apa_references)
        self.assertEqual(len(errors), 0, "正确格式的APA参考文献应该没有错误")
        
        # 测试错误的APA格式参考文献
        invalid_apa_references = [
            "Author, A. Title of the article. Journal Name, 40(1), 100-110.",  # 缺少年份
            "2019. Title of the book. Publisher."  # 缺少作者
        ]
        
        errors = format_checker._check_apa_references(invalid_apa_references)
        self.assertGreater(len(errors), 0, "错误格式的APA参考文献应该有错误")
    
    def test_check_mla_references(self):
        """测试_check_mla_references函数"""
        # 测试正确的MLA格式参考文献
        valid_mla_references = [
            "Author, Adam. \"Title of the Article.\" Journal Name, vol. 40, no. 1, 2020, pp. 100-110.",
            "Author, Bob. Title of the Book. Publisher, 2019."
        ]
        
        errors = format_checker._check_mla_references(valid_mla_references)
        self.assertEqual(len(errors), 0, "正确格式的MLA参考文献应该没有错误")
        
        # 测试错误的MLA格式参考文献
        invalid_mla_references = [
            "\"Title of the Article.\" Journal Name, vol. 40, no. 1, 2020, pp. 100-110.",  # 缺少作者
            "Title of the Book. Publisher, 2019."  # 缺少作者
        ]
        
        errors = format_checker._check_mla_references(invalid_mla_references)
        self.assertGreater(len(errors), 0, "错误格式的MLA参考文献应该有错误")
    
    def test_check_table_content_format(self):
        """测试_check_table_content_format函数"""
        # 创建模拟表格
        mock_table = MagicMock()
        
        # 测试空表格
        mock_table.rows = []
        mock_table.columns = []
        errors = format_checker._check_table_content_format(mock_table)
        self.assertGreater(len(errors), 0, "空表格应该报错")
        self.assertIn('表格为空', errors[0]['message'], "应该提示表格为空")
        
        # 测试正常表格
        mock_row1 = MagicMock()
        mock_row2 = MagicMock()
        mock_cell1 = MagicMock(text="内容1")
        mock_cell2 = MagicMock(text="内容2")
        mock_cell3 = MagicMock(text="内容3")
        mock_cell4 = MagicMock(text="内容4")
        
        mock_row1.cells = [mock_cell1, mock_cell2]
        mock_row2.cells = [mock_cell3, mock_cell4]
        mock_table.rows = [mock_row1, mock_row2]
        mock_table.columns = [MagicMock(), MagicMock()]
        
        errors = format_checker._check_table_content_format(mock_table)
        self.assertEqual(len(errors), 0, "正常表格不应该有错误")
        
        # 测试有空单元格的表格
        mock_cell3.text = ""
        errors = format_checker._check_table_content_format(mock_table)
        self.assertGreater(len(errors), 0, "有空单元格的表格应该报错")
        self.assertIn('表格存在空单元格', errors[0]['message'], "应该提示存在空单元格")
        
        # 测试行列不一致的表格
        mock_cell3.text = "内容3"  # 恢复内容
        mock_row3 = MagicMock()
        mock_row3.cells = [mock_cell1, mock_cell2, MagicMock(text="额外内容")]  # 多一列
        mock_table.rows = [mock_row1, mock_row2, mock_row3]
        
        errors = format_checker._check_table_content_format(mock_table)
        self.assertGreater(len(errors), 0, "行列不一致的表格应该报错")
        self.assertIn('表格行列不一致', errors[0]['message'], "应该提示行列不一致")
    
    def test_check_table_number_format(self):
        """测试_check_table_number_format函数"""
        # 测试正确的表格编号格式
        valid_caption = "表2-3 这是一个表格"
        errors = format_checker._check_table_number_format(valid_caption)
        self.assertEqual(len(errors), 0, "正确的表格编号格式不应该有错误")
        
        # 测试英文表格编号格式
        valid_en_caption = "Table 2-3 This is a table"
        errors = format_checker._check_table_number_format(valid_en_caption)
        self.assertEqual(len(errors), 0, "正确的英文表格编号格式不应该有错误")
        
        # 测试错误的表格编号格式
        invalid_caption = "表格2-3 这是一个表格"  # 不符合"表x-y"格式
        errors = format_checker._check_table_number_format(invalid_caption)
        self.assertGreater(len(errors), 0, "错误的表格编号格式应该有错误")
        
        # 测试负数章节或表格序号
        invalid_number_caption = "表-2-3 这是一个表格"
        errors = format_checker._check_table_number_format(invalid_number_caption)
        self.assertGreater(len(errors), 0, "负数章节或表格序号应该有错误")
    
    def test_check_figure_number_format(self):
        """测试_check_figure_number_format函数"""
        # 测试正确的图片编号格式
        valid_caption = "图2-3 这是一个图片"
        errors = format_checker._check_figure_number_format(valid_caption)
        self.assertEqual(len(errors), 0, "正确的图片编号格式不应该有错误")
        
        # 测试英文图片编号格式
        valid_en_caption = "Figure 2-3 This is a figure"
        errors = format_checker._check_figure_number_format(valid_en_caption)
        self.assertEqual(len(errors), 0, "正确的英文图片编号格式不应该有错误")
        
        # 测试错误的图片编号格式
        invalid_caption = "图片2-3 这是一个图片"  # 不符合"图x-y"格式
        errors = format_checker._check_figure_number_format(invalid_caption)
        self.assertGreater(len(errors), 0, "错误的图片编号格式应该有错误")
        
        # 测试负数章节或图片序号
        invalid_number_caption = "图-2-3 这是一个图片"
        errors = format_checker._check_figure_number_format(invalid_number_caption)
        self.assertGreater(len(errors), 0, "负数章节或图片序号应该有错误")
    
    def test_recursive_check(self):
        """测试_recursive_check函数"""
        # 测试完全匹配的情况
        expected = {
            'fonts': {
                'zh_family': '宋体',
                'en_family': 'Times New Roman',
                'size': '12pt'
            },
            'paragraph_format': {
                'first_line_indent': '2em'
            }
        }
        
        actual = {
            'fonts': {
                'zh_family': '宋体',
                'en_family': 'Times New Roman',
                'size': '12pt'
            },
            'paragraph_format': {
                'first_line_indent': '2em'
            }
        }
        
        errors = format_checker._recursive_check(actual, expected)
        self.assertEqual(len(errors), 0, "完全匹配的情况不应该有错误")
        
        # 测试缺少字段的情况
        actual_missing = {
            'fonts': {
                'zh_family': '宋体',
                # 缺少en_family
                'size': '12pt'
            },
            'paragraph_format': {
                'first_line_indent': '2em'
            }
        }
        
        errors = format_checker._recursive_check(actual_missing, expected)
        self.assertGreater(len(errors), 0, "缺少字段的情况应该有错误")
        self.assertIn("缺少必需字段: 'en_family'", errors[0][1], "应该提示缺少en_family字段")
        
        # 测试值不匹配的情况
        actual_mismatch = {
            'fonts': {
                'zh_family': '黑体',  # 与期望的宋体不匹配
                'en_family': 'Times New Roman',
                'size': '12pt'
            },
            'paragraph_format': {
                'first_line_indent': '2em'
            }
        }
        
        errors = format_checker._recursive_check(actual_mismatch, expected)
        self.assertGreater(len(errors), 0, "值不匹配的情况应该有错误")
        self.assertIn("'zh_family' 不匹配", errors[0][1], "应该提示zh_family不匹配")
        
        # 测试字段类型不匹配的情况
        actual_type_mismatch = {
            'fonts': "这不是一个字典",  # 类型不匹配
            'paragraph_format': {
                'first_line_indent': '2em'
            }
        }
        
        errors = format_checker._recursive_check(actual_type_mismatch, expected)
        self.assertGreater(len(errors), 0, "字段类型不匹配的情况应该有错误")
        self.assertIn("字段类型不匹配", errors[0][1], "应该提示字段类型不匹配")
        
        # 测试列表类型字段的情况
        actual_list = {
            'fonts': {
                'zh_family': ['宋体'],  # 列表类型
                'en_family': ['Times New Roman'],
                'size': '12pt'
            },
            'paragraph_format': {
                'first_line_indent': '2em'
            }
        }
        
        errors = format_checker._recursive_check(actual_list, expected)
        self.assertEqual(len(errors), 0, "单值列表类型字段应该能正确处理")
        
        # 测试多值列表的情况
        actual_multi_list = {
            'fonts': {
                'zh_family': ['宋体', '黑体'],  # 多值列表
                'en_family': 'Times New Roman',
                'size': '12pt'
            },
            'paragraph_format': {
                'first_line_indent': '2em'
            }
        }
        
        errors = format_checker._recursive_check(actual_multi_list, expected)
        self.assertGreater(len(errors), 0, "多值列表类型字段应该报错")
        self.assertIn("存在多个值", errors[0][1], "应该提示存在多个值")

if __name__ == '__main__':
    unittest.main()
