import unittest

from fastapi.testclient import TestClient

from app.main import app


class APITest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

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


if __name__ == "__main__":
    unittest.main()
