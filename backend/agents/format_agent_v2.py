# backend/agents/format_agent_v2.py
from typing import List, Dict, Any
import json
import logging
from .base_v2 import BaseAgent

logger = logging.getLogger(__name__)

class FormatAgentV2(BaseAgent):
    """格式分析 Agent v2"""

    async def parse_format(
        self,
        doc_content: str,
        config_json: str = "{}"
    ) -> str:
        """解析格式要求文档，生成配置"""
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

        if not self.client:
            return config_json if config_json else "{}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            # Try with json_object response_format first
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"}
            )
        except Exception:
            # Fallback without response_format for models that don't support it
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages
                )
            except Exception as e:
                logger.exception(f"parse_format failed: {e}")
                return config_json if config_json else "{}"

        try:
            content = response.choices[0].message.content
            if not content:
                return config_json if config_json else "{}"

            # 验证 JSON 格式
            json.loads(content)
            return content

        except Exception as e:
            logger.exception(f"parse_format response processing failed: {e}")
            return config_json if config_json else "{}"

    async def provide_fix_suggestions(
        self,
        errors: List[Dict],
        doc_content: str = ""  # Reserved for future use
    ) -> str:
        """提供修复建议"""
        if not errors:
            return "未发现格式问题。"

        error_summary = "\n".join([
            f"- {e.get('message', 'Unknown')} ({e.get('location', 'N/A')})"
            for e in errors[:10]
        ])
        if len(errors) > 10:
            error_summary += f"\n... 还有 {len(errors)-10} 个问题"

        context = "你是一个文档格式修复专家。请提供简洁、可操作的修复建议。"
        prompt = (
            "发现以下格式问题:\n"
            f"{error_summary}\n\n"
            "请提供可操作的修复步骤。"
        )

        return await self.chat(prompt, context=context)
