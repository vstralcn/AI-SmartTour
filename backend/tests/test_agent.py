import unittest

from app.core.agent import GuideAgent
from app.core.rag import RAGEngine


class GuideAgentTest(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = GuideAgent(RAGEngine())
        self.agent.create_profile("session-1", ["历史文化"])

    def test_route_request_calls_profile_and_route_tools(self) -> None:
        execution = self.agent.execute(
            "session-1",
            "带孩子游玩3小时，想看古建筑，请规划路线",
        )

        self.assertEqual(execution.intent, "route_planning")
        self.assertIn("规划依据", execution.direct_response)
        self.assertEqual([step.tool for step in execution.steps], ["profile", "route"])
        self.assertIn(
            "亲子游玩",
            self.agent.user_profiles["session-1"]["interests"],
        )
        self.assertIn("古建筑群", execution.route_spots)
        self.assertIn("文化体验馆", execution.route_spots)

    def test_unknown_knowledge_is_refused(self) -> None:
        execution = self.agent.execute("session-1", "请介绍量子芯片设计")

        self.assertEqual(execution.intent, "knowledge_query")
        self.assertEqual(execution.confidence, 0.0)
        self.assertIn("没有足够依据", execution.direct_response)
        self.assertEqual(execution.steps[0].status, "no_result")

    def test_feedback_is_recorded_with_tracking_id(self) -> None:
        execution = self.agent.execute("session-1", "我要反馈：卫生间指引不清楚")

        self.assertEqual(execution.intent, "feedback")
        self.assertIn("FB-", execution.direct_response)
        self.assertEqual(len(self.agent.feedback_records), 1)

    def test_follow_up_reference_uses_last_scenic_spot(self) -> None:
        self.agent.execute("session-1", "介绍一下古建筑群")
        execution = self.agent.execute("session-1", "这个景点有什么历史？")

        self.assertTrue(execution.evidence)
        self.assertEqual(execution.evidence[0].title, "古建筑群")


if __name__ == "__main__":
    unittest.main()
