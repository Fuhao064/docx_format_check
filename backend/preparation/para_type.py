from typing import List, Dict, Optional
from enum import Enum
from dataclasses import dataclass
import json, re
from utils.translation_utils import translation_dict

class ParsedParaType(Enum):
    # 枚举定义保持不变，与用户提供的相同
    COVER = 'cover'
    TITLE_ZH = 'title_zh'
    TITLE_EN = 'title_en'
    ABSTRACT_ZH = 'abstract_zh'
    ABSTRACT_CONTENT_ZH = 'abstract_content_zh'
    ABSTRACT_EN = 'abstract_en'
    ABSTRACT_CONTENT_EN = 'abstract_content_en'
    KEYWORDS_ZH = 'keywords_zh'
    KEYWORDS_CONTENT_ZH = 'keywords_content_zh'
    KEYWORDS_EN = 'keywords_en'
    KEYWORDS_CONTENT_EN = 'keywords_content_en'
    HEADING1 = 'heading1'
    HEADING2 = 'heading2'
    HEADING3 = 'heading3'
    BODY = 'body'
    FIGURES = 'figures'
    TABLES = 'tables'
    REFERENCES = 'references'
    REFERENCES_CONTENT = 'references_content'
    ACKNOWLEDGMENTS = 'acknowledgments'
    ACKNOWLEDGMENTS_CONTENT = 'acknowledgments_content'
    EQUATIONS = 'equation'
    OTHERS = 'others'
    @classmethod
    def get_enum_values(cls):
        """获取枚举值及其对应的中文解释
        返回格式示例：['cover (页面设置)', 'title_zh (中文标题)']
        """
        return [f"{member.value} ({translation_dict.get(member.value, '')})" for member in cls]



@dataclass
class ParaInfo:
    """段落信息数据结构"""
    type: ParsedParaType
    content: str
    meta: Dict = None

    def __post_init__(self):
        """数据验证"""
        if not isinstance(self.type, ParsedParaType):
            raise ValueError("Invalid paragraph type")
        self.meta = self.meta or {}

