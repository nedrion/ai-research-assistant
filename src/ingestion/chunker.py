def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    paragraphs = text.split("\n\n")
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    if not paragraphs:
        return []

    chunks = []
    current = ""

    for para in paragraphs:
        if not current or len(current) + len(para) + 2 <= chunk_size:
            current += ("\n\n" + para) if current else para
        else:
            chunks.append(current.strip())
            overlap_start = max(0, len(current) - chunk_overlap)
            current = current[overlap_start:] + "\n\n" + para

    if current.strip():
        chunks.append(current.strip())

    return chunks
