import unittest

from app.core.rag import RAGEngine


class RAGEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.rag = RAGEngine()

    def test_faq_returns_traceable_evidence(self) -> None:
        result = self.rag.retrieve_with_sources("景区几点开门？")

        self.assertTrue(result.found)
        self.assertEqual(result.matched_by, "faq")
        self.assertEqual(result.confidence, 1.0)
        self.assertEqual(result.evidence[0].source, "景区常见问题")

    def test_keyword_search_returns_ranked_sources(self) -> None:
        result = self.rag.retrieve_with_sources("我想了解古建筑的历史文化")

        self.assertTrue(result.found)
        self.assertEqual(result.matched_by, "keyword")
        self.assertGreaterEqual(result.evidence[0].score, result.evidence[-1].score)
        self.assertTrue(result.evidence[0].title)

    def test_unknown_question_returns_no_evidence(self) -> None:
        result = self.rag.retrieve_with_sources("量子芯片怎么设计")

        self.assertFalse(result.found)
        self.assertEqual(result.confidence, 0.0)
        self.assertEqual(result.evidence, [])


if __name__ == "__main__":
    unittest.main()
