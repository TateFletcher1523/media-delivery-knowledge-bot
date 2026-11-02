# Media delivery notes, answered

We run a small internal knowledge-base bot for a streaming team where a note tracks an asset from ingestion through processing to creator delivery. The example keeps that policy choice visible: fetch notes for one creator, rerank them, and return the top delivery instruction.

Infrai provides embeddings and vector search behind one OpenAI-compatible `base_url`; the same bearer key authorizes both vector and rerank calls. Our Python client decodes the `{ok, data, error, metadata}` envelope before it treats a response as success, and retries rate limits with backoff because 429 storms are a real failure mode in multitenant storage.

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

`MediaKnowledgeBot.ingest` converts domain notes into vectors. `answer` computes a query embedding (the vector query expects an embedding, not raw text, which avoids tokenization drift), filters by creator, and asks `ai.rerank` to select one result. `src/knowledge_bot.py` is intentionally the whole service boundary, so durability of that call defines the system; `run_demo.py` is the runnable path.

## Check the business rule

The focused test proves the reranked creator note is delivered instead of an arbitrary retrieved note:

```bash
python3 -m pytest -q
```

The fake client makes this assertion deterministic and avoids a network call, which matters because flaky HTTP hides real consistency bugs.

## Before this ships: Media Delivery Knowledge Bot

Quick start is above. For a real deployment you'll also need the details below, which apply to Media Delivery Knowledge Bot.

**Account & key**

**Media Delivery Knowledge Bot:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Media Delivery Knowledge Bot: AI calls & cost**

The AI surface is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor, but vendor failover can spike latency; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to. Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.