"""PDF „êh"""
import fitz  # PyMuPDF
from utils.text_clean import clean_text


class PDFParser:
    """PDF ác„êh"""

    def parse(self, file_path: str):
        """„ê PDF áˆ"""
        doc = fitz.open(file_path)
        text_parts = []
        metadata = {}

        # –÷Cpn
        meta = doc.metadata
        if meta:
            metadata = {
                "title": meta.get("title", ""),
                "author": meta.get("author", ""),
                "subject": meta.get("subject", ""),
                "keywords": meta.get("keywords", ""),
            }

        # –÷á,
        for page_num, page in enumerate(doc):
            page_text = page.get_text()
            if page_text.strip():
                text_parts.append(page_text)

        full_text = "\n\n".join(text_parts)
        cleaned_text = clean_text(full_text)

        return {
            "text": cleaned_text,
            "metadata": metadata,
            "page_count": len(doc),
            "word_count": len(cleaned_text.split()),
        }
