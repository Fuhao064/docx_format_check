import re, docx
from typing import Dict, List


def check_reference_format(doc_path: str, required_format: Dict) -> List[Dict]:
    """检查引用和参考文献格式"""
    errors = []

    try:
        doc = docx.Document(doc_path)

        # 获取参考文献格式要求
        reference_format = required_format.get('reference_format', {})
        if not reference_format:
            return errors

        # 获取引用样式
        citation_style = reference_format.get('citation_style', '').lower()
        if not citation_style:
            return errors

        # 查找参考文献部分
        references_start = False
        references = []

        for para in doc.paragraphs:
            text = para.text.strip()

            # 标识参考文献部分的开始
            if text.startswith('参考文献') or text.lower().startswith('references'):
                references_start = True
                continue

            # 收集参考文献条目
            if references_start and text:
                references.append(text)

        # 检查是否有参考文献
        if not references:
            errors.append({
                'message': '未找到参考文献部分或参考文献为空',
                'location': '文档末尾部分'
            })
            return errors

        # 根据不同引用样式检查参考文献格式
        if 'gb' in citation_style or 'gbt' in citation_style:
            # 检查GB/T格式
            ref_errors = _check_gbt_references(references, citation_style)
            for i, error in enumerate(ref_errors):
                if isinstance(error, dict):
                    errors.append(error)
                else:
                    errors.append({
                        'message': error,
                        'location': f"参考文献[{i+1}]"
                    })

        elif 'apa' in citation_style:
            # 检查APA格式
            ref_errors = _check_apa_references(references)
            for i, error in enumerate(ref_errors):
                if isinstance(error, dict):
                    errors.append(error)
                else:
                    errors.append({
                        'message': error,
                        'location': f"参考文献[{i+1}]"
                    })

        elif 'mla' in citation_style:
            # 检查MLA格式
            ref_errors = _check_mla_references(references)
            for i, error in enumerate(ref_errors):
                if isinstance(error, dict):
                    errors.append(error)
                else:
                    errors.append({
                        'message': error,
                        'location': f"参考文献[{i+1}]"
                    })

        else:
            errors.append({
                'message': f"不支持的引用样式: {citation_style}",
                'location': '参考文献格式设置'
            })

    except Exception as e:
        errors.append({
            'message': f"检查参考文献格式时出错: {str(e)}",
            'location': '参考文献部分'
        })

    return errors

def _check_gbt_references(references: List[str], standard: str) -> List[str]:
    """
    检查参考文献是否符合GB/T 7714标准
    """
    errors = []

    # 检查每条参考文献
    for i, ref in enumerate(references):
        # 检查编号格式 [1] 或 [1]
        if not re.match(r'^\[\d+\]', ref):
            errors.append(f"参考文献 #{i+1} 编号格式错误，应以[数字]开头")
            continue

        # 检查作者与题名之间的分隔符
        if '. ' not in ref and '．' not in ref:
            errors.append(f"参考文献 #{i+1} 作者与题名之间缺少正确的分隔符")

        # 检查不同类型文献的格式
        if '[J]' in ref or '[J/OL]' in ref:  # 期刊论文
            if not _check_journal_format(ref, standard):
                errors.append(f"参考文献 #{i+1} 期刊论文格式不符合{standard}标准")
        elif '[M]' in ref:  # 专著
            if not _check_book_format(ref, standard):
                errors.append(f"参考文献 #{i+1} 专著格式不符合{standard}标准")
        elif '[D]' in ref:  # 学位论文
            if not _check_thesis_format(ref, standard):
                errors.append(f"参考文献 #{i+1} 学位论文格式不符合{standard}标准")
        elif '[C]' in ref or '[C/OL]' in ref:  # 会议论文
            if not _check_conference_format(ref, standard):
                errors.append(f"参考文献 #{i+1} 会议论文格式不符合{standard}标准")
        elif '[EB/OL]' in ref:  # 电子资源
            if not _check_electronic_format(ref, standard):
                errors.append(f"参考文献 #{i+1} 电子资源格式不符合{standard}标准")
        else :errors.append(f"不符合的参考文献类型: {ref}")

    return errors

