import os

from src.knowledge_bot import CreatorQuestion, InfraiClient, MediaKnowledgeBot, MediaNote


def main() -> None:
    bot = MediaKnowledgeBot(InfraiClient())
    bot.prepare_collection()
    bot.ingest([MediaNote("job-42", "Creator delivery: publish the 4K mezzanine after loudness check.", "ava")])
    print(bot.answer(CreatorQuestion("When can Ava receive the 4K file?", "ava")))


if __name__ == "__main__":
    main()
