from typing import List, Dict, Tuple, Any, Optional
import os
import json
import re
from datetime import datetime
from preparation.para_type import ParagraphManager, ParaInfo
from preparation.extractors import get_extractor_for_file
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


def _as_iterable(value: Any) -> List[Any]:
    """把元数据里的集合 / 单值统一成列表，便于逐项比对。"""
    if value is None:
        return []
    if isinstance(value, (set, frozenset, list, tuple)):
        return list(value)
    return [value]


def _to_cm(value: Any) -> Optional[float]:
    """把 ``'0.74cm'`` / ``0.74`` / ``'21pt'`` 统一换算为厘米。"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().lower()
    if not text:
        return None
    if "cm" in text or "厘米" in text:
        factor = 1.0
    elif "pt" in text or "磅" in text:
        factor = 2.54 / 72.0
    elif "字符" in text or "char" in text:
        # 与 editors/format_fixer.py 的换算保持一致
        factor = 0.5
    else:
        factor = 1.0
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    return float(match.group(0)) * factor


def _normalize_line_spacing(value: Any) -> str:
    """规范化行距文本，使 ``1.5`` 与 ``1.50`` 等价、固定值与倍数不混淆。"""
    text = str(value or "").strip()
    if not text:
        return ""
    low = text.lower()
    match = re.search(r"\d+(?:\.\d+)?", text)
    if not match:
        return low
    number = f"{float(match.group(0)):g}"
    if "fixed" in low or "固定值" in text:
        return f"fixed:{number}"
    return number


def _normalize_color(value: Any) -> str:
    """把颜色统一成 ``#RRGGBB`` 小写形式；``black`` 视为 ``#000000``。"""
    text = str(value or "").strip().lower()
    if not text:
        return ""
    if text in ("black", "auto", "none"):
        return "#000000"
    if text.startswith("#"):
        return text
    if len(text) == 6 and re.fullmatch(r"[0-9a-f]{6}", text):
        return "#" + text
    return text


