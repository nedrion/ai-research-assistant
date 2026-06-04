import fitz


def load_pdf(filepath: str) -> str:
    doc = fitz.open(filepath)
    text_parts = []
    for page_num, page in enumerate(doc, 1):
        text = page.get_text()
        if text.strip():
            text_parts.append(f"--- Page {page_num} ---\n{text}")
    doc.close()
    return "\n\n".join(text_parts)
