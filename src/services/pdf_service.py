import fitz


def load_pdf(filepath: str) -> list[tuple[int, str]]:
    doc = fitz.open(filepath)
    pages: list[tuple[int, str]] = []
    for page_num, page in enumerate(doc, 1):
        text = page.get_text().strip()
        if text:
            pages.append((page_num, text))
    doc.close()
    return pages


def chunk_text_with_pages(
    pages: list[tuple[int, str]], chunk_size: int = 500, chunk_overlap: int = 50
) -> list[tuple[str, int]]:
    paragraphs: list[tuple[str, int]] = []
    for page_num, text in pages:
        for para in text.split("\n\n"):
            para = para.strip()
            if para:
                paragraphs.append((para, page_num))

    if not paragraphs:
        return []

    chunks: list[tuple[str, int]] = []
    current_text = ""
    current_page = paragraphs[0][1]

    for para_text, page_num in paragraphs:
        if not current_text:
            current_text = para_text
            current_page = page_num
        elif len(current_text) + len(para_text) + 2 <= chunk_size:
            current_text += "\n\n" + para_text
        else:
            chunks.append((current_text.strip(), current_page))
            overlap_start = max(0, len(current_text) - chunk_overlap)
            current_text = current_text[overlap_start:] + "\n\n" + para_text
            current_page = page_num

    if current_text.strip():
        chunks.append((current_text.strip(), current_page))

    return chunks
