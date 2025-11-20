"""
Utility Functions Module
"""
from utils.hash import compute_file_hash, compute_text_hash
from utils.text_clean import clean_text, remove_extra_whitespace, normalize_unicode
from utils.timing import timer, async_timer

__all__ = [
    "compute_file_hash",
    "compute_text_hash",
    "clean_text",
    "remove_extra_whitespace",
    "normalize_unicode",
    "timer",
    "async_timer",
]
