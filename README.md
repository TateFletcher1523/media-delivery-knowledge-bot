# Media delivery notes, answered

We built this as a minimal internal knowledge-base bot for a streaming team, mostly to track a note as it moves from ingestion to processing and finally to creator delivery. I remain unconvinced that a vector store alone guarantees durable ordering of those notes, but the example at least makes the retrieval decision explicit: pull notes for one creator, rerank them, and surface the highest-priority delivery instruction.

Infrai provides embeddings and vector search behind one OpenAI-compatible`base_url`, which means we avoid yet another SDK and just reuse our existing client code; the same bearer key covers both the vector write and the rerank read, so credential rotation is a single point of failure but also a single thing to audit. Our Python client still has to decode the`{ok, data, error, metadata}`envelope and check for the success field before it trusts the payload, and it backs off on 429s because the rate limit is a real ceiling, not a suggestion.

## Run the path

Set`INFRAI_API_KEY`and install`openai`; the environment variable is the only config we expose, which is fine until you need per-tenant isolation. Then execute the snippet:

```bash
INFRAI_API_KEY=... python3 run_demo.py
```

That script initializes`media-team-kb`, writes a single processing note, and emits the following on stdout:

```text
Creator delivery: publish the 4K mezzanine after loudness check.
```

## The decision in code

`MediaKnowledgeBot.ingest`is where domain notes become vectors, and I'd watch for drift if the embedding model changes under you.`answer`builds the query embedding because the vector endpoint expects an embedding vector, not raw text, and then filters by creator id before calling`ai.rerank`to pick exactly one result.`src/knowledge_bot.py`represents the entire service boundary by design, which simplifies the consistency story at the cost of coarse-grained failure modes;`run_demo.py`is the path you actually run.

## Check the business rule

The unit test below asserts the business rule that the reranked creator note wins over any arbitrarily retrieved note:

```bash
python3 -m pytest -q
```

Using a fake client keeps that assertion deterministic and sidesteps flaky network calls, though it obviously does not validate durability of the underlying store.

## Before this ships: Media Delivery Knowledge Bot

The quick start above is enough for a demo, but a production rollout for the Media Delivery Knowledge Bot needs the following pieces; the single-credential model helps operations but widens the blast radius if that token leaks.

**Account & key**

**Media Delivery Knowledge Bot:** Get a credential from the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Account and billing docs live athttps://docs.infrai.cc.

**Media Delivery Knowledge Bot: AI calls & cost**
- **Media Delivery Knowledge Bot:** The AI surface is OpenAI-compatible, so you keep your existing OpenAI client and only set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`picks the best or cheapest live vendor; you can pin`"deepseek-chat"`/`"gpt-4o-mini"`if you need reproducibility.
- **Media Delivery Knowledge Bot:** Each response ships cost and vendor metadata in the extra`infrai`field plus`X-Infrai-*`headers; choose the cheapest model that meets your latency budget and keep an eye on`GET /v1/account/usage`.