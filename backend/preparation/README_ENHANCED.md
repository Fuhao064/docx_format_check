# 增强版段落信息提取模块

## 概述

`extract_para_info_enhanced.py` 是 `extract_para_info.py` 的增强版本，结合了 `docx2python` 和 `python-docx` 两者的优势。

## 主要改进

### 1. 层级结构提取

**旧方案 (python-docx 纯模式):**
```python
# 扁平结构，无法识别大纲层级
for para in doc.paragraphs:
    # 无法直接知道这是几级标题
    # 需要手动解析 XML 的 outlineLvl 属性
```

**新方案 (docx2python 增强模式):**
```python
# 嵌套列表结构，天然体现层级
extractor = DocumentHierarchyExtractor(docx_path)
for struct in extractor.structures:
    print(f"层级: L{struct.level}, 类型: {struct.para_type}")
```

### 2. 段落类型智能识别

自动识别段落类型：
- **标题**: heading1, heading2, heading3
- **摘要**: abstract_label, abstract_content
- **关键词**: keywords_label, keywords_content
- **参考文献**: reference
- **正文**: body

### 3. 简化的 API

```python
from preparation.extract_para_info_enhanced import EnhancedParagraphExtractor
from preparation.para_type import ParagraphManager

# 创建提取器
extractor = EnhancedParagraphExtractor("document.docx")

# 创建管理器
manager = ParagraphManager()

# 提取（自动结合层级结构和详细格式）
manager = extractor.extract_with_hierarchy(manager)

# 使用结果
for para in manager.paragraphs:
    print(f"类型: {para.type.value}")
    print(f"内容: {para.content[:50]}...")
    if 'hierarchy' in para.meta:
        print(f"层级: L{para.meta['hierarchy']['level']}")
```

## 对比测试

### 旧版本输出 (纯 python-docx)
```
段落 1: 样式=Normal, 内容=为什么钱很重要
段落 2: 样式=Normal, 内容=Why Survival Requires Money
段落 3: 样式=Normal, 内容=摘要：在现代...
...
无法区分标题层级
```

### 新版本输出 (docx2python 增强)
```
[1] [H]   L0 [heading2        ] 为什么钱很重要
[2] [H]   L0 [heading2        ] Why Survival Requires Money
[3]     L2 [abstract_content  ] 摘要：在现代...
[4]     L2 [abstract_content  ] Abstract: In modern...
[5]     L2 [keywords_content  ] 关键词：钱、生存...
...
✓ 自动识别标题、摘要、关键词等类型
✓ 明确显示层级关系
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `extract_para_info.py` | 原始版本，纯 python-docx 实现 |
| `extract_para_info_enhanced.py` | 增强版本，结合 docx2python |
| `extract_para_info_v2.py` | 实验版本，功能更复杂但不够稳定 |

## 建议

1. **新项目**: 直接使用 `extract_para_info_enhanced.py`
2. **现有项目**: 可以无缝替换，API 向后兼容
3. **性能要求**: 如果不需要层级信息，可使用原始版本

## 依赖安装

```bash
# 必须
pip install python-docx

# 增强功能需要
pip install docx2python
```
