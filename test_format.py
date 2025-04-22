import os
import sys
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.preparation.para_type import ParagraphManager
from backend.preparation.extract_para_info import extract_para_format_info
from backend.editors.format_editor import generate_formatted_doc

def main():
    # 测试文件路径
    doc_path = 'backend/tests/测试图片和表格.docx'
    config_path = 'config.json'
    output_path = 'output_test.docx'
    
    # 创建配置文件（如果不存在）
    if not os.path.exists(config_path):
        config = {
            "paper": {
                "width": 21.0,
                "height": 29.7,
                "left_margin": 2.5,
                "right_margin": 2.5,
                "top_margin": 2.5,
                "bottom_margin": 2.5
            },
            "body": {
                "paragraph_format": {
                    "alignment": "justify",
                    "first_line_indent": "2characters"
                },
                "fonts": {
                    "zh_family": ["宋体"],
                    "en_family": ["Times New Roman"],
                    "size": [10.5],
                    "color": ["black"],
                    "bold": [False],
                    "italic": [False]
                }
            },
            "figures": {
                "paragraph_format": {
                    "alignment": "center",
                    "first_line_indent": "0cm"
                },
                "caption": {
                    "position": "below",
                    "fonts": {
                        "zh_family": ["宋体"],
                        "en_family": ["Times New Roman"],
                        "size": [10.5],
                        "color": ["black"],
                        "bold": [False],
                        "italic": [False]
                    }
                }
            },
            "tables": {
                "paragraph_format": {
                    "alignment": "center",
                    "first_line_indent": "0cm"
                },
                "caption": {
                    "position": "above",
                    "fonts": {
                        "zh_family": ["宋体"],
                        "en_family": ["Times New Roman"],
                        "size": [10.5],
                        "color": ["black"],
                        "bold": [False],
                        "italic": [False]
                    },
                    "border": {
                        "style": "solid"
                    }
                }
            }
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    
    # 创建段落管理器
    manager = ParagraphManager()
    
    # 提取段落信息
    manager = extract_para_format_info(doc_path, manager)
    
    # 打印段落信息
    print(f"段落数量: {len(manager.paragraphs)}")
    
    # 检查是否有图片和表格
    figures_count = 0
    tables_count = 0
    for para in manager.paragraphs:
        if para.type == 'figures':
            figures_count += 1
        elif para.type == 'tables':
            tables_count += 1
    
    print(f"图片数量: {figures_count}")
    print(f"表格数量: {tables_count}")
    
    # 生成格式化文档
    output_path = generate_formatted_doc(config_path, manager, output_path, None, doc_path)
    
    print(f"格式化文档已生成: {output_path}")
    print(f"请打开文档检查图片和表格是否正确显示")

if __name__ == "__main__":
    main()
