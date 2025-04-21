"""
测试文件：读取docx文件并将其内容导出为JSON
"""
import os
import sys
import json
import time
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入所需模块
from preparation.para_type import ParagraphManager
from preparation.extract_para_info import extract_para_format_info

def main():
    # 获取当前脚本所在目录
    current_dir = Path(__file__).parent.absolute()

    # 获取项目根目录
    root_dir = current_dir.parent.parent

    # 设置输入文件路径（假设test.docx在项目根目录）
    input_file = os.path.join(root_dir, "test.docx")

    # 检查文件是否存在
    if not os.path.exists(input_file):
        print(f"错误：文件 {input_file} 不存在")
        return

    # 设置输出文件路径
    cache_dir = os.path.join(root_dir, "backend", "caches")

    # 确保缓存目录存在
    os.makedirs(cache_dir, exist_ok=True)

    # 生成唯一的输出文件名
    timestamp = int(time.time())
    output_file = os.path.join(cache_dir, f"test_docx_content_{timestamp}.json")

    print(f"正在处理文件: {input_file}")

    try:
        # 初始化段落管理器
        manager = ParagraphManager()

        # 使用extract_para_format_info函数提取文档内容
        manager = extract_para_format_info(input_file, manager)

        # 将段落信息转换为字典格式（包含完整的meta信息）
        paragraphs_dict = manager.to_dict()

        # 将结果保存为JSON文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(paragraphs_dict, f, ensure_ascii=False, indent=4)

        print(f"处理完成，结果已保存到: {output_file}")

        # 打印段落数量和类型统计
        para_types = {}
        for para in manager.paragraphs:
            para_type = para.type.value
            if para_type in para_types:
                para_types[para_type] += 1
            else:
                para_types[para_type] = 1

        print(f"\n文档包含 {len(manager.paragraphs)} 个段落")
        print("段落类型统计:")
        for para_type, count in para_types.items():
            print(f"  - {para_type}: {count}个")

    except Exception as e:
        print(f"处理文件时出错: {str(e)}")

if __name__ == "__main__":
    main()
