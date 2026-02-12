from __future__ import annotations

import json
import os
from typing import Dict, Optional

from agents.advice_agent import AdviceAgent
from agents.editor_agent import EditorAgent
from agents.format_agent import FormatAgent
from agents.setting import LLMs
from checkers.format_checker import FormatChecker
from editors.document_marker import mark_document_errors
from editors.format_editor import generate_formatted_doc, load_config
from preparation.para_type import ParagraphManager
from utils.utils import parse_llm_json_response


class CommunicateAgent:
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

        self.format_agent: Optional[FormatAgent] = None
        self.format_checker: Optional[FormatChecker] = None
        self.editor_agent: Optional[EditorAgent] = None
        self.advice_agent: Optional[AdviceAgent] = None

    def analyze_intent(self, user_message: str) -> Dict:
        if self.client is None:
            return {"agent": "communicate", "function": "chat", "reason": "LLM not initialized"}

        system_prompt = (
            "Classify the user request and return JSON with keys: agent, function, reason. "
            "agent must be one of [format, editor, advice, communicate, none]. "
            "function should be one of [analyze_format_issues, provide_format_fix_suggestions, "
            "generate_format_report, optimize_document_format, analyze_paragraph, provide_advice, chat]."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        try:
            kwargs = {"model": self.model, "messages": messages}
            if hasattr(self.llm, "supports_json_response_format") and self.llm.supports_json_response_format():
                kwargs["response_format"] = {"type": "json_object"}
            response = self.client.chat.completions.create(**kwargs)
            parsed = parse_llm_json_response(response.choices[0].message.content)
            if isinstance(parsed, dict) and parsed.get("agent") and parsed.get("function"):
                return parsed
        except Exception as e:
            print(f"Error analyzing intent: {e}")

        return {"agent": "communicate", "function": "chat", "reason": "fallback"}

    def get_response(
        self,
        user_message: str,
        doc_content: str,
        para_manager: Optional[ParagraphManager] = None,
        config_path: Optional[str] = None,
        doc_path: Optional[str] = None,
    ) -> str:
        intent = self.analyze_intent(user_message)
        agent_type = intent.get("agent", "communicate")
        function_name = intent.get("function", "chat")

        if agent_type == "format":
            if self.format_agent is None:
                self.format_agent = FormatAgent(self.model)
            if self.format_checker is None:
                self.format_checker = FormatChecker()

            if function_name == "analyze_format_issues":
                if not doc_path or not config_path:
                    return "Missing doc_path or config_path"
                errors, _ = self.format_checker.analyze_format_issues(doc_path, config_path, self.format_agent)
                if not errors:
                    return "No format issues found."
                lines = [f"{i+1}. {e.get('message', '')} ({e.get('location', 'N/A')})" for i, e in enumerate(errors)]
                return "\n".join(lines)

            if function_name == "provide_format_fix_suggestions":
                if not doc_path or not config_path:
                    return "Missing doc_path or config_path"
                if para_manager:
                    errors = self.format_checker.check_paragraph_manager(para_manager, config_path)
                else:
                    errors, para_manager = self.format_checker.analyze_format_issues(doc_path, config_path, self.format_agent)
                return self.format_agent.provide_format_fix_suggestions(errors, doc_content)

            if function_name == "generate_format_report":
                if not doc_path or not config_path:
                    return "Missing doc_path or config_path"
                if para_manager:
                    errors = self.format_checker.check_paragraph_manager(para_manager, config_path)
                else:
                    errors, para_manager = self.format_checker.analyze_format_issues(doc_path, config_path, self.format_agent)
                output_path = mark_document_errors(doc_path, errors, para_manager)
                return f"Report generated: {output_path}"

            if function_name == "optimize_document_format":
                if not doc_path or not config_path:
                    return "Missing doc_path or config_path"
                if para_manager is None:
                    _, para_manager = self.format_checker.analyze_format_issues(doc_path, config_path, self.format_agent)
                config = load_config(config_path)
                output_path = os.path.join(os.path.dirname(doc_path), f"formatted_{os.path.basename(doc_path)}")
                result_path = generate_formatted_doc(config, para_manager, output_path, [], doc_path)
                return f"Formatted document generated: {result_path}"

            if function_name == "analyze_paragraph" and para_manager is not None:
                try:
                    para_index = int(user_message.strip().split()[-1])
                    if not config_path:
                        return "Missing config_path"
                    if not (0 <= para_index < len(para_manager.paragraphs)):
                        return "Paragraph index out of range"
                    para_info = para_manager.paragraphs[para_index]
                    config = load_config(config_path)
                    if para_info.type.value not in config:
                        return "Paragraph type not configured"
                    result = self.format_checker.check_paragraph(para_info, config[para_info.type.value], para_index)
                    return json.dumps(result, ensure_ascii=False)
                except Exception as e:
                    return f"Analyze paragraph failed: {e}"

            return self.chat(user_message, doc_content)

        if agent_type == "editor":
            if self.editor_agent is None:
                self.editor_agent = EditorAgent(self.model)
            return self.editor_agent.enhance_content(user_message, "text")

        if agent_type == "advice":
            if self.advice_agent is None:
                self.advice_agent = AdviceAgent(self.model)
            return self.advice_agent.provide_advice(doc_content)

        return self.chat(user_message, doc_content)

    def chat(self, user_message: str, doc_content: str = "") -> str:
        if self.client is None:
            return "Error: LLM client not initialized."

        try:
            system_content = (
                "You are a writing assistant. Provide concise and practical help about document formatting and content."
            )
            user_content = user_message
            if doc_content and doc_content.strip():
                user_content = f"Document content:\n{doc_content[:3000]}\n\nUser request:\n{user_message}"

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content},
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error in chat: {str(e)}"
