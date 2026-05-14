from __future__ import annotations

import json
from typing import Dict, List, Tuple

from agents.setting import LLMs
from preparation.para_type import ParsedParaType


class FormatAgent:
    def __init__(self, model_name: str = 'alibaba_qwen-flash'):
        self.llm = LLMs()
        try:
            self.llm.set_model(model_name)
            self.model = self.llm.model
            self.client = self.llm.client
        except ValueError as e:
            print(f"Error setting model: {e}")
            self.llm = None
            self.client = None
            self.model = None

    def parse_format(self, doc_content: str, config_json: str = "{}") -> str:
        """Extract format rules from a spec document and return JSON string."""
        if not self.client:
            return config_json if config_json else "{}"

        system_prompt = (
            "You are a document formatting expert. "
            "Extract formatting requirements from the input document and return strict JSON only. "
            "If a default config is provided, keep its schema and fill values based on the document."
        )

        user_prompt = (
            "Default config schema (JSON):\n"
            f"{config_json}\n\n"
            "Format requirement document content:\n"
            f"{doc_content[:12000]}"
        )

        try:
            kwargs = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
            if hasattr(self.llm, "supports_json_response_format") and self.llm.supports_json_response_format():
                kwargs["response_format"] = {"type": "json_object"}

            response = self.client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content
            if not content:
                return config_json if config_json else "{}"

            # Validate JSON shape early to avoid propagating invalid payloads.
            try:
                json.loads(content)
                return content
            except Exception:
                return config_json if config_json else "{}"
        except Exception as e:
            print(f"parse_format failed: {e}")
            return config_json if config_json else "{}"

    def provide_format_fix_suggestions(self, errors: List[Dict], doc_content: str = "") -> str:
        if not errors:
            return "No formatting issues found."
        if not self.client:
            return "Error: LLM client not initialized."

        error_summary = "\n".join([f"- {e.get('message', 'Unknown')} ({e.get('location', 'N/A')})" for e in errors[:10]])
        if len(errors) > 10:
            error_summary += f"\n... and {len(errors)-10} more issues"

        prompt = (
            "I found the following formatting issues:\n"
            f"{error_summary}\n\n"
            "Please provide actionable fixes in numbered steps."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a document formatting expert. Give concise, practical fixes.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating fix suggestions: {str(e)}"

    def llm_predict_para_type(
        self,
        para_string: str,
        para_meta: dict,
        prev_para_type: ParsedParaType,
        next_para_type: ParsedParaType,
        next_para_content: str,
        processed_paragraphs: list,
    ) -> Tuple[ParsedParaType, float]:
        if not self.client:
            return ParsedParaType.BODY, 0.5

        context_info = []
        if prev_para_type:
            context_info.append(f"prev={prev_para_type.value}")
        if next_para_type:
            context_info.append(f"next={next_para_type.value}")
        if next_para_content:
            context_info.append(f"next_content={next_para_content[:80]}")

        # 提取格式特征
        format_features = []
        if para_meta:
            pf = para_meta.get('paragraph_format', {})
            fonts = para_meta.get('fonts', {})

            # 对齐方式
            alignment = pf.get('alignment', '')
            if alignment:
                format_features.append(f"alignment={alignment}")

            # 字体大小
            sizes = fonts.get('size', set())
            if sizes:
                avg_size = sum(s for s in sizes if isinstance(s, (int, float))) / len(sizes) if sizes else 0
                if avg_size >= 16:
                    format_features.append(f"font_size=large({avg_size}pt)")
                elif avg_size >= 12:
                    format_features.append(f"font_size=medium({avg_size}pt)")
                else:
                    format_features.append(f"font_size=small({avg_size}pt)")

            # 是否加粗
            bold = fonts.get('bold', set())
            if True in bold:
                format_features.append("bold=True")

            # 首行缩进
            first_line_indent = pf.get('first_line_indent', 0)
            if first_line_indent and first_line_indent > 0:
                format_features.append(f"first_line_indent={first_line_indent}")

        user_content = (
            "Classify paragraph type based on content and formatting.\n\n"
            "Classification rules:\n"
            "- title_zh/title_en: Document title, usually centered, bold, larger font (>=16pt)\n"
            "- abstract_zh/abstract_en: Abstract label (e.g., '摘要：' or 'Abstract:')\n"
            "- abstract_content_zh/abstract_content_en: Content after abstract label\n"
            "- keywords_zh/keywords_en: Keywords label (e.g., '关键词：' or 'Keywords:')\n"
            "- keywords_content_zh/keywords_content_en: Content after keywords label\n"
            "- heading1: Main section heading (e.g., '一、...', '二、...')\n"
            "- heading2: Subsection heading (e.g., '1、...', '2、...')\n"
            "- references: References label (e.g., '参考文献：')\n"
            "- references_content: Reference entries (e.g., '[1] ...')\n"
            "- body: Regular paragraph text\n\n"
            f"Paragraph: {para_string}\n"
            f"Format features: {', '.join(format_features) if format_features else 'none'}\n"
            f"Context: {'; '.join(context_info) if context_info else 'none'}\n"
            f"Return ONLY one enum value from: {[t.value for t in ParsedParaType]}"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a document paragraph classifier. Analyze the paragraph content and formatting to determine its type. Return only the enum value.",
                    },
                    {"role": "user", "content": user_content},
                ],
            )
            result = (response.choices[0].message.content or "").strip().strip('"').strip("'").lower()
            valid_types = [t.value for t in ParsedParaType]
            if result in valid_types:
                return ParsedParaType(result), 0.9
            if "abstract" in result and "zh" in result:
                return ParsedParaType.ABSTRACT_CONTENT_ZH, 0.8
            if "abstract" in result and "en" in result:
                return ParsedParaType.ABSTRACT_CONTENT_EN, 0.8
            if "keyword" in result and "zh" in result:
                return ParsedParaType.KEYWORDS_CONTENT_ZH, 0.8
            if "keyword" in result and "en" in result:
                return ParsedParaType.KEYWORDS_CONTENT_EN, 0.8
            if "reference" in result:
                return ParsedParaType.REFERENCES_CONTENT, 0.8
            return ParsedParaType.BODY, 0.7
        except Exception as e:
            print(f"LLM prediction failed: {str(e)}")
            return ParsedParaType.BODY, 0.5
