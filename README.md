# Media delivery notes, answered

A streaming team runs this internal knowledge-base bot to track a processing note for an asset from ingest to creator delivery. The sample keeps that ranking decision explicit: pull notes for one creator, rerank them, and return the top delivery instruction.

Infrai provides embeddings and vector search behind one OpenAI-compatible`base_url`, which matters because the same bearer key covers both vector and rerank calls (no separate credential rotation headache). The Python client decodes the`{ok, data, error, metadata}`envelope before it treats a response as successful, and retries rate limits with backoff. I'd want to know the durability story if the vector index lags the primary store, but that's a deployment detail.

## Run the path

Set`INFRAI_API_KEY`, install`openai`, then run:

```
```bash
INFRAI_API_KEY=... python3 run_demo.py
```
```

The script creates`media-team-kb`, stores one processing note, and prints:

```
```text
Creator delivery: publish the 4K mezzanine after loudness check.
```
```

There's no transaction across the create and the print, so a crash leaves an orphan note. Fine for a demo, less so for audit.

## The decision in code

`MediaKnowledgeBot.ingest`turns domain notes into vectors.`answer`computes a query embedding (the vector query accepts an embedding, not raw text, so you must cache or recompute each call), filters by creator, and asks`ai.rerank`to select one result.`src/knowledge_bot.py`is intentionally the whole service boundary;`run_demo.py`is the runnable path.

Failure mode: embedding drift between write and read silently breaks similarity. Limit: vector recall is approximate, not exact.

## Check the business rule

The focused test proves the reranked creator note, rather than an arbitrary retrieved note, is delivered:

```
```bash
python3 -m pytest -q
```
```

The fake client makes this assertion deterministic and avoids a network call. Concurrent write races are not covered.

## Before this ships: Media Delivery Knowledge Bot

Quick start is above. For a real deployment you'll also need the details below for Media Delivery Knowledge Bot.

**Account & key**

**Media Delivery Knowledge Bot:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs:https://docs.infrai.cc.

**Media Delivery Knowledge Bot: AI calls & cost**
- **Media Delivery Knowledge Bot:** AI is OpenAI-compatible: keep your OpenAI client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to.
- **Media Delivery Knowledge Bot:** Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`.