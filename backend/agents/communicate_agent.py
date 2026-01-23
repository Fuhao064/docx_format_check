import json
from typing import Dict, Optional
from agents.setting import LLMs
from agents.format_agent import FormatAgent
from agents.editor_agent import EditorAgent
from agents.advice_agent import AdviceAgent
from preparation.para_type import ParagraphManager
from utils.utils import parse_llm_json_response
from checkers.format_checker import FormatChecker

class CommunicateAgent:
    def __init__(self, model_name='alibaba_qwen-flash'):
        # 初始化基本LLM客户端
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

        # 初始化可能用到的其他代理，但不立即实例化
        self.format_agent = None
        self.format_checker = None
        self.editor_agent = None
        self.advice_agent = None

    def analyze_intent(self, user_message: str) -> Dict:
        """
        分析用户意图，确定应该使用哪个代理来处理请求

        Args:
            user_message: 用户消息内容

        Returns:
            Dict: 包含意图分析结果
        """
        try:
            if self.client is None:
                return {"agent": "none", "function": "none", "reason": "LLM客户端未初始化"}

            # 准备消息内容
            system_content = """你是一个用户意图分析助手，请分析用户消息并确定最合适的处理代理。
                    返回JSON格式必须包含以下字段：
                    - agent: 应使用的代理类型，可选值为 ["format", "editor", "advice", "communicate", "none"]
                    - function: 该代理应执行的具体功能，可选值为[
                        "search_para_config", "check_format", "fix_format", "check_paragraph_manager",
                        "fix_paragraph_manager", "generate_caption", "enhance_content", "provide_advice",
                        "analyze_paragraph", "analyze_format_issues", "provide_format_fix_suggestions",
                        "generate_format_report", "optimize_document_format", "none"
                    ]
                    - reason: 简单说明做出这个判断的原因

                    特别注意以下几种常见的用户意图：
                    1. 当用户询问"请分析文档中的格式问题"或类似内容时，应返回 {"agent": "format", "function": "analyze_format_issues", "doc_id": current_doc_id}
                    2. 当用户询问"如何修复文档中的格式错误"或类似内容时，应返回 {"agent": "format", "function": "provide_format_fix_suggestions", "doc_id": current_doc_id}
                    3. 当用户提到"生成格式修正报告"或"下载标记文档"时，应返回 {"agent": "format", "function": "generate_format_report", "doc_id": current_doc_id}
                    4. 当用户提到"优化文档格式"或"下载格式化后的文档"时，应返回 {"agent": "format", "function": "optimize_document_format", "doc_id": current_doc_id}
                    """

            # 如果是doubao系列模型，添加额外的JSON格式要求
            if hasattr(self.llm, 'is_doubao_model') and self.llm.is_doubao_model:
                system_content += "\n请确保你的回复是有效的JSON格式，例如: {\"agent\": \"format\", \"function\": \"check_format\", \"reason\": \"用户请求检查文档格式\"}"

            # 准备消息列表
            messages = [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_message}
            ]

            # 根据模型类型决定是否使用response_format参数
            if hasattr(self.llm, 'supports_json_response_format') and self.llm.supports_json_response_format():
                response = self.client.chat.completions.create(
                    model=self.model,
                    response_format={"type": "json_object"},
                    messages=messages
                )
            else:
                # 对于不支持response_format的模型（如doubao系列），不使用该参数
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages
                )

            # 使用parse_llm_json_response函数解析大模型返回的内容
            result = parse_llm_json_response(response.choices[0].message.content)

            # 检查解析结果是否包含必要的字段
            if not isinstance(result, dict) or 'agent' not in result or 'function' not in result:
                print(f"解析结果缺少必要字段: {result}")
                return {"agent": "communicate", "function": "chat", "reason": "解析结果缺少必要字段，默认使用对话功能"}

            return result

        except Exception as e:
            print(f"Error analyzing intent: {e}")
            return {"agent": "communicate", "function": "chat", "reason": f"发生错误，默认使用对话功能: {str(e)}"}

    def get_response(self, user_message: str, doc_content: str, para_manager: Optional[ParagraphManager] = None, config_path: Optional[str] = None, doc_path: Optional[str] = None) -> str:
        """
        获取对用户消息的回复

        Args:
            user_message: 用户消息内容
            doc_content: 文档全文内容
            para_manager: 可选的段落管理器实例
            config_path: 可选的配置文件路径
            doc_path: 可选的文档路径

        Returns:
            str: 回复内容
        """
        # 1. 分析用户意图
        intent = self.analyze_intent(user_message)
        agent_type = intent.get("agent", "communicate")
        function_name = intent.get("function", "chat")
        print(f"意图分析结果: {intent}")

        # 2. 根据意图分发到相应的代理
        if agent_type == "format":
            # 初始化格式代理（如果尚未初始化）
            if self.format_agent is None:
                self.format_agent = FormatAgent(self.model)
            
            # 初始化检查器 (Lazy init)
            if self.format_checker is None:
                self.format_checker = FormatChecker()

            # 处理新增的格式分析和修复功能
            if function_name == "analyze_format_issues":
                if not doc_path or not config_path:
                    return "需要提供文档路径和配置文件路径才能分析格式问题"

                # 分析文档格式问题 (Use Checker)
                errors, para_manager = self.format_checker.analyze_format_issues(doc_path, config_path)

                # 如果没有错误
                if not errors or len(errors) == 0:
                    return "文档格式检查完成，未发现格式问题。"

                # 格式化错误信息
                error_text = "\n".join([f"{i+1}. {error.get('message', '')} (位置: {error.get('location', '未知')})" for i, error in enumerate(errors)])

                return f"文档格式检查完成，发现 {len(errors)} 个格式问题：\n\n{error_text}"

            elif function_name == "provide_format_fix_suggestions":
                if not doc_path or not config_path:
                    return "需要提供文档路径和配置文件路径才能提供修复建议"

                # 如果没有提供错误列表，先分析文档格式问题
                if not para_manager:
                    errors, para_manager = self.format_checker.analyze_format_issues(doc_path, config_path)
                else:
                    # 使用提供的段落管理器检查格式
                    errors = self.format_checker.check_paragraph_manager(para_manager, config_path)

                # 提供修复建议 (Use Agent LLM)
                return self.format_agent.provide_format_fix_suggestions(errors, doc_content)

            elif function_name == "generate_format_report":
                if not doc_path or not config_path:
                    return "需要提供文档路径和配置文件路径才能生成格式修正报告"

                # 如果没有提供错误列表，先分析文档格式问题
                if not para_manager:
                    errors, para_manager = self.format_checker.analyze_format_issues(doc_path, config_path)
                else:
                    # 使用提供的段落管理器检查格式
                    errors = self.format_checker.check_paragraph_manager(para_manager, config_path)

                # 生成格式修正报告 (Use Editor directly)
                try:
                    output_path = mark_document_errors(doc_path, errors, para_manager)
                    return f"格式修正报告生成成功，共发现 {len(errors)} 个格式问题。您可以下载标记文档查看详细错误位置。"
                except Exception as e:
                    return f"生成格式修正报告失败：{str(e)}"

            elif function_name == "optimize_document_format":
                if not doc_path or not config_path:
                    return "需要提供文档路径和配置文件路径才能优化文档格式"

                # 如果没有提供段落管理器，先分析文档格式问题
                if not para_manager:
                    errors, para_manager = self.format_checker.analyze_format_issues(doc_path, config_path)
                else:
                    # 使用提供的段落管理器检查格式
                    errors = self.format_checker.check_paragraph_manager(para_manager, config_path)

                # 优化文档格式 (Use Editor directly)
                try:
                    config = load_config(config_path)
                    dir_name = os.path.dirname(doc_path)
                    base_name = os.path.basename(doc_path)
                    output_path = os.path.join(dir_name, f"formatted_{base_name}")
                    
                    result_path = generate_formatted_doc(config, para_manager, output_path, errors, doc_path)
                    return f"文档格式优化成功。您可以下载格式化后的文档。"
                except Exception as e:
                    return f"优化文档格式失败：{str(e)}"

            # 处理原有的格式分析功能
            elif function_name == "check_paragraph_manager" and para_manager and config_path:
                errors = self.format_checker.check_paragraph_manager(para_manager, config_path)
                return json.dumps({"errors": errors, "count": len(errors)})
                
            elif function_name == "analyze_paragraph" and para_manager:
                # 从用户消息中提取段落索引
                try:
                    para_index = int(user_message.strip().split()[-1])
                    if 0 <= para_index < len(para_manager.paragraphs):
                        para_info = para_manager.paragraphs[para_index]
                        if config_path:
                            config = load_config(config_path)
                            # Get expected format
                            if para_info.type.value in config:
                                expected = config[para_info.type.value]
                                result = self.format_checker.check_paragraph(para_info, expected, para_index)
                                return json.dumps(result)
                            else:
                                return "配置文件中未找到该段落类型的配置"
                        else:
                            return "需要提供配置文件路径才能分析段落"
                    else:
                        return f"段落索引超出范围，有效范围为0-{len(para_manager.paragraphs)-1}"
                except (ValueError, IndexError):
                    return "无法解析段落索引，请提供有效的段落编号"
            else:
                # 默认使用communicate对话功能 (FormatAgent doesn't need to handle chat)
                return self.chat(user_message, doc_content)

        elif agent_type == "editor":
            # 初始化编辑代理（如果尚未初始化）
            if self.editor_agent is None:
                self.editor_agent = EditorAgent(self.model)

            # 根据function_name调用相应的编辑功能
            if function_name == "generate_caption":
                # 为图片生成题注时，可能需要文档上下文
                enhanced_message = f"基于以下文档全文的上下文，请为图片生成题注：\n\n文档全文：\n{doc_content[:2000]}...\n\n图片路径：\n{user_message}"
                return self.editor_agent.get_image_caption(enhanced_message)
            else:
                # 调用editor_agent的默认处理方法，传入文档全文作为上下文
                enhanced_content = f"基于以下文档全文的上下文，请优化内容：\n\n文档全文：\n{doc_content[:2000]}...\n\n需要优化的内容：\n{user_message}"
                return self.editor_agent.enhance_content(enhanced_content, "text")

        elif agent_type == "advice":
            # 初始化建议代理（如果尚未初始化）
            if self.advice_agent is None:
                self.advice_agent = AdviceAgent(self.model)

            # 调用建议功能，传入文档全文
            return self.advice_agent.provide_advice(doc_content)

        else:  # 默认使用communicate对话功能
            return self.chat(user_message, doc_content)



    def chat(self, user_message: str, doc_content: str = "") -> str:
        """
        与用户进行简单对话

        Args:
            user_message: 用户消息内容
            doc_content: 文档全文内容（可选）

        Returns:
            str: 回复内容
        """
        try:
            if self.client is None:
                return "抱歉，我无法处理您的请求，因为LLM客户端未初始化。"

            # 如果提供了文档内容，将其作为上下文添加到用户消息中
            system_content = "你是一个友好的学术写作助手，提供有关文档格式、内容编辑和写作建议的帮助。或者在用户提出任何问题时，你都可以回答。"
            user_content = user_message

            if doc_content and len(doc_content.strip()) > 0:
                system_content += "\n请基于用户提供的文档内容回答问题或提供建议。"
                user_content = f"文档内容：\n{doc_content[:2000]}...\n\n用户问题：\n{user_message}"

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content}
                ]
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"Error in chat: {e}")
            return f"抱歉，处理您的请求时出错：{str(e)}"
