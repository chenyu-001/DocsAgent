"""‡,‡öãhTXTMDHTML	"""
from utils.text_clean import clean_text
from bs4 import BeautifulSoup
import markdown


class TextParser:
    """¯‡,MarkdownHTML ãh"""

    def parse(self, file_path: str):
        """ã‡,‡ö"""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()

        # 9n‡öiU
        if file_path.endswith(".html") or file_path.endswith(".htm"):
            text = self._parse_html(raw_text)
        elif file_path.endswith(".md"):
            text = self._parse_markdown(raw_text)
        else:
            text = raw_text

        cleaned_text = clean_text(text)

        return {
            "text": cleaned_text,
            "metadata": {},
            "page_count": None,
            "word_count": len(cleaned_text.split()),
        }

    def _parse_html(self, html_content: str) -> str:
        """ã HTML"""
        soup = BeautifulSoup(html_content, "lxml")
        for script in soup(["script", "style"]):
            script.decompose()
        return soup.get_text()

    def _parse_markdown(self, md_content: str) -> str:
        """ã Markdown 0¯‡,"""
        html = markdown.markdown(md_content)
        return self._parse_html(html)
