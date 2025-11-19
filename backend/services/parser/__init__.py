"""ác„êh!W"""
from services.parser.pdf_parser import PDFParser
from services.parser.docx_parser import DOCXParser
from services.parser.pptx_parser import PPTXParser
from services.parser.text_parser import TextParser
from models.document_models import DocumentType


class DocumentParser:
    """ác„êhÂÇ"""

    @staticmethod
    def parse(file_path: str, file_type: DocumentType):
        parsers = {
            DocumentType.PDF: PDFParser,
            DocumentType.DOCX: DOCXParser,
            DocumentType.PPTX: PPTXParser,
            DocumentType.TXT: TextParser,
            DocumentType.MD: TextParser,
        }
        parser_class = parsers.get(file_type)
        if not parser_class:
            raise ValueError(f"/Ñáˆ{ã: {file_type}")
        return parser_class().parse(file_path)
