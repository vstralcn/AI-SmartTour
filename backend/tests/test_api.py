import unittest

from fastapi.testclient import TestClient

from app.main import app


class APITest(unittest.TestCase):
    def setUp(self) -> None:
        self.client_context = TestClient(app)
        self.client = self.client_context.__enter__()

    def tearDown(self) -> None:
        self.client_context.__exit__(None, None, None)

    def test_health_exposes_runtime_mode(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["agent_mode"], "single-orchestrator")
        self.assertGreater(response.json()["knowledge_documents"], 0)

    def test_websocket_returns_agent_trace_and_grounded_answer(self) -> None:
        session = self.client.post(
            "/api/v1/sessions",
            json={"interests": ["历史文化"]},
        ).json()

        with self.client.websocket_connect(
            f"/api/v1/chat/stream?session_id={session['session_id']}"
        ) as websocket:
            websocket.send_json(
                {
                    "type": "text",
                    "content": "景区几点开门？",
                    "session_id": session["session_id"],
                }
            )
            messages = []
            while True:
                message = websocket.receive_json()
                messages.append(message)
                if message["type"] == "text_chunk" and message["done"]:
                    break

        message_types = [message["type"] for message in messages]
        answer = "".join(
            message["content"]
            for message in messages
            if message["type"] == "text_chunk" and not message["done"]
        )
        self.assertIn("agent_step", message_types)
        self.assertIn("sources", message_types)
        self.assertIn("8:00-18:00", answer)

    def test_persistent_product_loop_apis(self) -> None:
        avatar = self.client.get("/api/v1/avatar/active")
        self.assertEqual(avatar.status_code, 200)
        self.assertTrue(avatar.json()["is_active"])

        uploaded = self.client.post(
            "/api/v1/admin/knowledge/upload",
            data={"category": "景点信息"},
            files={
                "file": (
                    "cloud-whale.txt",
                    "云鲸塔每天09:30开放，17:00停止入场。",
                    "text/plain",
                )
            },
        )
        self.assertEqual(uploaded.status_code, 200)
        doc_id = uploaded.json()["id"]

        knowledge_test = self.client.post(
            "/api/v1/admin/knowledge/test",
            json={"question": "云鲸塔几点开放？"},
        )
        self.assertEqual(knowledge_test.status_code, 200)
        self.assertIn("09:30", knowledge_test.json()["answer"])

        session = self.client.post(
            "/api/v1/sessions",
            json={
                "interests": ["历史文化"],
                "companions": ["儿童", "老人"],
                "mobility": "低强度",
                "visit_duration": 3,
            },
        )
        self.assertIn(avatar.json()["name"], session.json()["greeting"])
        route = self.client.post(
            "/api/v1/recommend/route",
            json={
                "session_id": session.json()["session_id"],
                "duration_hours": 3,
                "interests": ["历史文化"],
                "companions": ["儿童", "老人"],
                "mobility": "低强度",
            },
        )
        self.assertEqual(route.status_code, 200)
        self.assertIn("低强度", route.json()["description"])

        dashboard = self.client.get("/api/v1/admin/analytics/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(dashboard.json()["data_source"], "live")
        self.assertGreaterEqual(dashboard.json()["total_sessions"], 1)
        self.assertTrue(dashboard.json()["route_preferences"])

        deleted = self.client.delete(f"/api/v1/admin/knowledge/{doc_id}")
        self.assertEqual(deleted.status_code, 200)


if __name__ == "__main__":
    unittest.main()
