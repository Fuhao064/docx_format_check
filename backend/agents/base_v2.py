# backend/agents/base_v2.py
from typing import List, Dict, Any, Optional
import asyncio
import logging

try:
    from openai import AsyncOpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

class BaseAgent:
    """Agent 基类"""

    def __init__(self, model: str = "gpt-4", api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.model = model
        self.conversation_history: List[Dict[str, str]] = []
        self._lock = asyncio.Lock()

        if _OPENAI_AVAILABLE:
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url
            )
        else:
            self.client = None

    async def chat(self, message: str, context: str = "") -> str:
        """与 Agent 对话"""
        if not self.client:
            return "Error: OpenAI client not available"

        async with self._lock:
            system_prompt = self._build_system_prompt(context)

            messages = [
                {"role": "system", "content": system_prompt},
                *self.conversation_history,
                {"role": "user", "content": message}
            ]

            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7
                )

                assistant_message = response.choices[0].message.content or ""

                # 更新对话历史
                self.conversation_history.append({"role": "user", "content": message})
                self.conversation_history.append({"role": "assistant", "content": assistant_message})

                # 限制历史长度
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]

                return assistant_message

            except Exception as e:
                logger.exception(f"chat failed: {e}")
                return f"Error: {str(e)}"

    def _build_system_prompt(self, context: str) -> str:
        """构建系统提示词"""
        return f"""你是一个文档格式分析专家。

{context}

请用专业但易懂的语言回答用户的问题。"""

    def clear_history(self):
        """清除对话历史"""
        self.conversation_history = []

    async def close(self):
        """Close the OpenAI client and release resources"""
        if self.client:
            await self.client.close()
            self.client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
