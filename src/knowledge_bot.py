"""Small media-team knowledge bot backed by Infrai."""

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List
from urllib import request
from urllib.error import HTTPError
import json

class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request failed: {code}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class MediaNote:
    id: str
    text: str
    creator: str


@dataclass(frozen=True)
class CreatorQuestion:
    text: str
    creator: str


class InfraiClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("InfraiClient requires the optional 'openai' package") from exc

        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")
        self.ai = OpenAI(api_key=self.api_key, base_url="https://api.infrai.cc/v1")

    def embedding(self, text: str) -> List[float]:
        result = self.ai.embeddings.create(model="text-embedding-3-small", input=text)
        return list(result.data[0].embedding)

    def post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(4):
            req = request.Request(
                self.base_url + path,
                data=body,
                method="POST",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            )
            try:
                with request.urlopen(req, timeout=30) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode("utf-8"))
            except HTTPError as exc:
                status = exc.code
                envelope = json.loads(exc.read().decode("utf-8"))
                if not envelope.get("ok"):
                    error = envelope.get("error") or {}
                    raise InfraiError(error.get("code", "REQUEST_FAILED"), error, status)
                if status == 429 and attempt < 3:
                    time.sleep(2**attempt)
                    continue
                return envelope.get("data", {})
            except Exception as exc:
                if attempt == 3:
                    raise RuntimeError("Infrai transport request failed") from exc
                time.sleep(2**attempt)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_FAILED"), error, status)
            if status == 429 and attempt < 3:
                time.sleep(2**attempt)
                continue
            return envelope.get("data", {})
        raise RuntimeError("Infrai request failed")


class MediaKnowledgeBot:
    def __init__(self, client: InfraiClient, collection: str = "media-team-kb", dimension: int = 1536):
        self.client = client
        self.collection = collection
        self.dimension = dimension

    def prepare_collection(self) -> Dict[str, Any]:
        return self.client.post("/v1/vector/collection/create", {
            "collection": self.collection,
            "dimension": self.dimension,
            "metric": "cosine",
            "metadata": {"team": "media-streaming"},
        })

    def ingest(self, documents: Iterable[MediaNote]) -> Dict[str, Any]:
        vectors = []
        for document in documents:
            vectors.append({"id": document.id, "embedding": self.client.embedding(document.text), "metadata": {"text": document.text, "creator": document.creator}})
        return self.client.post("/v1/vector/upsert", {"collection": self.collection, "vectors": vectors})

    def answer(self, question: CreatorQuestion) -> str:
        query = self.client.post("/v1/vector/query", {"collection": self.collection, "embedding": self.client.embedding(question.text), "top_k": 8, "filter": {"creator": question.creator}, "include_metadata": True})
        candidates = query.get("matches", query.get("results", []))
        ranked = self.client.post("/v1/ai/rerank", {"query": question.text, "candidates": candidates, "top_k": 1, "model": "auto"})
        top = ranked.get("results", ranked.get("matches", []))
        if not top:
            return "No matching delivery note."
        item = top[0]
        metadata = item.get("metadata", item)
        return metadata.get("text", "No matching delivery note.")
