"""
Text cleaning and normalization utilities
"""
import re
import unicodedata
from typing import Optional


def normalize_unicode(text: str) -> str:
    """
    Normalize Unicode text to NFKC form

    Args:
        text: Input text string

    Returns:
        Normalized text string

    Example:
        >>> normalize_unicode("file")  # Full-width characters
        'file'
    """
    return unicodedata.normalize("NFKC", text)


def remove_extra_whitespace(text: str) -> str:
    """
    Remove excessive whitespace from text

    Args:
        text: Input text string

    Returns:
        Text with normalized whitespace

    Example:
        >>> remove_extra_whitespace("Hello    World\\n\\n\\nTest")
        'Hello World\\nTest'
    """
    # Replace multiple spaces with single space
    text = re.sub(r" +", " ", text)
    # Replace more than 2 newlines with 2 newlines (keep paragraph breaks)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip whitespace from each line
    text = "\n".join(line.strip() for line in text.split("\n"))
    return text.strip()


def remove_control_characters(text: str) -> str:
    """
    Remove control characters from text

    Args:
        text: Input text string

    Returns:
        Text with control characters removed
    """
    # Keep newlines and tabs, but remove other control characters
    return "".join(char for char in text if unicodedata.category(char)[0] != "C" or char in "\n\t")


def remove_urls(text: str) -> str:
    """
    Remove URLs from text

    Args:
        text: Input text string

    Returns:
        Text with URLs removed
    """
    url_pattern = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    return re.sub(url_pattern, "", text)


def remove_emails(text: str) -> str:
    """
    Remove email addresses from text

    Args:
        text: Input text string

    Returns:
        Text with email addresses removed
    """
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    return re.sub(email_pattern, "", text)


def remove_special_chars(text: str, keep: Optional[str] = None) -> str:
    """
    Remove special characters, keeping only letters, numbers, and common punctuation

    Args:
        text: Input text string
        keep: Additional characters to preserve

    Returns:
        Cleaned text string
    """
    if keep:
        pattern = f"[^a-zA-Z0-9\u4e00-\u9fff""''	{re.escape(keep)}\\s]"
    else:
        pattern = r"[^a-zA-Z0-9\u4e00-\u9fff""''	\s]"
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
    Clean and normalize text with various options

    Args:
        text: Input text string
        normalize: Whether to normalize Unicode
        remove_whitespace: Whether to remove excessive whitespace
        remove_control: Whether to remove control characters
        remove_url: Whether to remove URLs
        remove_email: Whether to remove email addresses
        remove_special: Whether to remove special characters
        keep_chars: Additional characters to keep when removing special chars

    Returns:
        Cleaned text string

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
    # Test examples
    test_text = """
    Hello    World

    This is a  test  text.
    Email: test@example.com
    URL: https://example.com
    """
    print("Original text:")
    print(repr(test_text))
    print("\nCleaned text:")
    print(repr(clean_text(test_text, remove_url=True, remove_email=True)))
