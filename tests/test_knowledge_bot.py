from src.knowledge_bot import CreatorQuestion, MediaKnowledgeBot


class FakeClient:
    def embedding(self, text):
        return [1.0, 0.0]

    def post(self, path, payload):
        if path.endswith("/query"):
            return {"matches": [{"id": "old", "metadata": {"text": "old note"}}, {"id": "new", "metadata": {"text": "send after loudness check"}}]}
        if path.endswith("/rerank"):
            return {"results": [{"metadata": {"text": "send after loudness check"}}]}
        return {}


def test_answer_delivers_top_ranked_creator_note():
    bot = MediaKnowledgeBot(FakeClient())
    assert bot.answer(CreatorQuestion("delivery timing", "ava")) == "send after loudness check"
