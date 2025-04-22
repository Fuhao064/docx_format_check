from editors.format_editor import apply_paragraph_format
from docx import Document
from docx.enum.text import WD_LINE_SPACING, WD_ALIGN_PARAGRAPH
from docx.shared import Pt

# 创建测试文档
doc = Document()
para = doc.add_paragraph()

# 测试固定值行间距和左对齐
print("测试固定值行间距和左对齐:")
apply_paragraph_format(para, {'line_spacing': 'Fixed value 20pt', 'alignment': '左对齐'})
print(f'行间距规则: {para.paragraph_format.line_spacing_rule}')
print(f'行间距值: {para.paragraph_format.line_spacing}')
print(f'对齐方式: {para.paragraph_format.alignment}')
print(f'预期行间距规则: {WD_LINE_SPACING.EXACTLY}')
print(f'预期行间距值: {Pt(20)}')
print(f'预期对齐方式: {WD_ALIGN_PARAGRAPH.LEFT}')

# 保存测试结果
doc.save('test_format_result.docx')
print("测试文档已保存为 test_format_result.docx")
