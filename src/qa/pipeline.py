from src.ingestion.loader import load_pdf
from src.ingestion.chunker import chunk_text


class RAGPipeline:
    def __init__(self, embedder, vector_store, llm_client, top_k: int = 5):
        self.embedder = embedder
        self.vector_store = vector_store
        self.llm = llm_client
        self.top_k = top_k

    def ingest(self, pdf_path: str, chunk_size: int, chunk_overlap: int) -> int:
        text = load_pdf(pdf_path)
        chunks = chunk_text(text, chunk_size, chunk_overlap)
        if not chunks:
            return 0

        metadatas = [
            {"source": pdf_path, "chunk_index": i} for i in range(len(chunks))
        ]
        embeddings = self.embedder.embed(chunks)
        self.vector_store.add_documents(chunks, embeddings, metadatas)
        return len(chunks)

    def ask(self, question: str) -> dict:
        query_embedding = self.embedder.embed([question])[0]
        results = self.vector_store.search(query_embedding, self.top_k)
        if not results:
            return {"answer": "No relevant documents found.", "sources": []}

        context = "\n\n".join(
            f"[Source: {r['metadata']['source']}, Chunk {r['metadata']['chunk_index']}]\n{r['document']}"
            for r in results
        )

        system_prompt = (
            "You are a precise research assistant. Answer the question based solely on the provided context. "
            "If the context doesn't contain enough information, say so. "
            "Always reference the source documents in your answer."
        )
        user_prompt = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"

        try:
            answer = self.llm.generate(user_prompt, system=system_prompt)
        except RuntimeError as exc:
            return {"answer": f"LLM error: {exc}", "sources": []}

        sources = [
            {"source": r["metadata"]["source"], "chunk_index": r["metadata"]["chunk_index"]}
            for r in results
        ]
        return {"answer": answer, "sources": sources}
