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
                    "你是一名专业的技术文档助理，擅长理解和解释技术文档内容。\n"
                    "你的职责是：\n"
                    "1. 仔细阅读提供的文档片段，理解其中的技术细节\n"
                    "2. 基于文档内容准确回答用户问题，不要编造信息\n"
                    "3. 使用 Markdown 格式组织答案，使其结构清晰、易读\n"
                    "4. 如果文档中有步骤、列表或重点内容，请使用对应的 Markdown 格式（列表、加粗等）\n"
                    "5. 引用具体的文档片段时，注明来源（如：根据文档[1]...）\n"
                    "6. 如果文档内容不足以回答问题，请明确说明"
                ),
            },
            {
                "role": "user",
                "content": (
                    "请基于以下参考内容回答我的问题。\n\n"
                    f"**我的问题：** {question}\n\n"
                    f"**参考文档片段：**\n{context}\n\n"
                    "**回答要求：**\n"
                    "- 使用 Markdown 格式（如标题、列表、加粗）使答案结构清晰\n"
                    "- 如果有多个步骤或要点，使用编号列表或项目符号\n"
                    "- 重要信息用**加粗**标注\n"
                    "- 引用文档时注明片段编号（如：根据文档[1]，...）\n"
                    "- 保持专业、准确、简洁"
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
