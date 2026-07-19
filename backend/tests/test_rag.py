import unittest

from app.core.rag import RAGEngine


class RAGEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.rag = RAGEngine()

    def test_faq_returns_traceable_evidence(self) -> None:
        result = self.rag.retrieve_with_sources("景区几点开门？")

        self.assertTrue(result.found)
        self.assertEqual(result.matched_by, "faq")
        # 置信度根据命中关键词具体度打分，不再一律虚高为 1.0
        self.assertGreaterEqual(result.confidence, self.rag._FAQ_THRESHOLD)
        self.assertLessEqual(result.confidence, 1.0)
        self.assertEqual(result.evidence[0].source, "景区常见问题")

    def test_generic_keyword_does_not_trigger_faq(self) -> None:
        # 仅命中泛词（“时间”）不应误命中“开放时间”FAQ
        result = self.rag.retrieve_with_sources("我没时间了")

        self.assertNotEqual(result.matched_by, "faq")

    def test_keyword_search_returns_ranked_sources(self) -> None:
        result = self.rag.retrieve_with_sources("我想了解古建筑的历史文化")

        self.assertTrue(result.found)
        self.assertEqual(result.matched_by, "keyword")
        self.assertGreaterEqual(
            result.evidence[0].score, result.evidence[-1].score)
        self.assertTrue(result.evidence[0].title)

    def test_bm25_ranks_most_relevant_doc_first(self) -> None:
        # 餐饮相关查询应由 BM25 将“景区餐饮”排在首位
        result = self.rag.retrieve_with_sources("有什么好吃的美食餐厅推荐")

        self.assertTrue(result.found)
        self.assertEqual(result.matched_by, "keyword")
        self.assertEqual(result.evidence[0].title, "景区餐饮")

    def test_unknown_question_returns_no_evidence(self) -> None:
        result = self.rag.retrieve_with_sources("量子芯片怎么设计")

        self.assertFalse(result.found)
        self.assertEqual(result.confidence, 0.0)
        self.assertEqual(result.evidence, [])


if __name__ == "__main__":
    unittest.main()