class ParagraphManager:
    """段落信息管理系统"""

    def __init__(self):
        self.paragraphs: List[ParaInfo] = []
        self.position = 0  # 添加文件指针位置跟踪

    def seek(self, offset, whence=0):
        """模拟文件seek操作"""
        if whence == 0:  # 从文件开始计算
            self.position = offset
        elif whence == 1:  # 从当前位置计算
            self.position += offset
        elif whence == 2:  # 从文件末尾计算
            self.position = len(self.paragraphs) + offset
        else:
            raise ValueError("Invalid whence value")
        return self.position

    def add_para(self, para_type: ParsedParaType, content: str, meta: Dict = None) -> None:
        """
        添加段落
        :param para_type: 段落类型（必须为ParsedParaType枚举）
        :param content: 段落文本内容
        :param meta: 附加元数据（可选）
        """
        new_para = ParaInfo(para_type, content, meta)
        self.paragraphs.append(new_para)

    def remove_para(self, *,
                   para_type: Optional[ParsedParaType] = None,
                   content: Optional[str] = None,
                   meta_filter: Optional[Dict] = None) -> int:
        """
        删除符合条件的段落（支持组合条件）
        :param para_type: 按类型筛选
        :param content: 按内容全文匹配
        :param meta_filter: 按元数据包含匹配
        :return: 被删除的段落数量
        """
        removed = []

        for para in self.paragraphs:
            type_match = para_type is None or para.type == para_type
            content_match = content is None or para.content == content
            meta_match = True

            if meta_filter:
                meta_match = all(
                    para.meta.get(k) == v
                    for k, v in meta_filter.items()
                )

            if type_match and content_match and meta_match:
                removed.append(para)

        # 批量删除
        for para in removed:
            self.paragraphs.remove(para)

        return len(removed)

    def get_by_type(self, para_type: ParsedParaType) -> List[ParaInfo]:
        """按类型获取段落"""
        return [p for p in self.paragraphs if p.type == para_type]

    def find_in_content(self, keyword: str) -> List[ParaInfo]:
        """在内容中搜索关键词"""
        return [p for p in self.paragraphs if keyword in p.content]
    @staticmethod
    def convert_sets_to_lists(obj):
        """将字典/列表中的集合转换为列表"""
        if isinstance(obj, set) or isinstance(obj, list):
            return list(obj)
        elif isinstance(obj, dict):
            return {key: ParagraphManager.convert_sets_to_lists(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [ParagraphManager.convert_sets_to_lists(item) for item in obj]
        return obj
    def to_dict(self) -> List[Dict]:
        """导出为字典格式（自动处理集合转列表）"""
        return [
            self.convert_sets_to_lists({
                "id": f"para{i}",  # 自动生成带序号的ID
                "type": p.type.value,
                "content": p.content,
                "meta": p.meta
            })
            for i, p in enumerate(self.paragraphs)  # 使用enumerate自动生成序号
        ]
    # 提取必要的段落信息
    @staticmethod
    def extract_paragraph_info(paragraphs):
        result = []
        for para in paragraphs:
            # 提取基础信息
            paragraph_data = {
                "id": para.get("id"),
                "type": para.get("type"),
                "content": para.get("content")
            }

            # 提取段落设置
            paragraph_settings = para.get("meta", {}).get("段落设置", {})
            paragraph_data.update({
                "对齐方式": paragraph_settings.get("对齐方式"),
                "首行缩进": paragraph_settings.get("首行缩进")
            })

            # 提取字体信息
            font_info = para.get("meta", {}).get("字体", {})
            paragraph_data.update({
                "中文字体": ", ".join(font_info.get("中文字体", [])),
                "英文字体": ", ".join(font_info.get("英文字体", [])),
                "字号": font_info.get("字号")
            })

            result.append(paragraph_data)

        return result

    @staticmethod
    def extract_to_json_string(json_data):
        try:
            processed = ParagraphManager.extract_consistent_contents(json_data)
            return json.dumps(processed, indent=2, ensure_ascii=False)
        except ValueError as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def to_chinese_dict(self) -> List[Dict]:
        """导出为中文键字典格式"""
        english_data = self.to_dict()
        return [self._translate_keys(item) for item in english_data]
    # 由json文件转为ParagraphManager
    @staticmethod
    def build_from_json_file(json_file_path: str) -> "ParagraphManager":
        p = ParagraphManager()
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
            for para in json_data:
                # 将字符串类型转换为ParsedParaType枚举
                para_type = ParsedParaType(para["type"])
                p.add_para(
                    para_type=para_type,
                    content=para["content"],
                    meta=para.get("meta", {})
                )
        return p
    def _translate_keys(self, data: Dict) -> Dict:
        """递归转换字典键名为中文"""
        translated = {}
        for key, value in data.items():
            # 转换当前层级的键名
            new_key = translation_dict.get(key, key)

            # 递归处理嵌套结构
            if isinstance(value, dict):
                translated[new_key] = self._translate_keys(value)
            elif isinstance(value, list):
                translated[new_key] = [
                    self._translate_keys(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                translated[new_key] = value

            # 特殊处理段落类型值
            if new_key == "类型":
                translated[new_key] = translation_dict.get(value, value)

        return translated

    def to_english_dict(self, data:Dict) -> List[Dict]:
        """导出为英文键字典格式"""
        english_data = data
        reverse_dict = {v: k for k, v in translation_dict.items()}
        return [self._translate_keys_english(item, reverse_dict) for item in english_data]

    def _translate_keys_english(self, data: Dict, reverse_dict: Dict) -> Dict:
        translated = {}
        for key, value in data.items():
            new_key = reverse_dict.get(key, key)
            if isinstance(value, dict):
                translated[new_key] = self._translate_keys_english(value, reverse_dict)
            elif isinstance(value, list):
                translated[new_key] = [
                    self._translate_keys_english(item, reverse_dict) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                translated[new_key] = value
        return translated
    def __len__(self) -> int:
        return len(self.paragraphs)

    def __repr__(self) -> str:
        return f"<ParagraphManager with {len(self)} paragraphs>"

    def add_paragraph_from_dict(self, para_dict: Dict) -> None:
        """
        从字典中添加段落
        :param para_dict: 段落字典，包含 type、content 和 meta 字段
        """
        try:
            # 将字符串类型转换为ParsedParaType枚举
            para_type_str = para_dict.get("type")
            if not para_type_str:
                print(f"段落字典缺少type字段: {para_dict}")
                return

            try:
                para_type = ParsedParaType(para_type_str)
            except ValueError:
                print(f"无效的段落类型: {para_type_str}")
                para_type = ParsedParaType.OTHERS

            content = para_dict.get("content", "")
            meta = para_dict.get("meta", {})

            # 添加段落
            self.add_para(para_type, content, meta)
        except Exception as e:
            print(f"从字典添加段落时出错: {str(e)}")
