import uuid

import chromadb
from chromadb.config import Settings


class VectorRepository:
    def __init__(self, persist_dir: str, collection_name: str = "documents"):
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection_name = collection_name
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_documents(
        self,
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> list[str]:
        ids = [str(uuid.uuid4()) for _ in texts]
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids,
        )
        return ids

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )
        hits = []
        for i in range(len(results["ids"][0])):
            hits.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else None,
            })
        return hits

    def count(self) -> int:
        return self.collection.count()

    def clear(self):
        self.client.delete_collection(self._collection_name)
        self.collection = self.client.get_or_create_collection(name=self._collection_name)

    def delete_by_source(self, source: str) -> int:
        results = self.collection.get(where={"source": source})
        ids = results.get("ids", [])
        if ids:
            self.collection.delete(ids=ids)
        return len(ids)

    def list_sources(self) -> dict[str, int]:
        all_data = self.collection.get(include=["metadatas"])
        sources: dict[str, int] = {}
        for meta in all_data.get("metadatas", []):
            src = meta.get("source", "unknown")
            sources[src] = sources.get(src, 0) + 1
        return sources
