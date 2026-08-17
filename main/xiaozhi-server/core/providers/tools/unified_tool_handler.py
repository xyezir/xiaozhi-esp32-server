"""统一工具处理器"""

import json
from copy import deepcopy
from typing import Dict, List, Any, Optional
from config.logger import setup_logging
from plugins_func.loadplugins import auto_import_modules

from .base import ToolType
from plugins_func.register import Action, ActionResponse
from .unified_tool_manager import ToolManager
from .server_plugins import ServerPluginExecutor
from .server_mcp import ServerMCPExecutor
from .device_iot import DeviceIoTExecutor
from .device_mcp import DeviceMCPExecutor
from .mcp_endpoint import MCPEndpointExecutor
from core.handle.sendAudioHandle import send_display_message


class UnifiedToolHandler:
    """统一工具处理器"""

    _RAG_FIRST_ROLE_ID = "pet_expert_shilang"
    _RAG_TOOL_NAME = "retrieve_from_cyjdata"
    _WEB_SEARCH_TOOL_NAMES = frozenset({"bailian_web_search"})
    _WEB_AUTHORIZATION_PHRASES = (
        "联网查",
        "联网搜索",
        "上网查",
        "网上查",
        "互联网查",
        "搜索互联网",
        "搜索网页",
        "网络搜索",
        "可以联网",
        "允许联网",
        "同意联网",
        "确认联网",
    )
    _WEB_NEGATION_PHRASES = (
        "不要联网",
        "别联网",
        "无需联网",
        "不允许联网",
        "不要上网",
        "别上网",
        "不要网上查",
    )
    _AFFIRMATIVE_REPLIES = frozenset(
        {"可以", "可以的", "好", "好的", "行", "同意", "确认", "查吧", "去查吧"}
    )
    _RAG_INSUFFICIENT_MARKERS = (
        "没有找到足够可靠的资料",
        "现有资料不足以可靠回答",
        "内部检索暂时不可用",
        "检索问题过短",
    )

    def __init__(self, conn):
        self.conn = conn
        self.config = conn.config
        self.logger = setup_logging()

        # 创建工具管理器
        self.tool_manager = ToolManager(conn)

        # 创建各类执行器
        self.server_plugin_executor = ServerPluginExecutor(conn)
        self.server_mcp_executor = ServerMCPExecutor(conn)
        self.device_iot_executor = DeviceIoTExecutor(conn)
        self.device_mcp_executor = DeviceMCPExecutor(conn)
        self.mcp_endpoint_executor = MCPEndpointExecutor(conn)

        # 注册执行器
        self.tool_manager.register_executor(
            ToolType.SERVER_PLUGIN, self.server_plugin_executor
        )
        self.tool_manager.register_executor(
            ToolType.SERVER_MCP, self.server_mcp_executor
        )
        self.tool_manager.register_executor(
            ToolType.DEVICE_IOT, self.device_iot_executor
        )
        self.tool_manager.register_executor(
            ToolType.DEVICE_MCP, self.device_mcp_executor
        )
        self.tool_manager.register_executor(
            ToolType.MCP_ENDPOINT, self.mcp_endpoint_executor
        )

        # 初始化标志
        self.finish_init = False
        self._pending_web_search_question: Optional[str] = None
        self._web_search_blocked_turn_id: Optional[str] = None
        self._rag_result_turn_id: Optional[str] = None
        self._rag_result: Optional[ActionResponse] = None

    async def _initialize(self):
        """异步初始化"""
        try:
            # 自动导入插件模块
            auto_import_modules("plugins_func.functions")

            # 初始化服务端MCP
            await self.server_mcp_executor.initialize()

            # 初始化MCP接入点
            await self._initialize_mcp_endpoint()

            # 初始化Home Assistant（如果需要）
            self._initialize_home_assistant()

            self.finish_init = True
            self.logger.debug("统一工具处理器初始化完成")

            # 输出当前支持的所有工具列表
            self.current_support_functions()

        except Exception as e:
            self.logger.error(f"统一工具处理器初始化失败: {e}")

    async def _initialize_mcp_endpoint(self):
        """初始化MCP接入点"""
        try:
            from .mcp_endpoint import connect_mcp_endpoint

            # 从配置中获取MCP接入点URL
            mcp_endpoint_url = self.config.get("mcp_endpoint", "")

            if (
                mcp_endpoint_url
                and "你的" not in mcp_endpoint_url
                and mcp_endpoint_url != "null"
            ):
                self.logger.info(f"正在初始化MCP接入点: {mcp_endpoint_url}")
                mcp_endpoint_client = await connect_mcp_endpoint(
                    mcp_endpoint_url, self.conn
                )

                if mcp_endpoint_client:
                    # 将MCP接入点客户端保存到连接对象中
                    self.conn.mcp_endpoint_client = mcp_endpoint_client
                    self.logger.info("MCP接入点初始化成功")
                else:
                    self.logger.warning("MCP接入点初始化失败")

        except Exception as e:
            self.logger.error(f"初始化MCP接入点失败: {e}")

    def _initialize_home_assistant(self):
        """初始化Home Assistant提示词"""
        try:
            from plugins_func.functions.hass_init import append_devices_to_prompt

            append_devices_to_prompt(self.conn)
        except ImportError:
            pass  # 忽略导入错误
        except Exception as e:
            self.logger.error(f"初始化Home Assistant失败: {e}")

    def get_functions(self) -> List[Dict[str, Any]]:
        """获取所有工具的函数描述"""
        functions = self.tool_manager.get_function_descriptions()
        if not self._rag_first_policy_enabled():
            return functions

        routed_functions = deepcopy(functions)
        for tool in routed_functions:
            function = tool.get("function", {})
            name = function.get("name")
            description = str(function.get("description") or "")
            if name == self._RAG_TOOL_NAME:
                function["description"] = (
                    "四郎的首选检索工具。凡涉及商品、品牌、企业、展会、行业资料、"
                    "专业知识或自有语料，必须先调用本工具；不得与联网搜索并行调用。"
                    + description
                )
            elif name in self._WEB_SEARCH_TOOL_NAMES:
                function["description"] = (
                    "受用户授权约束：只有内部RAG不足、模型自身也无法可靠回答，且已先"
                    "询问用户并得到明确联网同意后才能调用。不得主动或并行调用。"
                    + description
                )
        return routed_functions

    def _rag_first_policy_enabled(self) -> bool:
        role = self.config.get("role", {}) if isinstance(self.config, dict) else {}
        return isinstance(role, dict) and role.get("id") == self._RAG_FIRST_ROLE_ID

    def _recent_conversation(self):
        dialogue = getattr(getattr(self.conn, "dialogue", None), "dialogue", [])
        return dialogue if isinstance(dialogue, list) else []

    def _last_user_turn(self):
        return next(
            (message for message in reversed(self._recent_conversation()) if message.role == "user"),
            None,
        )

    def _previous_assistant_text(self, last_user) -> str:
        if last_user is None:
            return ""
        messages = self._recent_conversation()
        try:
            user_index = messages.index(last_user)
        except ValueError:
            return ""
        return next(
            (
                str(message.content or "")
                for message in reversed(messages[:user_index])
                if message.role == "assistant" and message.content
            ),
            "",
        )

    def _web_search_authorized(self, user_text: str, previous_assistant: str) -> bool:
        normalized = " ".join(user_text.split())
        if any(phrase in normalized for phrase in self._WEB_NEGATION_PHRASES):
            return False
        if any(phrase in normalized for phrase in self._WEB_AUTHORIZATION_PHRASES):
            return True
        consent_was_requested = (
            any(term in previous_assistant for term in ("联网", "互联网", "网上"))
            and any(
                term in previous_assistant
                for term in ("是否", "要不要", "需要我", "允许", "可以")
            )
        )
        return consent_was_requested and normalized in self._AFFIRMATIVE_REPLIES

    @classmethod
    def _rag_result_is_insufficient(cls, result: ActionResponse) -> bool:
        if result.action in (Action.ERROR, Action.NOTFOUND):
            return True
        text = str(result.result or result.response or "")
        return not text or any(marker in text for marker in cls._RAG_INSUFFICIENT_MARKERS)

    async def _execute_tool_with_search_policy(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> ActionResponse:
        if not self._rag_first_policy_enabled():
            return await self.tool_manager.execute_tool(tool_name, arguments)

        last_user = self._last_user_turn()
        user_text = str(getattr(last_user, "content", "") or "")
        turn_id = str(getattr(last_user, "uniq_id", "") or "")
        if tool_name == self._RAG_TOOL_NAME:
            result = await self.tool_manager.execute_tool(tool_name, arguments)
            self._rag_result_turn_id = turn_id
            self._rag_result = result
            return result
        if tool_name not in self._WEB_SEARCH_TOOL_NAMES:
            return await self.tool_manager.execute_tool(tool_name, arguments)

        previous_assistant = self._previous_assistant_text(last_user)
        authorized = self._web_search_authorized(user_text, previous_assistant)

        if authorized and self._pending_web_search_question:
            self._pending_web_search_question = None
            self._web_search_blocked_turn_id = None
            return await self.tool_manager.execute_tool(tool_name, arguments)

        if turn_id and self._rag_result_turn_id == turn_id and self._rag_result:
            rag_result = self._rag_result
        else:
            rag_result = await self.tool_manager.execute_tool(
                self._RAG_TOOL_NAME,
                {"question": user_text},
            )
            self._rag_result_turn_id = turn_id
            self._rag_result = rag_result
        if not self._rag_result_is_insufficient(rag_result):
            self._pending_web_search_question = None
            self._web_search_blocked_turn_id = None
            return rag_result

        if authorized:
            return await self.tool_manager.execute_tool(tool_name, arguments)

        self._pending_web_search_question = user_text
        if turn_id and self._web_search_blocked_turn_id == turn_id:
            return ActionResponse(
                action=Action.RESPONSE,
                response="内部资料暂时没有找到可靠答案。需要我再联网查询吗？",
            )
        self._web_search_blocked_turn_id = turn_id
        rag_context = str(rag_result.result or rag_result.response or "")
        return ActionResponse(
            action=Action.REQLLM,
            result=(
                rag_context
                + "\n【联网规则】当前未获得联网授权。若你凭已有知识也无法可靠回答，"
                "只询问用户是否允许联网查询，不得调用联网搜索。"
            ),
        )

    def current_support_functions(self) -> List[str]:
        """获取当前支持的函数名称列表"""
        func_names = self.tool_manager.get_supported_tool_names()
        self.logger.info(f"当前支持的函数列表: {func_names}")
        return func_names

    def upload_functions_desc(self):
        """刷新函数描述列表"""
        self.tool_manager.refresh_tools()
        self.logger.info("函数描述列表已刷新")

    def has_tool(self, tool_name: str) -> bool:
        """检查是否有指定工具"""
        return self.tool_manager.has_tool(tool_name)

    async def handle_llm_function_call(
        self, conn, function_call_data: Dict[str, Any]
    ) -> Optional[ActionResponse]:
        """处理LLM函数调用"""
        try:
            # 处理多函数调用
            if "function_calls" in function_call_data:
                responses = []
                for call in function_call_data["function_calls"]:
                    result = await self._execute_tool_with_search_policy(
                        call["name"], call.get("arguments", {})
                    )
                    responses.append(result)
                return self._combine_responses(responses)

            # 处理单函数调用
            function_name = function_call_data["name"]
            arguments = function_call_data.get("arguments", {})

            # 如果arguments是字符串，尝试解析为JSON
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments) if arguments else {}
                except json.JSONDecodeError:
                    self.logger.error(f"无法解析函数参数: {arguments}")
                    return ActionResponse(
                        action=Action.ERROR,
                        response="无法解析函数参数",
                    )

            self.logger.debug(f"调用函数: {function_name}, 参数: {arguments}")

            # 发送工具调用显示消息到设备
            try:
                await send_display_message(self.conn, f"% {function_name}")
            except Exception as e:
                self.logger.warning(f"发送工具调用显示消息失败: {e}")

            # 执行工具调用
            result = await self._execute_tool_with_search_policy(
                function_name, arguments
            )
            return result

        except Exception as e:
            self.logger.error(f"处理function call错误: {e}")
            return ActionResponse(action=Action.ERROR, response=str(e))

    def _combine_responses(self, responses: List[ActionResponse]) -> ActionResponse:
        """合并多个函数调用的响应"""
        if not responses:
            return ActionResponse(action=Action.NONE, response="无响应")

        # 如果有任何错误，返回第一个错误
        for response in responses:
            if response.action == Action.ERROR:
                return response

        # 合并所有成功的响应
        contents = []
        responses_text = []

        for response in responses:
            if response.content:
                contents.append(response.content)
            if response.response:
                responses_text.append(response.response)

        # 确定最终的动作类型
        final_action = Action.RESPONSE
        for response in responses:
            if response.action == Action.REQLLM:
                final_action = Action.REQLLM
                break

        return ActionResponse(
            action=final_action,
            result="; ".join(contents) if contents else None,
            response="; ".join(responses_text) if responses_text else None,
        )

    async def register_iot_tools(self, descriptors: List[Dict[str, Any]]):
        """注册IoT设备工具"""
        self.device_iot_executor.register_iot_tools(descriptors)
        self.tool_manager.refresh_tools()
        self.logger.info(f"注册了{len(descriptors)}个IoT设备的工具")

    def get_tool_statistics(self) -> Dict[str, int]:
        """获取工具统计信息"""
        return self.tool_manager.get_tool_statistics()

    async def cleanup(self):
        """清理资源"""
        try:
            try:
                from plugins_func.functions.retrieve_from_cyjdata import (
                    close_retrieval_runtime_client,
                )

                await close_retrieval_runtime_client(self.conn)
            except ImportError:
                pass
            except Exception:
                self.logger.warning("清理检索客户端失败")

            await self.server_mcp_executor.cleanup()

            # 清理MCP接入点连接
            if (
                hasattr(self.conn, "mcp_endpoint_client")
                and self.conn.mcp_endpoint_client
            ):
                await self.conn.mcp_endpoint_client.close()

            self.logger.info("工具处理器清理完成")
        except Exception as e:
            self.logger.error(f"工具处理器清理失败: {e}")
