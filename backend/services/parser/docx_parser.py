"""DOCX „êh"""
from docx import Document
from utils.text_clean import clean_text


class DOCXParser:
    """Word ác„êh"""

    def parse(self, file_path: str):
        """„ê DOCX áˆ"""
        doc = Document(file_path)
        text_parts = []

        # –÷µ=á,
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)

        # –÷h<á,
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells)
                if row_text.strip():
                    text_parts.append(row_text)

        full_text = "\n".join(text_parts)
        cleaned_text = clean_text(full_text)

        # –÷Cpn
        core_props = doc.core_properties
        metadata = {
            "title": core_props.title or "",
            "author": core_props.author or "",
            "subject": core_props.subject or "",
            "keywords": core_props.keywords or "",
        }

        return {
            "text": cleaned_text,
            "metadata": metadata,
            "page_count": None,
            "word_count": len(cleaned_text.split()),
        }
