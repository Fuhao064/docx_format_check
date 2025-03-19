import docx
from docx import Document
from docx.shared import Pt, RGBColor, Cm, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.enum.section import WD_ORIENTATION, WD_SECTION
import json
import os
from typing import Dict, List, Union, Optional, Tuple
from para_type import ParsedParaType, ParagraphManager, ParaInfo
import re
from utils import parse_color

class FormatEditor:
    """
    文档格式编辑器，用于修改docx文档的格式，包括段落样式、字体样式等
    支持大模型作为工具函数调用
    """
    def __init__(self, doc_path: str, paragraph_manager: Optional[ParagraphManager] = None):
        """
        初始化格式编辑器
        
        Args:
            doc_path: 文档路径
            paragraph_manager: 段落管理器，包含已处理好的段落类型信息
        """
        self.doc_path = doc_path
        self.doc = Document(doc_path)
        self.paragraph_manager = paragraph_manager
        
        # 如果传入了paragraph_manager，创建段落类型映射
        self.para_type_map = {}
        if paragraph_manager:
            para_infos = paragraph_manager.to_dict()
            for i, para in enumerate(self.doc.paragraphs):
                para_content = para.text.strip()
                for para_info in para_infos:
                    if para_content == para_info['content'].strip():
                        self.para_type_map[i] = para_info['type']
                        break
    
    def save(self, output_path: Optional[str] = None):
        """
        保存文档
        
        Args:
            output_path: 输出路径，如果为None则覆盖原文件
        """
        if output_path is None:
            output_path = self.doc_path
        self.doc.save(output_path)
        return output_path
    
    def set_paper_format(self, paper_config: Dict):
        """
        设置文档纸张格式
        
        Args:
            paper_config: 纸张配置，包含size, orientation, margins等
        """
        for section in self.doc.sections:
            # 设置纸张大小
            if 'size' in paper_config:
                size = paper_config['size']
                if size == 'A4':
                    section.page_width = Cm(21)
                    section.page_height = Cm(29.7)
                elif size == 'A3':
                    section.page_width = Cm(29.7)
                    section.page_height = Cm(42)
                elif size == 'Letter':
                    section.page_width = Inches(8.5)
                    section.page_height = Inches(11)
            
            # 设置纸张方向
            if 'orientation' in paper_config:
                orientation = paper_config['orientation']
                if orientation.lower() == 'portrait':
                    section.orientation = WD_ORIENTATION.PORTRAIT
                elif orientation.lower() == 'landscape':
                    section.orientation = WD_ORIENTATION.LANDSCAPE
            
            # 设置页边距
            if 'margins' in paper_config:
                margins = paper_config['margins']
                if 'top' in margins:
                    section.top_margin = Cm(float(margins['top']))
                if 'bottom' in margins:
                    section.bottom_margin = Cm(float(margins['bottom']))
                if 'left' in margins:
                    section.left_margin = Cm(float(margins['left']))
                if 'right' in margins:
                    section.right_margin = Cm(float(margins['right']))
            
            # 设置页眉页脚
            if 'header' in paper_config:
                header = paper_config['header']
                if 'top' in header:
                    section.header_distance = Cm(float(header['top']))
                if 'bottom' in header:
                    section.footer_distance = Cm(float(header['bottom']))
    
    def _get_alignment_value(self, alignment_str: str) -> int:
        """
        获取对齐方式的枚举值
        
        Args:
            alignment_str: 对齐方式字符串
            
        Returns:
            对齐方式枚举值
        """
        alignment_map = {
            '左对齐': WD_ALIGN_PARAGRAPH.LEFT,
            '居中': WD_ALIGN_PARAGRAPH.CENTER,
            '右对齐': WD_ALIGN_PARAGRAPH.RIGHT,
            '两端对齐': WD_ALIGN_PARAGRAPH.JUSTIFY,
            'left': WD_ALIGN_PARAGRAPH.LEFT,
            'center': WD_ALIGN_PARAGRAPH.CENTER,
            'right': WD_ALIGN_PARAGRAPH.RIGHT,
            'justify': WD_ALIGN_PARAGRAPH.JUSTIFY
        }
        return alignment_map.get(alignment_str.lower(), WD_ALIGN_PARAGRAPH.LEFT)
    
    def _get_line_spacing_value(self, line_spacing_str: str) -> Union[float, int]:
        """
        获取行间距的值
        
        Args:
            line_spacing_str: 行间距字符串，如"1.5倍行距"、"1.5 倍行距"、"1.5"、"20磅"
            
        Returns:
            行间距值
        """
        # 提取数字
        match = re.search(r'(\d+(\.\d+)?)', line_spacing_str)
        if not match:
            return 1.0  # 默认单倍行距
        
        value = float(match.group(1))
        
        # 判断是倍行距还是固定磅值
        if '倍' in line_spacing_str:
            return value  # 倍行距
        elif '磅' in line_spacing_str:
            return int(value * 20)  # 固定磅值，python-docx中使用20倍的值
        else:
            # 默认为倍行距
            return value
    
    def _parse_color(self, color_str: str) -> Tuple[int, int, int]:
        return parse_color(color_str)
    
    def set_paragraph_format(self, paragraph, para_format: Dict):
        """
        设置段落格式
        
        Args:
            paragraph: 段落对象
            para_format: 段落格式配置
        """
        # 设置对齐方式
        if 'alignment' in para_format:
            paragraph.alignment = self._get_alignment_value(para_format['alignment'])
        
        # 设置首行缩进
        if 'first_line_indent' in para_format:
            # 将厘米转换为磅
            first_line_indent = para_format['first_line_indent']
            if isinstance(first_line_indent, str):
                first_line_indent = float(re.search(r'(\d+(\.\d+)?)', first_line_indent).group(1))
            paragraph.paragraph_format.first_line_indent = Pt(first_line_indent * 20)
        
        # 设置左缩进
        if 'left_indent' in para_format:
            left_indent = para_format['left_indent']
            if isinstance(left_indent, str):
                left_indent = float(re.search(r'(\d+(\.\d+)?)', left_indent).group(1))
            paragraph.paragraph_format.left_indent = Pt(left_indent)
        
        # 设置右缩进
        if 'right_indent' in para_format:
            right_indent = para_format['right_indent']
            if isinstance(right_indent, str):
                right_indent = float(re.search(r'(\d+(\.\d+)?)', right_indent).group(1))
            paragraph.paragraph_format.right_indent = Pt(right_indent)
        
        # 设置段前间距
        if 'before_spacing' in para_format:
            before_spacing = para_format['before_spacing']
            if isinstance(before_spacing, str):
                before_spacing = float(re.search(r'(\d+(\.\d+)?)', before_spacing).group(1))
            paragraph.paragraph_format.space_before = Pt(before_spacing)
        
        # 设置段后间距
        if 'after_spacing' in para_format:
            after_spacing = para_format['after_spacing']
            if isinstance(after_spacing, str):
                after_spacing = float(re.search(r'(\d+(\.\d+)?)', after_spacing).group(1))
            paragraph.paragraph_format.space_after = Pt(after_spacing)
        
        # 设置行间距
        if 'line_spacing' in para_format:
            line_spacing = self._get_line_spacing_value(para_format['line_spacing'])
            if isinstance(line_spacing, float):
                # 倍行距
                paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
                paragraph.paragraph_format.line_spacing = line_spacing
            else:
                # 固定磅值
                paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
                paragraph.paragraph_format.line_spacing = line_spacing
    
    def set_font_format(self, run, font_format: Dict):
        """
        设置字体格式
        
        Args:
            run: 文本运行对象
            font_format: 字体格式配置
        """
        # 设置中文字体
        if 'zh_family' in font_format:
            run.font.name = font_format['zh_family']
            run._element.rPr.rFonts.set(qn('w:eastAsia'), font_format['zh_family'])
        
        # 设置英文字体
        if 'en_family' in font_format:
            run.font.name = font_format['en_family']
        
        # 设置字号
        if 'size' in font_format:
            size = font_format['size']
            if isinstance(size, str):
                size = float(re.search(r'(\d+(\.\d+)?)', size).group(1))
            run.font.size = Pt(size)
        
        # 设置加粗
        if 'bold' in font_format:
            bold = font_format['bold']
            if isinstance(bold, str):
                bold = bold.lower() == 'true'
            run.font.bold = bold
        
        # 设置斜体
        if 'italic' in font_format:
            italic = font_format['italic']
            if isinstance(italic, str):
                italic = italic.lower() == 'true'
            run.font.italic = italic
        
        # 设置全大写
        if 'isAllcaps' in font_format:
            all_caps = font_format['isAllcaps']
            if isinstance(all_caps, str):
                all_caps = all_caps.lower() == 'true'
            run.font.all_caps = all_caps
        
        # 设置颜色
        if 'color' in font_format:
            r, g, b = self._parse_color(font_format['color'])
            run.font.color.rgb = RGBColor(r, g, b)
    
    def apply_format_to_paragraph(self, paragraph, para_config: Dict):
        """
        应用格式到段落
        
        Args:
            paragraph: 段落对象
            para_config: 段落配置
        """
        # 设置段落格式
        if 'paragraph_format' in para_config:
            self.set_paragraph_format(paragraph, para_config['paragraph_format'])
        
        # 设置字体格式
        if 'fonts' in para_config:
            # 如果段落没有runs，添加一个空的run
            if len(paragraph.runs) == 0:
                run = paragraph.add_run(paragraph.text)
                self.set_font_format(run, para_config['fonts'])
            else:
                # 对每个run应用字体格式
                for run in paragraph.runs:
                    self.set_font_format(run, para_config['fonts'])
    
    def apply_format_by_type(self, para_type: str, para_config: Dict):
        """
        根据段落类型应用格式
        
        Args:
            para_type: 段落类型
            para_config: 段落配置
        """
        # 有paragraph_manager优先使用
        if self.paragraph_manager:
            for i, paragraph in enumerate(self.doc.paragraphs):
                if i in self.para_type_map and self.para_type_map[i] == para_type:
                    self.apply_format_to_paragraph(paragraph, para_config)
        else:
            # 遍历文档中的所有段落
            for paragraph in self.doc.paragraphs:
                # 根据段落文本内容判断类型
                current_type = self._determine_para_type(paragraph.text)
                if current_type == para_type:
                    self.apply_format_to_paragraph(paragraph, para_config)
    
    def _determine_para_type(self, text: str) -> str:
        """
        简单判断段落类型，实际项目中可能需要更复杂的逻辑
        
        Args:
            text: 段落文本
            
        Returns:
            段落类型
        """
        # 这里只是一个简单的示例，实际项目中可能需要更复杂的逻辑
        text = text.strip()
        if not text:
            return ParsedParaType.OTHERS.value
        
        # 判断标题
        if re.match(r'^第[一二三四五六七八九十]+章', text):
            return ParsedParaType.HEADING1.value
        elif re.match(r'^\d+\.\d+', text):
            return ParsedParaType.HEADING2.value
        elif re.match(r'^\d+\.\d+\.\d+', text):
            return ParsedParaType.HEADING3.value
        
        # 判断摘要
        if '摘要' in text and len(text) < 10:
            return ParsedParaType.ABSTRACT_ZH.value
        elif 'Abstract' in text and len(text) < 15:
            return ParsedParaType.ABSTRACT_EN.value
        
        # 判断关键词
        if '关键词' in text and len(text) < 10:
            return ParsedParaType.KEYWORDS_ZH.value
        elif 'Keywords' in text and len(text) < 15:
            return ParsedParaType.KEYWORDS_EN.value
        
        # 默认为正文
        return ParsedParaType.BODY.value
    
    def apply_format_with_manager(self, config: Dict):
        """
        使用段落管理器应用格式
        
        Args:
            config: 格式配置
        """
        if not self.paragraph_manager:
            raise ValueError("需要提供段落管理器才能使用此方法")
            
        # 应用格式
        for i, paragraph in enumerate(self.doc.paragraphs):
            if i in self.para_type_map:
                para_type = self.para_type_map[i]
                if para_type in config:
                    self.apply_format_to_paragraph(paragraph, config[para_type])
    
    def apply_config(self, config_path: str):
        """
        应用配置文件
        
        Args:
            config_path: 配置文件路径
        """
        # 加载配置文件
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 设置纸张格式
        if 'paper' in config:
            self.set_paper_format(config['paper'])
        
        # 应用段落格式
        if self.paragraph_manager:
            # 使用段落管理器应用格式
            self.apply_format_with_manager(config)
        else:
            # 判断段落类型并应用格式
            for para_type, para_config in config.items():
                if para_type != 'paper':  # 排除纸张配置
                    self.apply_format_by_type(para_type, para_config)
        
        # 保存文档
        return self.save()
    
    # 以下为新增的工具函数，方便大模型调用
    
    def get_document_content(self) -> str:
        """
        获取文档内容
        
        Returns:
            文档内容字符串
        """
        return "\n".join([para.text for para in self.doc.paragraphs])
    
    def get_paragraph_content(self, index: int) -> str:
        """
        获取指定段落的内容
        
        Args:
            index: 段落索引
            
        Returns:
            段落内容
        """
        if 0 <= index < len(self.doc.paragraphs):
            return self.doc.paragraphs[index].text
        return ""
    
    def modify_paragraph_content(self, index: int, new_content: str) -> bool:
        """
        修改指定段落的内容
        
        Args:
            index: 段落索引
            new_content: 新内容
            
        Returns:
            是否修改成功
        """
        if 0 <= index < len(self.doc.paragraphs):
            # 清除原有内容
            p = self.doc.paragraphs[index]
            for run in p.runs:
                run.text = ""
            # 添加新内容
            p.add_run(new_content)
            return True
        return False
    
    def set_paragraph_alignment(self, index: int, alignment: str) -> bool:
        """
        设置段落对齐方式
        
        Args:
            index: 段落索引
            alignment: 对齐方式，支持 "左对齐", "居中", "右对齐", "两端对齐" 
                      或 "left", "center", "right", "justify"
                      
        Returns:
            是否设置成功
        """
        if 0 <= index < len(self.doc.paragraphs):
            p = self.doc.paragraphs[index]
            p.alignment = self._get_alignment_value(alignment)
            return True
        return False
    
    def set_paragraph_font(self, index: int, font_config: Dict) -> bool:
        """
        设置段落字体格式
        
        Args:
            index: 段落索引
            font_config: 字体配置，如 {"zh_family": "宋体", "en_family": "Times New Roman", 
                         "size": 12, "bold": True, "italic": False, "color": "黑色"}
                         
        Returns:
            是否设置成功
        """
        if 0 <= index < len(self.doc.paragraphs):
            p = self.doc.paragraphs[index]
            if not p.runs:
                run = p.add_run(p.text)
                self.set_font_format(run, font_config)
            else:
                for run in p.runs:
                    self.set_font_format(run, font_config)
            return True
        return False
    
    def add_paragraph(self, content: str, position: int = -1) -> int:
        """
        添加段落
        
        Args:
            content: 段落内容
            position: 插入位置，-1表示添加到文档末尾
            
        Returns:
            新段落的索引
        """
        if position < 0 or position >= len(self.doc.paragraphs):
            p = self.doc.add_paragraph(content)
            return len(self.doc.paragraphs) - 1
        else:
            # 在指定位置插入段落
            p = self.doc.paragraphs[position]
            new_p = p._element.addnext(docx.oxml.shared.OxmlElement('w:p'))
            new_p = docx.text.paragraph.Paragraph(new_p, p._parent)
            new_p.add_run(content)
            return position + 1
    
    def delete_paragraph(self, index: int) -> bool:
        """
        删除段落
        
        Args:
            index: 段落索引
            
        Returns:
            是否删除成功
        """
        if 0 <= index < len(self.doc.paragraphs):
            p = self.doc.paragraphs[index]
            p._element.getparent().remove(p._element)
            return True
        return False
    
    def apply_style_to_paragraph_by_type(self, para_type: str, style_config: Dict) -> int:
        """
        根据段落类型应用样式
        
        Args:
            para_type: 段落类型
            style_config: 样式配置
            
        Returns:
            修改的段落数量
        """
        count = 0
        if self.paragraph_manager:
            for i, paragraph in enumerate(self.doc.paragraphs):
                if i in self.para_type_map and self.para_type_map[i] == para_type:
                    self.apply_format_to_paragraph(paragraph, style_config)
                    count += 1
        else:
            for paragraph in self.doc.paragraphs:
                current_type = self._determine_para_type(paragraph.text)
                if current_type == para_type:
                    self.apply_format_to_paragraph(paragraph, style_config)
                    count += 1
        return count
    
    def list_all_paragraphs(self) -> List[Dict]:
        """
        列出所有段落信息
        
        Returns:
            段落信息列表，每个元素包含索引、内容和类型
        """
        paragraphs = []
        for i, p in enumerate(self.doc.paragraphs):
            para_type = self.para_type_map.get(i, self._determine_para_type(p.text)) if hasattr(self, 'para_type_map') else self._determine_para_type(p.text)
            paragraphs.append({
                "index": i,
                "content": p.text,
                "type": para_type
            })
        return paragraphs


def format_document(doc_path: str, config_path: str, output_path: Optional[str] = None, paragraph_manager: Optional[ParagraphManager] = None):
    """
    格式化文档
    
    Args:
        doc_path: 文档路径
        config_path: 配置文件路径
        output_path: 输出路径，如果为None则覆盖原文件
        paragraph_manager: 段落管理器，如果为None则自动判断段落类型
        
    Returns:
        是否成功
    """
    editor = FormatEditor(doc_path, paragraph_manager)
    editor.apply_config(config_path)
    if output_path:
        return editor.save(output_path)
    return True