def _check_journal_format(ref: str, standard: str) -> bool:
    """检查期刊论文格式"""
    # GB/T 7714-2015格式: [序号] 作者. 题名[J]. 刊名, 出版年, 卷号(期号): 起止页码.
    # 更灵活的正则表达式，允许一些常见变体
    pattern = r'^\[\d+\]\s+[\w\s,]+\.\s+.+\[J(/OL)?\]\.\s+.+,\s+\d{4}(,\s+\d+(\(\d+\))?)?(\:\s*\d+(-\d+)?)?\.?$'
    return bool(re.match(pattern, ref, re.UNICODE))

def _check_book_format(ref: str, standard: str) -> bool:
    """检查专著格式"""
    # GB/T 7714-2015格式: [序号] 作者. 书名[M]. 版本(第1版不标注). 出版地: 出版社, 出版年: 起止页码.
    # 更灵活的模式
    pattern = r'^\[\d+\]\s+[\w\s,]+\.\s+.+\[M\]\.\s+.*(\:\s+.+,\s+\d{4}(\:\s*\d+(-\d+)?)?)?\.?$'
    return bool(re.match(pattern, ref, re.UNICODE))

def _check_thesis_format(ref: str, standard: str) -> bool:
    """检查学位论文格式"""
    # GB/T 7714-2015格式: [序号] 作者. 题名[D]. 保存地: 保存单位, 出版年.
    # 更灵活的模式
    pattern = r'^\[\d+\]\s+[\w\s,]+\.\s+.+\[D\]\.\s+.*(\:\s+.+,\s+\d{4})?\.?$'
    return bool(re.match(pattern, ref, re.UNICODE))

def _check_conference_format(ref: str, standard: str) -> bool:
    """检查会议论文格式"""
    # GB/T 7714-2015格式: [序号] 作者. 题名[C]. 会议名, 会议地点, 会议年份. 出版地: 出版者, 出版年: 起止页码.
    # 更灵活的模式
    pattern = r'^\[\d+\]\s+[\w\s,]+\.\s+.+\[C(/OL)?\]\.\s+.+(,\s+.+,\s+\d{4})?\.(\s+.+\:\s+.+,\s+\d{4}(\:\s*\d+(-\d+)?)?)?\.?$'
    return bool(re.match(pattern, ref, re.UNICODE))

def _check_electronic_format(ref: str, standard: str) -> bool:
    """检查电子资源格式"""
    # GB/T 7714-2015格式: [序号] 作者. 题名[EB/OL]. 出版地: 出版者, 出版年[引用日期]. 获取和访问路径.
    # 更灵活的模式，网址部分可选
    pattern = r'^\[\d+\]\s+[\w\s,]+\.\s+.+\[EB/OL\]\.(\s+.+\:\s+.+,\s+\d{4})?\s*(\[\d{4}-\d{2}-\d{2}\])?\.(\s+https?://.*)?$'
    return bool(re.match(pattern, ref, re.UNICODE))

def _check_apa_references(references: List[str]) -> List[str]:
    """
    检查参考文献是否符合APA标准
    """
    errors = []
    # APA格式检查逻辑
    for i, ref in enumerate(references):
        # 检查作者格式
        if not re.match(r'^[\w\s,]+\s+\(\d{4}\)', ref):
            errors.append(f"参考文献 #{i+1} 作者和年份格式不符合APA标准")

    return errors

def _check_mla_references(references: List[str]) -> List[str]:
    """
    检查参考文献是否符合MLA标准
    """
    errors = []
    # MLA格式检查逻辑
    for i, ref in enumerate(references):
        # 检查作者格式
        if not re.match(r'^[\w\s,]+\.', ref):
            errors.append(f"参考文献 #{i+1} 作者格式不符合MLA标准")

    return errors
