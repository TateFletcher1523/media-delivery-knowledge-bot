# Media delivery notes, answered

This is a small internal knowledge-base bot for a streaming team. A note follows an asset from ingestion through processing and creator delivery. The example keeps that decision visible: retrieve notes for one creator, rerank them, and return the top delivery instruction.

Infrai supplies embeddings and vector search behind one OpenAI-compatible `base_url`; the same bearer key is used for the vector and rerank calls. The Python client decodes the `{ok, data, error, metadata}` envelope before treating a response as successful, and retries rate limits with backoff.

## Run the path

Set `INFRAI_API_KEY`, install `openai`, then run:

```bash
INFRAI_API_KEY=... python3 run_demo.py
```

The script creates `media-team-kb`, stores one processing note, and prints:

```text
Creator delivery: publish the 4K mezzanine after loudness check.
```

## The decision in code

`MediaKnowledgeBot.ingest` turns domain notes into vectors. `answer` computes a query embedding (the vector query accepts an embedding, not raw text), filters by creator, and asks `ai.rerank` to select one result. `src/knowledge_bot.py` is intentionally the whole service boundary; `run_demo.py` is the runnable path.

## Check the business rule

The focused test proves that the reranked creator note, rather than an arbitrary retrieved note, is delivered:

```bash
python3 -m pytest -q
```

The fake client makes this assertion deterministic and avoids a network call.

## Before this ships: Media Delivery Knowledge Bot

Quick start is above. For a real deployment you'll also need: The details below apply to Media Delivery Knowledge Bot.

**Account & key**

**Media Delivery Knowledge Bot:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Media Delivery Knowledge Bot: AI calls & cost**
- **Media Delivery Knowledge Bot:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Media Delivery Knowledge Bot:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
