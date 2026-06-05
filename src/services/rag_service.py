from src.services.pdf_service import load_pdf, chunk_text_with_pages


class RagService:
    def __init__(self, embedder, vector_store, llm_client, top_k: int = 5):
        self.embedder = embedder
        self.vector_store = vector_store
        self.llm = llm_client
        self.top_k = top_k

    def ingest(self, pdf_path: str, chunk_size: int, chunk_overlap: int, source_name: str = None) -> int:
        pages = load_pdf(pdf_path)
        chunk_data = chunk_text_with_pages(pages, chunk_size, chunk_overlap)
        if not chunk_data:
            return 0

        chunks = [c[0] for c in chunk_data]
        page_nums = [c[1] for c in chunk_data]

        source = source_name or pdf_path
        metadatas = [
            {"source": source, "chunk_index": i, "page": page_nums[i]} for i in range(len(chunks))
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
            f"[Source: {r['metadata']['source']}, Page {r['metadata'].get('page', '?')}, Chunk {r['metadata']['chunk_index']}]\n{r['document']}"
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
            {
                "source": r["metadata"]["source"],
                "chunk_index": r["metadata"]["chunk_index"],
                "page": r["metadata"].get("page"),
            }
            for r in results
        ]
        return {"answer": answer, "sources": sources}
