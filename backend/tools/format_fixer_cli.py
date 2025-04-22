import os
import sys
import argparse
import glob

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from editors.format_fixer import FormatFixer, batch_fix_errors, apply_format_requirements
from preparation.para_type import ParagraphManager
from preparation.extract_para_info import extract_para_format_info
from utils.config_utils import load_config
from checkers.checker import check_format
from agents.format_agent import FormatAgent

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='文档格式修复工具')
    
    # 添加子命令
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # 修复错误子命令
    fix_parser = subparsers.add_parser('fix', help='修复格式错误')
    fix_parser.add_argument('doc_path', help='文档路径，支持通配符')
    fix_parser.add_argument('config_path', help='配置文件路径')
    fix_parser.add_argument('--output-dir', help='输出目录，默认为当前目录')
    
    # 应用格式子命令
    apply_parser = subparsers.add_parser('apply', help='应用格式要求')
    apply_parser.add_argument('doc_path', help='文档路径，支持通配符')
    apply_parser.add_argument('config_path', help='配置文件路径')
    apply_parser.add_argument('--output-dir', help='输出目录，默认为当前目录')
    
    return parser.parse_args()

def fix_document_errors(doc_path, config_path, output_dir=None):
    """
    修复文档格式错误
    
    Args:
        doc_path: 文档路径
        config_path: 配置文件路径
        output_dir: 输出目录
    
    Returns:
        str: 修复后的文档路径
    """
    # 初始化格式代理
    format_agent = FormatAgent()
    
    # 检查格式错误
    print(f"正在检查文档: {doc_path}")
    errors, para_manager = check_format(doc_path, config_path, format_agent)
    
    # 打印错误信息
    print(f"发现 {len(errors)} 个格式错误")
    
    # 修复错误
    if errors:
        # 确定输出路径
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"fixed_{os.path.basename(doc_path)}")
        else:
            output_path = f"fixed_{os.path.basename(doc_path)}"
        
        fixed_doc_path = batch_fix_errors(doc_path, errors, para_manager, output_path)
        print(f"已修复错误，保存到: {fixed_doc_path}")
        return fixed_doc_path
    else:
        print("未发现格式错误，无需修复")
        return doc_path

def apply_format_to_document(doc_path, config_path, output_dir=None):
    """
    应用格式要求到文档
    
    Args:
        doc_path: 文档路径
        config_path: 配置文件路径
        output_dir: 输出目录
    
    Returns:
        str: 格式化后的文档路径
    """
    # 加载配置
    requirements = load_config(config_path)
    
    # 初始化段落管理器
    para_manager = ParagraphManager()
    
    # 提取段落格式信息
    print(f"正在处理文档: {doc_path}")
    para_manager = extract_para_format_info(doc_path, para_manager)
    
    # 确定输出路径
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"formatted_{os.path.basename(doc_path)}")
    else:
        output_path = f"formatted_{os.path.basename(doc_path)}"
    
    # 应用格式要求
    formatted_doc_path = apply_format_requirements(doc_path, requirements, para_manager, output_path)
    
    print(f"已应用格式要求，保存到: {formatted_doc_path}")
    return formatted_doc_path

def main():
    """主函数"""
    args = parse_args()
    
    # 获取匹配的文档路径
    doc_paths = glob.glob(args.doc_path)
    
    if not doc_paths:
        print(f"未找到匹配的文档: {args.doc_path}")
        return
    
    # 处理每个文档
    for doc_path in doc_paths:
        if args.command == 'fix':
            fix_document_errors(doc_path, args.config_path, args.output_dir)
        elif args.command == 'apply':
            apply_format_to_document(doc_path, args.config_path, args.output_dir)

if __name__ == "__main__":
    main()
