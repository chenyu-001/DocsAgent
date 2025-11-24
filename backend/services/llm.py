"""LLM client utilities."""
from openai import OpenAI
from api.config import settings
from loguru import logger


class LLMClient:
    """Wrapper around an OpenAI-compatible chat completion API."""

    def __init__(self):
        if not settings.LLM_API_KEY:
            raise ValueError("LLM_API_KEY is not configured")

        self.client = OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_API_BASE,
        )

    def generate_answer(self, question: str, context: str) -> str:
        """Generate an answer using provided context snippets."""
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一名精确、简洁的文档助理。"
                    "请基于给定的参考内容回答用户问题；如果资料不足以回答，请明确告知。"
                ),
            },
            {
                "role": "user",
                "content": (
                    "请使用下面的参考内容回答用户问题。保持回答简洁、直接，并引用最相关的信息。\n\n"
                    f"用户问题：{question}\n\n"
                    f"参考内容：\n{context}"
                ),
            },
        ]

        response = self.client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=messages,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            timeout=settings.LLM_TIMEOUT,
        )

        answer = response.choices[0].message.content or ""
        return answer.strip()


_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Get or create a singleton LLM client instance."""
    global _llm_client
    if _llm_client is None:
        try:
            _llm_client = LLMClient()
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Failed to initialize LLM client: {exc}")
            raise
    return _llm_client
