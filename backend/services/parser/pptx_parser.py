"""PPTX „êh"""
from pptx import Presentation
from utils.text_clean import clean_text


class PPTXParser:
    """PowerPoint ác„êh"""

    def parse(self, file_path: str):
        """„ê PPTX áˆ"""
        prs = Presentation(file_path)
        text_parts = []

        # –÷œuÖπ
        for slide_num, slide in enumerate(prs.slides):
            slide_text = []
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_text.append(shape.text)

            if slide_text:
                text_parts.append(f"[Slide {slide_num + 1}]\n" + "\n".join(slide_text))

        full_text = "\n\n".join(text_parts)
        cleaned_text = clean_text(full_text)

        # –÷Cpn
        core_props = prs.core_properties
        metadata = {
            "title": core_props.title or "",
            "author": core_props.author or "",
            "subject": core_props.subject or "",
            "keywords": core_props.keywords or "",
        }

        return {
            "text": cleaned_text,
            "metadata": metadata,
            "page_count": len(prs.slides),
            "word_count": len(cleaned_text.split()),
        }