class FormatChecker:
    def analyze_format_issues(self, doc_path: str, config_path: str, format_agent=None, preferred_extractor: Optional[str] = None) -> Tuple[List[Dict], ParagraphManager]:
        """
        分析文档格式问题

        Args:
            doc_path: 文档路径
            config_path: 配置文件路径
            format_agent: 格式代理实例（可选，用于LLM辅助分析）
            preferred_extractor: 优先使用的提取器名称

        Returns:
            Tuple[List[Dict], ParagraphManager]: 错误列表和段落管理器
        """
        errors = []
        try:
            # 1. 加载配置
            config = load_config(config_path)

            # 2. 检查页面格式
            print(f"正在检查页面格式: {doc_path}")
            doc_info = self._extract_section_info_with_extractor(doc_path, preferred_extractor)
            errors.extend(check_paper_format(doc_info, config))

            # 3. 提取文档段落信息
            print(f"正在提取段落信息: {doc_path}")
            para_manager = ParagraphManager()
            para_manager = self._extract_para_info_with_extractor(doc_path, para_manager, preferred_extractor)

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

    # 对齐方式：配置值 → 中文展示名（ALIGNMENT_MAP 同时接受中英文键）
    _ALIGNMENT_ZH = {
        "left": "左对齐",
        "center": "居中",
        "right": "右对齐",
        "justify": "两端对齐",
    }

    # 段落格式检查项：(元数据键, 配置键, 错误类型)
    _INDENT_FIELDS = (
        ("first_line", "first_line", "首行缩进"),
        ("left", "left", "左缩进"),
        ("right", "right", "右缩进"),
        ("space_before", "space_before", "段前距"),
        ("space_after", "space_after", "段后距"),
    )

    # 字体检查项：(元数据键, 配置键, 错误类型, 展示名)
    _FONT_FIELDS = (
        ("zh_family", "zh_family", "中文字体", "中文字体"),
        ("en_family", "en_family", "英文字体", "英文字体"),
    )

    def check_paragraph(self, para: ParaInfo, expected_format: Dict, index: int) -> List[Dict]:
        """检查单个段落的格式。

        比对字体（中英文、字号、加粗、斜体、颜色）与段落格式
        （对齐、行距、缩进、段前段后距），实际值来自提取阶段的样式继承解析。
        """
        meta = para.meta or {}
        actual_format = meta.get("paragraph_format") or {}
        actual_fonts = meta.get("fonts") or {}
        label = f"段落类型 '{para.type.value}'"
        location = f"{para.content[:10]}... (段落 {index+1})"

        errors: List[Dict] = []
        errors.extend(
            self._check_paragraph_format(
                expected_format.get("paragraph_format") or {},
                actual_format,
                label,
                location,
            )
        )
        errors.extend(
            self._check_fonts(
                expected_format.get("fonts") or {},
                actual_fonts,
                label,
                location,
            )
        )
        return errors

    def _check_paragraph_format(
        self,
        exp_para: Dict,
        actual_format: Dict,
        label: str,
        location: str,
    ) -> List[Dict]:
        """检查段落的对齐、行距、缩进与段间距。"""
        errors: List[Dict] = []

        # 对齐方式
        if "alignment" in exp_para:
            exp_align = str(exp_para["alignment"]).strip().lower()
            actual_align = str(actual_format.get("alignment") or "").strip().lower()
            exp_code = ALIGNMENT_MAP.get(exp_align)
            actual_code = ALIGNMENT_MAP.get(actual_align)
            if exp_code is not None and actual_code is not None:
                matched = exp_code == actual_code
            else:
                matched = actual_align == exp_align
            if not matched:
                errors.append({
                    "type": "对齐方式",
                    "message": (
                        f"{label} 对齐方式不匹配。"
                        f"期望: {self._ALIGNMENT_ZH.get(exp_align, exp_align)}, "
                        f"实际: {self._ALIGNMENT_ZH.get(actual_align, actual_align)}"
                    ),
                    "location": location,
                })

        # 行间距
        if "line_spacing" in exp_para:
            exp_ls = str(exp_para["line_spacing"]).strip()
            actual_ls = str(actual_format.get("line_spacing") or "").strip()
            if (
                exp_ls
                and actual_ls
                and _normalize_line_spacing(exp_ls) != _normalize_line_spacing(actual_ls)
            ):
                errors.append({
                    "type": "行间距",
                    "message": f"{label} 行间距不匹配。期望: {exp_ls}, 实际: {actual_ls}",
                    "location": location,
                })

        # 缩进与段前段后距
        exp_indent = exp_para.get("indentation") or {}
        actual_indent = actual_format.get("indentation") or {}
        for meta_key, exp_key, err_type in self._INDENT_FIELDS:
            if exp_key not in exp_indent:
                continue
            exp_cm = _to_cm(exp_indent[exp_key])
            actual_cm = _to_cm(actual_indent.get(meta_key))
            if exp_cm is None or actual_cm is None:
                continue
            if abs(actual_cm - exp_cm) > 0.05:
                errors.append({
                    "type": err_type,
                    "message": (
                        f"{label} {err_type}不匹配。"
                        f"期望: {exp_cm:g}cm, 实际: {actual_cm:g}cm"
                    ),
                    "location": location,
                })

        return errors

    def _check_fonts(
        self,
        exp_fonts: Dict,
        actual_fonts: Dict,
        label: str,
        location: str,
    ) -> List[Dict]:
        """检查字号、中英文字体、加粗、斜体与颜色。"""
        errors: List[Dict] = []

        # 字号
        if "size" in exp_fonts:
            exp_size = str(exp_fonts["size"])
            sizes = {
                str(s)
                for s in _as_iterable(actual_fonts.get("size"))
                if str(s) not in ("Unknown", "")
            }
            if sizes and not any(self._compare_font_size(s, exp_size) for s in sizes):
                errors.append({
                    "type": "字号",
                    "message": (
                        f"{label} 字号不匹配。"
                        f"期望: {exp_size}, 实际: {', '.join(sorted(sizes))}"
                    ),
                    "location": location,
                })

        # 中文字体 / 英文字体
        for meta_key, exp_key, err_type, human in self._FONT_FIELDS:
            if exp_key not in exp_fonts:
                continue
            exp_family = str(exp_fonts[exp_key])
            families = {
                str(f)
                for f in _as_iterable(actual_fonts.get(meta_key))
                if str(f) not in ("Unknown", "")
            }
            if families and exp_family not in families:
                errors.append({
                    "type": err_type,
                    "message": (
                        f"{label} {human}不匹配。"
                        f"期望: {exp_family}, 实际: {', '.join(sorted(families))}"
                    ),
                    "location": location,
                })

        # 加粗 / 斜体
        for exp_key, err_type in (("bold", "加粗"), ("italic", "斜体")):
            if exp_key not in exp_fonts:
                continue
            exp_flag = bool(exp_fonts[exp_key])
            flags = {
                bool(v) for v in _as_iterable(actual_fonts.get(exp_key)) if v is not None
            }
            if flags and exp_flag not in flags:
                errors.append({
                    "type": err_type,
                    "message": (
                        f"{label} {err_type}不匹配。"
                        f"期望: {'是' if exp_flag else '否'}, "
                        f"实际: {'是' if True in flags else '否'}"
                    ),
                    "location": location,
                })

        # 颜色
        if "color" in exp_fonts:
            exp_color = _normalize_color(exp_fonts["color"])
            colors = {
                _normalize_color(c)
                for c in _as_iterable(actual_fonts.get("color"))
                if c
            }
            if colors and exp_color not in colors:
                errors.append({
                    "type": "字体颜色",
                    "message": (
                        f"{label} 字体颜色不匹配。"
                        f"期望: {exp_color}, 实际: {', '.join(sorted(colors))}"
                    ),
                    "location": location,
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

    @staticmethod
    def _extract_para_info_with_extractor(doc_path: str, manager: ParagraphManager, preferred_extractor: Optional[str] = None) -> ParagraphManager:
        """使用提取器工厂提取段落信息"""
        extractor = get_extractor_for_file(doc_path, preferred=preferred_extractor)
        if extractor:
            return extractor.extract(doc_path, manager)
        # 回退到旧方法
        return extract_para_format_info(doc_path, manager)

    @staticmethod
    def _extract_section_info_with_extractor(doc_path: str, preferred_extractor: Optional[str] = None) -> Dict[str, Any]:
        """使用提取器工厂提取节信息"""
        extractor = get_extractor_for_file(doc_path, preferred=preferred_extractor)
        if extractor:
            return extractor.extract_section_info(doc_path)
        # 回退到旧方法
        return extract_section_info(doc_path)
