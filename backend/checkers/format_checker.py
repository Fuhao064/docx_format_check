from typing import List, Dict, Tuple, Any, Optional
import os
import json
from datetime import datetime
from preparation.para_type import ParagraphManager, ParaInfo
from preparation.extract_para_info import extract_para_format_info
from preparation.docx_parser import extract_section_info
from editors.format_editor import load_config, ALIGNMENT_MAP
from preparation.delude_engine import correct_para_type
from utils.translation_utils import translate_errors

# Import checks from other modules
from .check_paper import check_paper_format
from .check_references import check_reference_format
from .check_tables_figures import check_table_format, check_figure_format
from .checker import check_abstract, check_keywords, check_required_paragraphs

class FormatChecker:
    def analyze_format_issues(self, doc_path: str, config_path: str, format_agent=None) -> Tuple[List[Dict], ParagraphManager]:
        """
        分析文档格式问题

        Args:
            doc_path: 文档路径
            config_path: 配置文件路径
            format_agent: 格式代理实例（可选，用于LLM辅助分析）

        Returns:
            Tuple[List[Dict], ParagraphManager]: 错误列表和段落管理器
        """
        errors = []
        try:
            # 1. 加载配置
            config = load_config(config_path)

            # 2. 检查页面格式
            print(f"正在检查页面格式: {doc_path}")
            doc_info = extract_section_info(doc_path)
            errors.extend(check_paper_format(doc_info, config))

            # 3. 提取文档段落信息
            print(f"正在提取段落信息: {doc_path}")
            para_manager = ParagraphManager()
            para_manager = extract_para_format_info(doc_path, para_manager)

            # 4. 如果提供了format_agent，进行智能段落类型重分配
            if format_agent:
                print("正在使用AI进行段落类型重分析...")
                para_manager = correct_para_type(doc_path, format_agent, para_manager)
                
                # 保存中间结果 (保留原有逻辑)
                self._save_cache(doc_path, para_manager)

            # 5. 执行各种结构检查
            print("正在执行结构检查...")
            errors.extend(check_abstract(para_manager))
            errors.extend(check_keywords(para_manager))
            errors.extend(check_required_paragraphs(para_manager, config))
            errors.extend(check_reference_format(doc_path, config))
            errors.extend(check_table_format(doc_path, config))
            errors.extend(check_figure_format(doc_path, config, para_manager))

            # 6. 检查段落样式 (使用本类的check_paragraph_manager)
            print("正在检查段落样式...")
            style_errors = self.check_paragraph_manager(para_manager, config_path)
            errors.extend(style_errors)

            # 7. 翻译错误信息
            translated_errors = translate_errors(errors)
            
            return translated_errors, para_manager

        except Exception as e:
            print(f"分析过程出错: {str(e)}")
            errors.append({
                "message": f"分析过程出错: {str(e)}",
                "location": "系统错误"
            })
            return errors, ParagraphManager()

    def _save_cache(self, doc_path: str, para_manager: ParagraphManager):
        """保存中间结果到缓存"""
        try:
            base_name = os.path.splitext(os.path.basename(doc_path))[0]
            result_filename = f"{base_name}_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            caches_folder = os.path.join(os.path.dirname(__file__), '..', '..', 'caches') # Adjust path relative to backend/checkers
            # Previous code used os.path.join(os.path.dirname(__file__), '..', 'caches') from checker.py
            # If checker.py is in backend/checkers, then '..' is backend, so backend/caches?
            # Let's check where caches folder is. Usually it is at project root or backend root.
            # Assuming backend/caches based on checker.py logic.
            # checker.py path: backend/checkers/checker.py
            # os.path.dirname(__file__) -> backend/checkers
            # .. -> backend
            # caches -> backend/caches
            
            os.makedirs(caches_folder, exist_ok=True)
            result_path = os.path.join(caches_folder, result_filename)
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(para_manager.to_dict(), f, ensure_ascii=False, indent=4)
            print(f"重分配结果已保存到: {result_path}")
        except Exception as e:
            print(f"保存缓存失败: {e}")

    def check_paragraph_manager(self, para_manager: ParagraphManager, config_path: str) -> List[Dict]:
        """
        检查段落管理器中的格式问题
        """
        config = load_config(config_path)
        errors = []

        for i, para in enumerate(para_manager.paragraphs):
            # 获取段落类型对应的配置
            para_type_value = para.type.value
            if para_type_value not in config:
                continue

            expected_format = config[para_type_value]
            para_errors = self.check_paragraph(para, expected_format, i)
            errors.extend(para_errors)

        return errors

    def check_paragraph(self, para: ParaInfo, expected_format: Dict, index: int) -> List[Dict]:
        """
        检查单个段落的格式
        """
        errors = []
        actual_format = para.meta.get('paragraph_format', {})
        actual_fonts = para.meta.get('fonts', {})
        
        # 1. 检查段落格式 (对齐、缩进、行距)
        if 'paragraph_format' in expected_format:
            exp_para = expected_format['paragraph_format']
            
            # 检查对齐方式
            if 'alignment' in exp_para:
                exp_align_str = str(exp_para['alignment']).lower()
                actual_align_str = str(actual_format.get('alignment')).lower()
                
                # 尝试将对齐方式转换为标准常量进行比较
                exp_val = ALIGNMENT_MAP.get(exp_align_str)
                actual_val = ALIGNMENT_MAP.get(actual_align_str)
                
                # 如果两者都能映射到常量，比较常量
                if exp_val is not None and actual_val is not None:
                    if exp_val != actual_val:
                        errors.append({
                            'type': '对齐方式',
                            'message': f"段落类型 '{para.type.value}' 对齐方式不匹配。期望: {exp_align_str}, 实际: {actual_align_str}",
                            'location': f"{para.content[:10]}... (段落 {index+1})"
                        })
                # 否则直接比较字符串
                elif actual_align_str != exp_align_str:
                     errors.append({
                        'type': '对齐方式',
                        'message': f"段落类型 '{para.type.value}' 对齐方式不匹配。期望: {exp_align_str}, 实际: {actual_align_str}",
                        'location': f"{para.content[:10]}... (段落 {index+1})"
                    })
            
            # 检查行间距 (TODO: 完善)

        # 2. 检查字体 (中文字体、英文字体、字号、加粗、斜体)
        if 'fonts' in expected_format:
            exp_fonts = expected_format['fonts']
            
            # 检查字号
            if 'size' in exp_fonts:
                exp_size = str(exp_fonts['size'])
                actual_sizes = actual_fonts.get('size', set())
                valid_sizes = {str(s) for s in actual_sizes if s != 'Unknown'}
                if valid_sizes:
                    is_match = False
                    for s in valid_sizes:
                        if self._compare_font_size(s, exp_size):
                            is_match = True
                            break
                    
                    if not is_match:
                        errors.append({
                            'type': '字号',
                            'message': f"段落类型 '{para.type.value}' 字号不匹配。期望: {exp_size}, 实际: {', '.join(valid_sizes)}",
                            'location': f"{para.content[:10]}... (段落 {index+1})"
                        })

            # 检查中文字体
            if 'zh_family' in exp_fonts:
                exp_zh = exp_fonts['zh_family']
                actual_zh = actual_fonts.get('zh_family', set())
                valid_zh = {f for f in actual_zh if f != 'Unknown'}
                
                if valid_zh and exp_zh not in valid_zh:
                     errors.append({
                        'type': '字体',
                        'message': f"段落类型 '{para.type.value}' 中文字体不匹配。期望: {exp_zh}, 实际: {', '.join(valid_zh)}",
                        'location': f"{para.content[:10]}... (段落 {index+1})"
                    })

        return errors

    def _compare_font_size(self, size1: Any, size2: Any) -> bool:
        """比较两个字号是否相等"""
        try:
            s1 = float(str(size1).replace('pt', ''))
            s2 = float(str(size2).replace('pt', ''))
            return abs(s1 - s2) < 0.1
        except:
            return str(size1) == str(size2)
