import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from core.providers.tools.unified_tool_handler import UnifiedToolHandler
from plugins_func.register import Action, ActionResponse


def message(role, content, uniq_id=None):
    return SimpleNamespace(role=role, content=content, uniq_id=uniq_id)


class RagFirstWebPolicyTest(unittest.IsolatedAsyncioTestCase):
    def handler(self, messages, role_id="pet_expert_shilang"):
        conn = SimpleNamespace(
            config={"role": {"id": role_id}},
            dialogue=SimpleNamespace(dialogue=messages),
        )
        handler = object.__new__(UnifiedToolHandler)
        handler.conn = conn
        handler.config = conn.config
        handler.tool_manager = SimpleNamespace(execute_tool=AsyncMock())
        handler._pending_web_search_question = None
        handler._web_search_blocked_turn_id = None
        handler._rag_result_turn_id = None
        handler._rag_result = None
        return handler

    async def test_web_attempt_is_replaced_by_rag_when_rag_has_answer(self):
        handler = self.handler([message("user", "介绍一下鲜朗", "turn-1")])
        handler.tool_manager.execute_tool.return_value = ActionResponse(
            Action.REQLLM, "【内部检索问题】介绍一下鲜朗\n1. [brand] 鲜朗"
        )

        result = await handler._execute_tool_with_search_policy(
            "bailian_web_search", {"query": "鲜朗"}
        )

        self.assertIn("鲜朗", result.result)
        handler.tool_manager.execute_tool.assert_awaited_once_with(
            "retrieve_from_cyjdata", {"question": "介绍一下鲜朗"}
        )

    async def test_insufficient_rag_requires_consent_before_web(self):
        handler = self.handler([message("user", "亚宠展有哪些工厂", "turn-2")])
        handler.tool_manager.execute_tool.return_value = ActionResponse(
            Action.REQLLM, "【检索结果】没有找到足够可靠的资料。"
        )

        first = await handler._execute_tool_with_search_policy(
            "bailian_web_search", {"query": "亚宠展 工厂"}
        )
        second = await handler._execute_tool_with_search_policy(
            "bailian_web_search", {"query": "亚宠展 工厂"}
        )

        self.assertEqual(Action.REQLLM, first.action)
        self.assertIn("当前未获得联网授权", first.result)
        self.assertEqual(Action.RESPONSE, second.action)
        self.assertIn("需要我再联网查询吗", second.response)
        self.assertEqual(1, handler.tool_manager.execute_tool.await_count)

    async def test_affirmative_reply_after_consent_question_allows_web(self):
        handler = self.handler(
            [
                message("user", "亚宠展有哪些工厂", "turn-1"),
                message("assistant", "内部资料不足，需要我再联网查询吗？"),
                message("user", "可以", "turn-2"),
            ]
        )
        handler._pending_web_search_question = "亚宠展有哪些工厂"
        handler.tool_manager.execute_tool.return_value = ActionResponse(
            Action.REQLLM, "web result"
        )

        result = await handler._execute_tool_with_search_policy(
            "bailian_web_search", {"query": "亚宠展 工厂"}
        )

        self.assertEqual("web result", result.result)
        handler.tool_manager.execute_tool.assert_awaited_once_with(
            "bailian_web_search", {"query": "亚宠展 工厂"}
        )

    async def test_explicit_web_request_still_checks_rag_first(self):
        handler = self.handler([message("user", "请联网查一下鲜朗", "turn-3")])
        handler.tool_manager.execute_tool.return_value = ActionResponse(
            Action.REQLLM, "【内部检索问题】请联网查一下鲜朗\n1. [brand] 鲜朗"
        )

        await handler._execute_tool_with_search_policy(
            "bailian_web_search", {"query": "鲜朗"}
        )

        handler.tool_manager.execute_tool.assert_awaited_once_with(
            "retrieve_from_cyjdata", {"question": "请联网查一下鲜朗"}
        )

    async def test_explicit_web_negation_cannot_authorize_search(self):
        handler = self.handler([message("user", "不要联网，查一下亚宠展", "turn-4")])
        handler.tool_manager.execute_tool.return_value = ActionResponse(
            Action.REQLLM, "【检索结论】现有资料不足以可靠回答。"
        )

        result = await handler._execute_tool_with_search_policy(
            "bailian_web_search", {"query": "亚宠展"}
        )

        self.assertEqual(Action.REQLLM, result.action)
        handler.tool_manager.execute_tool.assert_awaited_once_with(
            "retrieve_from_cyjdata", {"question": "不要联网，查一下亚宠展"}
        )

    def test_tool_descriptions_are_routed_without_mutating_registry(self):
        handler = self.handler([])
        registry = [
            {
                "type": "function",
                "function": {
                    "name": "retrieve_from_cyjdata",
                    "description": "RAG",
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "bailian_web_search",
                    "description": "WEB",
                },
            },
        ]
        handler.tool_manager.get_function_descriptions = lambda: registry

        routed = handler.get_functions()

        self.assertIn("必须先调用", routed[0]["function"]["description"])
        self.assertIn("明确联网同意", routed[1]["function"]["description"])
        self.assertEqual("RAG", registry[0]["function"]["description"])
        self.assertEqual("WEB", registry[1]["function"]["description"])

    async def test_other_roles_keep_existing_web_behavior(self):
        handler = self.handler(
            [message("user", "查一下新闻", "turn-5")], role_id="cheese_cat"
        )
        handler.tool_manager.execute_tool.return_value = ActionResponse(
            Action.REQLLM, "web result"
        )

        await handler._execute_tool_with_search_policy(
            "bailian_web_search", {"query": "新闻"}
        )

        handler.tool_manager.execute_tool.assert_awaited_once_with(
            "bailian_web_search", {"query": "新闻"}
        )


if __name__ == "__main__":
    unittest.main()
