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
                    "1. **通读所有文档片段**：仔细阅读所有提供的片段，不要遗漏任何重要信息\n"
                    "2. **综合信息**：将分散在不同片段中的相关信息整合在一起，形成完整的答案\n"
                    "3. **准确性优先**：基于文档内容准确回答，不要编造或猜测\n"
                    "4. **结构化表达**：使用 Markdown 格式（标题、列表、加粗）使答案清晰易读\n"
                    "5. **完整性检查**：确保回答涵盖了问题的所有方面，特别是：\n"
                    "   - 如果有多个相关章节，都要提及\n"
                    "   - 如果有必选和可选步骤，都要说明\n"
                    "   - 如果有多种方法，都要列出\n"
                    "6. **引用来源**：注明关键信息来自哪个文档片段（如：根据文档[1]...）"
                ),
            },
            {
                "role": "user",
                "content": (
                    "请基于以下参考内容回答我的问题。\n\n"
                    f"**我的问题：** {question}\n\n"
                    f"**参考文档片段：**\n{context}\n\n"
                    "**回答要求：**\n"
                    "- **完整性至关重要**：仔细检查所有片段，确保没有遗漏相关内容\n"
                    "- **综合多个片段**：如果答案分散在多个片段中，请整合成完整回答\n"
                    "- **结构化输出**：使用 Markdown 格式（标题、列表、加粗）组织答案\n"
                    "- **必选vs可选**：如果文档中区分了必选和可选内容，请明确标注\n"
                    "- **引用来源**：在关键信息处标注来自哪个文档片段编号\n"
                    "- **保持准确**：只基于文档内容回答，不确定的地方说明需要更多信息"
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
