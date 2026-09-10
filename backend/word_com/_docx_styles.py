"""样式继承解析：还原 OOXML 中段落实际生效的字体与段落格式。

python-docx 只暴露段落 / run 上**显式声明**的属性，而 Word 文档中绝大多数格式
来自继承链：

1. run 自身的 ``rPr``
2. 段落样式（含 ``basedOn`` 链）的 ``rPr``
3. ``docDefaults`` → ``rPrDefault`` → ``rPr``

字体还可能通过 ``w:eastAsiaTheme`` / ``w:asciiTheme`` 等属性引用
``word/theme/theme1.xml`` 中的主题字体，此时 run 上没有显式字体名。

本模块按上述优先级逐级回退，并解析主题字体引用，把 ``+中文正文`` 这类
本地化主题别名还原为实际字体名（如 ``等线``）。全部为**只读**解析，
不会向文档注入任何节点。
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterator, List, Optional

from docx.oxml.ns import qn

# twips → cm（1 inch = 1440 twips = 2.54cm）
_TWIPS_TO_CM = 2.54 / 1440.0

# 主题别名 → 主题槽位。中文版 Word 把 minor/major East Asian 显示为
# “+中文正文 / +中文标题”，西文为 “+Body / +Headings”。
_ALIAS_SLOTS: Dict[str, str] = {
    "+中文正文": "minorEastAsia",
    "+正文": "minorEastAsia",
    "+body": "minorHAnsi",
    "+西文正文": "minorHAnsi",
    "+中文标题": "majorEastAsia",
    "+标题": "majorEastAsia",
    "+headings": "majorHAnsi",
    "+heading": "majorHAnsi",
    "+西文标题": "majorHAnsi",
}

# 可直接作为主题槽位出现的属性值
_THEME_SLOTS = (
    "minorHAnsi",
    "minorEastAsia",
    "minorBidi",
    "majorHAnsi",
    "majorEastAsia",
    "majorBidi",
)


def _twips_to_cm(value: Any) -> float:
    try:
        return round(float(value) * _TWIPS_TO_CM, 2)
    except (TypeError, ValueError):
        return 0.0


def _int_or_none(value: Any) -> Optional[int]:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------
# 主题字体
# --------------------------------------------------------------------------

def _pick_script_typeface(body: str, script: str) -> str:
    """从 ``<a:font script="Hans" typeface="等线"/>`` 中取出字体名。"""
    for match in re.finditer(r"<a:font\b[^>]*>", body):
        tag = match.group(0)
        s = re.search(r'script="([^"]*)"', tag)
        t = re.search(r'typeface="([^"]*)"', tag)
        if s and t and s.group(1).strip() == script:
            return t.group(1).strip()
    return ""


def _pick_typeface(body: str, kind: str) -> str:
    """取出 ``<a:latin|ea|cs typeface="..."/>`` 的字体名。"""
    match = re.search(r"<a:" + kind + r"\b[^>]*\btypeface=\"([^\"]*)\"", body)
    return match.group(1).strip() if match else ""


class ThemeFonts:
    """``theme1.xml`` 的主题字体映射（majorFont / minorFont）。"""

    def __init__(self, doc: Any):
        self._map: Dict[str, str] = {}
        xml = self._read_theme_xml(doc)
        if not xml:
            return
        for tag, prefix in (("majorFont", "major"), ("minorFont", "minor")):
            match = re.search(
                r"<a:" + tag + r"\b[^>]*>(.*?)</a:" + tag + r">", xml, re.S
            )
            if not match:
                continue
            body = match.group(1)
            latin = _pick_typeface(body, "latin")
            # <a:ea> 为空是 Word 中文主题的常见写法，此时按 Hans 脚本回退
            east_asia = (
                _pick_typeface(body, "ea")
                or _pick_script_typeface(body, "Hans")
                or latin
            )
            csl = _pick_typeface(body, "cs") or latin
            self._map[prefix + "HAnsi"] = latin
            self._map[prefix + "Ascii"] = latin
            self._map[prefix + "EastAsia"] = east_asia
            self._map[prefix + "Bidi"] = csl

    @staticmethod
    def _read_theme_xml(doc: Any) -> str:
        try:
            from docx.opc.constants import RELATIONSHIP_TYPE as RT

            part = doc.part.part_related_by(RT.THEME)
            return part.blob.decode("utf-8")
        except Exception:
            return ""

    def resolve(self, theme_name: Optional[str]) -> str:
        """把 ``minorEastAsia`` 这类主题槽位解析为实际字体名。"""
        if not theme_name:
            return ""
        return self._map.get(str(theme_name).strip(), "")

    def resolve_alias(self, name: str) -> str:
        """把 ``+中文正文`` 这类主题别名解析为实际字体名。"""
        if not name:
            return ""
        key = str(name).strip()
        low = key.lower()
        slot: Optional[str] = None
        for alias, target in _ALIAS_SLOTS.items():
            if low == alias.lower():
                slot = target
                break
        if slot is None and key.startswith("+"):
            candidate = key[1:].strip()
            if candidate in _THEME_SLOTS:
                slot = candidate
        if slot is None:
            return ""
        return self._map.get(slot, "")

    def alias_map(self) -> Dict[str, str]:
        """返回 ``{"+中文正文": "等线", "+中文标题": "等线 Light"}`` 形式的映射。"""
        result: Dict[str, str] = {}
        for alias, slot in _ALIAS_SLOTS.items():
            name = self._map.get(slot)
            if name:
                result[alias] = name
        return result


# --------------------------------------------------------------------------
# 只读属性读取
# --------------------------------------------------------------------------

def rfonts_attr(rPr: Any, attr: str) -> Optional[str]:
    """只读读取 ``rPr/rFonts`` 的属性；不创建任何节点。"""
    if rPr is None:
        return None
    try:
        rfonts = rPr.find(qn("w:rFonts"))
    except Exception:
        return None
    if rfonts is None:
        return None
    value = rfonts.get(qn(attr))
    return str(value) if value else None


def _style_id(style: Any) -> Optional[str]:
    return getattr(style, "style_id", None)


def iter_rpr_sources(para: Any, doc: Any) -> Iterator[Any]:
    """按优先级降序产出可继承的 ``rPr``：段落样式链 → docDefaults。"""
    style = getattr(para, "style", None)
    seen = set()
    while style is not None:
        sid = _style_id(style)
        if sid is not None and sid in seen:
            break
        if sid is not None:
            seen.add(sid)
        try:
            rPr = style.element.find(qn("w:rPr"))
        except Exception:
            rPr = None
        if rPr is not None:
            yield rPr
        try:
            style = style.base_style
        except Exception:
            style = None

    defaults = _doc_defaults_rpr(doc)
    if defaults is not None:
        yield defaults


def iter_ppr_sources(para: Any, doc: Any) -> Iterator[Any]:
    """按优先级降序产出可继承的 ``pPr``：段落自身 → 样式链 → docDefaults。"""
    try:
        own = para._element.find(qn("w:pPr"))
    except Exception:
        own = None
    if own is not None:
        yield own

    style = getattr(para, "style", None)
    seen = set()
    while style is not None:
        sid = _style_id(style)
        if sid is not None and sid in seen:
            break
        if sid is not None:
            seen.add(sid)
        try:
            pPr = style.element.find(qn("w:pPr"))
        except Exception:
            pPr = None
        if pPr is not None:
            yield pPr
        try:
            style = style.base_style
        except Exception:
            style = None

    defaults = _doc_defaults_ppr(doc)
    if defaults is not None:
        yield defaults


def _doc_defaults_rpr(doc: Any) -> Any:
    container = _doc_defaults(doc)
    if container is None:
        return None
    rPrDefault = container.find(qn("w:rPrDefault"))
    return rPrDefault.find(qn("w:rPr")) if rPrDefault is not None else None


def _doc_defaults_ppr(doc: Any) -> Any:
    container = _doc_defaults(doc)
    if container is None:
        return None
    pPrDefault = container.find(qn("w:pPrDefault"))
    return pPrDefault.find(qn("w:pPr")) if pPrDefault is not None else None


def _doc_defaults(doc: Any) -> Any:
    try:
        styles = doc.styles
        root = styles.element if styles is not None else None
    except Exception:
        return None
    if root is None:
        return None
    try:
        return root.find(qn("w:docDefaults"))
    except Exception:
        return None


# --------------------------------------------------------------------------
# 取值助手
# --------------------------------------------------------------------------

def pick_attr(sources: List[Any], tag: str, attr: str) -> Optional[str]:
    for src in sources:
        if src is None:
            continue
        try:
            el = src.find(qn(tag))
        except Exception:
            el = None
        if el is None:
            continue
        value = el.get(qn(attr))
        if value is not None:
            return str(value)
    return None


def pick_val(sources: List[Any], tag: str) -> Optional[str]:
    return pick_attr(sources, tag, "w:val")


def pick_flag(sources: List[Any], tag: str) -> Optional[bool]:
    """三态读取布尔属性：``w:b`` 无 ``val`` 表示 true。"""
    for src in sources:
        if src is None:
            continue
        try:
            el = src.find(qn(tag))
        except Exception:
            el = None
        if el is None:
            continue
        value = el.get(qn("w:val"))
        if value is None:
            return True
        text = str(value).strip().lower()
        if text in ("0", "false", "off"):
            return False
        if text in ("1", "true", "on"):
            return True
    return None


def pick_half_points(sources: List[Any], tag: str) -> Optional[float]:
    """读取以半磅（``w:sz``）存储的字号并换算为磅。"""
    raw = pick_val(sources, tag)
    value = _int_or_none(raw)
    if value is None or value <= 0:
        return None
    return round(value / 2.0, 1)


def pick_color(sources: List[Any]) -> Optional[str]:
    for src in sources:
        if src is None:
            continue
        try:
            el = src.find(qn("w:color"))
        except Exception:
            el = None
        if el is None:
            continue
        raw = el.get(qn("w:val"))
        if not raw:
            continue
        text = str(raw).strip()
        if text.lower() == "auto":
            return "black"
        if len(text) == 6:
            return "#" + text.upper()
    return None


# --------------------------------------------------------------------------
# 对外解析入口
# --------------------------------------------------------------------------

def resolve_fonts(para: Any, doc: Any, theme: ThemeFonts) -> Dict[str, Any]:
    """还原段落首个 run 实际生效的字体、字号、字重与颜色。"""
    info: Dict[str, Any] = {
        "zh_family": "Unknown",
        "en_family": "Unknown",
        "size": 0.0,
        "bold": 0,
        "italic": 0,
        "color": None,
    }
    runs = list(getattr(para, "runs", []) or [])
    if not runs:
        return info
    try:
        run_rPr = runs[0]._element.find(qn("w:rPr"))
    except Exception:
        run_rPr = None
    sources = [run_rPr] + list(iter_rpr_sources(para, doc))

    def font_value(*pairs: str) -> str:
        """pairs 为 (属性名, 是否主题引用) 交替序列。"""
        for index in range(0, len(pairs), 2):
            attr, is_theme = pairs[index], pairs[index + 1]
            for src in sources:
                raw = rfonts_attr(src, attr)
                if not raw:
                    continue
                if is_theme:
                    resolved = theme.resolve(raw)
                    if resolved:
                        return resolved
                    continue
                return raw
        return ""

    def normalize(name: str) -> str:
        if not name:
            return ""
        text = str(name).strip()
        if text.startswith("+"):
            resolved = theme.resolve_alias(text)
            return resolved or text.lstrip("+").strip()
        return text

    zh = normalize(
        font_value(
            "w:eastAsia", False,
            "w:eastAsiaTheme", True,
            "w:ascii", False,
            "w:asciiTheme", True,
        )
    )
    en = normalize(
        font_value(
            "w:ascii", False,
            "w:asciiTheme", True,
            "w:hAnsi", False,
            "w:hAnsiTheme", True,
        )
    )
    if zh:
        info["zh_family"] = zh
    if en:
        info["en_family"] = en

    size = pick_half_points(sources, "w:sz")
    if size:
        info["size"] = size

    bold = pick_flag(sources, "w:b")
    if bold is not None:
        info["bold"] = -1 if bold else 0

    italic = pick_flag(sources, "w:i")
    if italic is not None:
        info["italic"] = -1 if italic else 0

    color = pick_color(sources)
    if color:
        info["color"] = color
    return info


# Word 对齐值 → COM 常量
_JC_TO_CODE = {
    "left": 0,
    "start": 0,
    "center": 1,
    "right": 2,
    "end": 2,
    "both": 3,
    "distribute": 3,
}


def resolve_alignment_code(para: Any, doc: Any) -> int:
    """还原段落对齐（含样式继承），返回 COM 对齐常量。"""
    jc = pick_val(list(iter_ppr_sources(para, doc)), "w:jc")
    if jc is None:
        return 0
    return _JC_TO_CODE.get(str(jc).strip().lower(), 0)


def _find_child(sources: List[Any], tag: str, require_attr: Optional[str] = None) -> Any:
    """在继承链中查找第一个（可含指定属性的）子元素。"""
    for src in sources:
        if src is None:
            continue
        try:
            el = src.find(qn(tag))
        except Exception:
            el = None
        if el is None:
            continue
        if require_attr is not None and el.get(qn(require_attr)) is None:
            continue
        return el
    return None


# lineRule → COM 行距常量
_RULE_AUTO = "auto"
_RULE_EXACT = "exact"
_RULE_AT_LEAST = "atleast"

_WD_LINE_SPACE_SINGLE = 0
_WD_LINE_SPACE_1_5 = 1
_WD_LINE_SPACE_DOUBLE = 2
_WD_LINE_SPACE_AT_LEAST = 3
_WD_LINE_SPACE_EXACTLY = 4
_WD_LINE_SPACE_MULTIPLE = 5


def resolve_line_spacing(para: Any, doc: Any) -> Dict[str, Any]:
    """还原行距（含样式继承）。

    返回 ``{"rule": COM 常量, "spacing": 数值}``。``spacing`` 的约定与
    ``com_utils._line_spacing_to_string`` 保持一致：``MULTIPLE`` 传入
    「倍数 × 12」的磅值，``EXACTLY`` / ``AT_LEAST`` 传入磅值。
    """
    sources = list(iter_ppr_sources(para, doc))
    spacing = _find_child(sources, "w:spacing", require_attr="w:line")
    if spacing is None:
        return {"rule": _WD_LINE_SPACE_SINGLE, "spacing": 12.0}

    line = _int_or_none(spacing.get(qn("w:line")))
    if line is None or line <= 0:
        return {"rule": _WD_LINE_SPACE_SINGLE, "spacing": 12.0}

    rule_attr = (spacing.get(qn("w:lineRule")) or _RULE_AUTO).strip().lower()

    if rule_attr == _RULE_EXACT:
        return {"rule": _WD_LINE_SPACE_EXACTLY, "spacing": round(line / 20.0, 1)}
    if rule_attr == _RULE_AT_LEAST:
        return {"rule": _WD_LINE_SPACE_AT_LEAST, "spacing": round(line / 20.0, 1)}

    # auto：line 以 240 = 单倍行距表示
    multiple = round(line / 240.0, 2)
    if line == 240:
        rule = _WD_LINE_SPACE_SINGLE
    elif line == 360:
        rule = _WD_LINE_SPACE_1_5
    elif line == 480:
        rule = _WD_LINE_SPACE_DOUBLE
    else:
        rule = _WD_LINE_SPACE_MULTIPLE
    return {"rule": rule, "spacing": round(multiple * 12.0, 2)}


def resolve_indents(para: Any, doc: Any) -> Dict[str, float]:
    """还原缩进与段前段后距（含样式继承），单位为厘米。"""
    result = {
        "first_line": 0.0,
        "left": 0.0,
        "right": 0.0,
        "space_before": 0.0,
        "space_after": 0.0,
    }
    sources = list(iter_ppr_sources(para, doc))
    ind = _find_child(sources, "w:ind")

    if ind is not None:
        first_line = ind.get(qn("w:firstLine"))
        if first_line is None:
            hanging = ind.get(qn("w:hanging"))
            first_line = hanging if hanging is not None else None
            if hanging is not None:
                value = _int_or_none(hanging)
                first_line = -value if value is not None else None
        result["first_line"] = _twips_to_cm(first_line) if first_line is not None else 0.0
        result["left"] = _twips_to_cm(ind.get(qn("w:left")) or ind.get(qn("w:start")) or 0)
        result["right"] = _twips_to_cm(ind.get(qn("w:right")) or ind.get(qn("w:end")) or 0)

    before_src = _find_child(sources, "w:spacing", require_attr="w:before")
    if before_src is not None:
        result["space_before"] = _twips_to_cm(before_src.get(qn("w:before")) or 0)

    after_src = _find_child(sources, "w:spacing", require_attr="w:after")
    if after_src is not None:
        result["space_after"] = _twips_to_cm(after_src.get(qn("w:after")) or 0)

    return {k: round(v, 2) for k, v in result.items()}


def theme_alias_map(doc: Any) -> Dict[str, str]:
    """返回文档的主题别名映射，如 ``{"+中文正文": "等线"}``。"""
    try:
        return ThemeFonts(doc).alias_map()
    except Exception:
        return {}


def theme_alias_map_from_path(doc_path: str) -> Dict[str, str]:
    """从文档路径读取主题别名映射；任何失败都返回空字典。

    Word COM 返回的 ``Font.NameFarEast`` 在文档使用主题字体时会给出
    ``+中文正文`` 这类本地化别名。COM 路径下用它把这些别名还原为实际
    字体名，使两个引擎的输出保持一致。
    """
    try:
        from docx import Document as _Doc

        return theme_alias_map(_Doc(doc_path))
    except Exception:
        return {}


def normalize_theme_name(name: Any, aliases: Dict[str, str]) -> str:
    """用别名表规范化单个字体名，非别名原样返回。"""
    if name is None:
        return "Unknown"
    text = str(name).strip()
    if not text:
        return "Unknown"
    if text in aliases:
        return aliases[text]
    if text.startswith("+"):
        # 别名表未覆盖时至少去掉前缀，避免把 "+xxx" 当成字体名展示
        stripped = text.lstrip("+").strip()
        return stripped or "Unknown"
    return text
