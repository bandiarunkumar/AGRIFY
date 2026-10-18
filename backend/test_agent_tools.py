"""Regression tests for agent tool timeout isolation."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from agent import tools


class TestToolTimeoutHandling(unittest.TestCase):
    def test_timed_out_wave_returns_unavailable_without_context_manager_wait(self):
        plan = SimpleNamespace(required_tools=["tool_weather"], entities={})

        def slow_tool(_entities, _previous):
            import time
            time.sleep(0.05)
            return tools.ToolResult("tool_weather", {"ok": True}, "live", None, 50)

        with patch.dict(tools.TOOL_FN_MAP, {"tool_weather": slow_tool}), \
             patch.object(tools, "as_completed", side_effect=tools.FutureTimeoutError):
            results = tools.execute_tools(plan)

        self.assertEqual(results["tool_weather"].trust_level, "unavailable")
        self.assertIn("response time budget", results["tool_weather"].error)


if __name__ == "__main__":
    unittest.main(verbosity=2)
