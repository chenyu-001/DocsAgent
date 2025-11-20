"""
‡,åw
"""
import re
import unicodedata
from typing import Optional


def normalize_unicode(text: str) -> str:
    """
    Unicode ÆNFKC	

    Args:
        text: “e‡,

    Returns:
        Æ„‡,

    Example:
        >>> normalize_unicode("le")  # ÞW
        'file'
    """
    return unicodedata.normalize("NFKC", text)


def remove_extra_whitespace(text: str) -> str:
    """
    ûdYz}W&

    Args:
        text: “e‡,

    Returns:
        „‡,

    Example:
        >>> remove_extra_whitespace("Hello    World\\n\\n\\nTest")
        'Hello World\\nTest'
    """
    # *z<ÿb:U*z<
    text = re.sub(r" +", " ", text)
    # *bL&ÿb:ÌbLÝYµ=	
    text = re.sub(r"\n{3,}", "\n\n", text)
    # »dL–L>z}
    text = "\n".join(line.strip() for line in text.split("\n"))
    return text.strip()


def remove_control_characters(text: str) -> str:
    """
    ûd§6W&

    Args:
        text: “e‡,

    Returns:
        „‡,
    """
    # ÝYbL&6h&ûdvÖ§6W&
    return "".join(char for char in text if unicodedata.category(char)[0] != "C" or char in "\n\t")


def remove_urls(text: str) -> str:
    """
    ûd URL

    Args:
        text: “e‡,

    Returns:
        ûd URL „‡,
    """
    url_pattern = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    return re.sub(url_pattern, "", text)


def remove_emails(text: str) -> str:
    """
    ûd®±0@

    Args:
        text: “e‡,

    Returns:
        ûd®±„‡,
    """
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    return re.sub(email_pattern, "", text)


def remove_special_chars(text: str, keep: Optional[str] = None) -> str:
    """
    ûdyŠW&ÝYWÍpW-‡ú,¹	

    Args:
        text: “e‡,
        keep: ÝY„W&

    Returns:
        „‡,
    """
    if keep:
        pattern = f"[^a-zA-Z0-9\u4e00-\u9fff""''	{re.escape(keep)}\\s]"
    else:
        pattern = r"[^a-zA-Z0-9\u4e00-\u9fff""''	\s]"
    return re.sub(pattern, "", text)


def clean_text(
    text: str,
    normalize: bool = True,
    remove_whitespace: bool = True,
    remove_control: bool = True,
    remove_url: bool = False,
    remove_email: bool = False,
    remove_special: bool = False,
    keep_chars: Optional[str] = None,
) -> str:
    """
    ü‡,

    Args:
        text: “e‡,
        normalize: /&Æ Unicode
        remove_whitespace: /&ûdYz}
        remove_control: /&ûd§6W&
        remove_url: /&ûd URL
        remove_email: /&ûd®±
        remove_special: /&ûdyŠW&
        keep_chars: ÝY„W&

    Returns:
        „‡,

    Example:
        >>> clean_text("  Hello   World  \\n\\n\\n Test  ", normalize=True, remove_whitespace=True)
        'Hello World\\nTest'
    """
    if normalize:
        text = normalize_unicode(text)

    if remove_control:
        text = remove_control_characters(text)

    if remove_url:
        text = remove_urls(text)

    if remove_email:
        text = remove_emails(text)

    if remove_special:
        text = remove_special_chars(text, keep=keep_chars)

    if remove_whitespace:
        text = remove_extra_whitespace(text)

    return text


if __name__ == "__main__":
    # KÕ
    test_text = """
    Hello    World

    This is a  test  ‡,
    Email: test@example.com
    URL: https://example.com
    """
    print("ŸË‡,")
    print(repr(test_text))
    print("\n")
    print(repr(clean_text(test_text, remove_url=True, remove_email=True)))
