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
        # Estimate question complexity to adjust answer length
        is_complex = len(question) > 30 or '如何' in question or '步骤' in question or '详细' in question or '流程' in question
        max_length = "500-800" if is_complex else "200-400"
        max_tokens = 1200 if is_complex else 600

        messages = [
            {
                "role": "system",
                "content": (
                    "你是 DocsAgent 企业知识库的智能助手，专注于提供精准、结构化的答案。\n\n"
                    "**核心原则：**\n"
                    "1. 直接回答，不要啰嗦 - 用户时间宝贵\n"
                    "2. 突出重点，不要平铺 - 先说最重要的\n"
                    "3. 结构清晰，易于扫读 - 使用标题和列表\n"
                    "4. 引用来源，可追溯 - 必须标注文档编号\n\n"
                    "**禁止的行为：**\n"
                    "❌ 不要写长篇大论，不要啰嗦重复\n"
                    "❌ 不要平铺所有信息，要提炼核心\n"
                    "❌ 不要编造内容，只基于文档回答\n"
                    "❌ 不要忽略来源引用"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"**问题：** {question}\n\n"
                    f"**文档片段：**\n{context}\n\n"
                    "---\n\n"
                    f"**请严格按以下格式回答（总长度 {max_length} 字）：**\n\n"
                    "## 🎯 核心答案\n"
                    "[一句话直接回答问题，30-80字]\n\n"
                    "## 📋 关键要点\n"
                    "- **要点1**：[简洁描述] `[文档1]`\n"
                    "- **要点2**：[简洁描述] `[文档2]`\n"
                    "- **要点3**：[简洁描述] `[文档3]`\n\n"
                    "## 💡 补充说明（可选）\n"
                    "[如有必要，补充重要细节]\n\n"
                    "---\n\n"
                    "**格式要求：**\n"
                    "1. 必须包含\"核心答案\"和\"关键要点\"两个部分\n"
                    "2. 引用格式：`[文档1]` `[文档2]`（数字对应文档片段编号）\n"
                    "3. 根据问题复杂度调整长度：\n"
                    "   - 简单问题：200-400字，3-5个要点\n"
                    "   - 复杂问题（如何、步骤、详细）：500-800字，5-8个要点\n"
                    "4. 如果文档中没有答案，直接说\"文档中未找到相关信息\"\n"
                    "5. 使用加粗 (**) 突出关键词"
                ),
            },
        ]

        response = self.client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=messages,
            temperature=0.3,  # Lower temperature for more focused answers
            max_tokens=max_tokens,  # Adaptive based on question complexity
            timeout=settings.LLM_TIMEOUT,
        )

        answer = response.choices[0].message.content or ""
        return answer.strip()

    def generate_summary(self, text: str, filename: str) -> str:
        """
        Generate structured summary for a document

        Args:
            text: Document full text (will be truncated if too long)
            filename: Document filename for context

        Returns:
            Structured summary in markdown format
        """
        # Truncate text if too long (keep first 8000 chars for summary)
        max_chars = 8000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[文档内容过长，仅基于前 8000 字生成摘要]"

        messages = [
            {
                "role": "system",
                "content": (
                    "你是 DocsAgent 文档摘要专家，擅长提炼文档核心信息。\n\n"
                    "**你的任务：**\n"
                    "为文档生成结构化摘要，帮助用户快速了解文档内容和价值。\n\n"
                    "**核心原则：**\n"
                    "1. 精炼准确 - 每个字都有价值\n"
                    "2. 突出重点 - 核心内容优先\n"
                    "3. 结构清晰 - 便于快速扫读\n"
                    "4. 实用导向 - 帮助用户判断文档价值"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"**文档名称：** {filename}\n\n"
                    f"**文档内容：**\n{text}\n\n"
                    "---\n\n"
                    "**请严格按以下格式生成摘要（总长度 150-200 字）：**\n\n"
                    "**📄 文档主题**\n"
                    "[一句话概括文档核心内容，20-30字]\n\n"
                    "**🎯 核心要点**\n"
                    "- 要点 1（15-20字）\n"
                    "- 要点 2（15-20字）\n"
                    "- 要点 3（15-20字）\n\n"
                    "**💼 适用场景**\n"
                    "- 场景 1（15-20字）\n"
                    "- 场景 2（15-20字）\n\n"
                    "---\n\n"
                    "**格式要求：**\n"
                    "1. 总字数 150-200 字（不含 emoji 和标题）\n"
                    "2. 核心要点必须提炼最重要的 3 条\n"
                    "3. 适用场景必须写明文档的使用价值\n"
                    "4. 每条都要简洁，不超过 20 字\n"
                    "5. 禁止出现\"本文档\"、\"该文档\"等冗余表述\n"
                    "6. 禁止编造文档中没有的内容"
                ),
            },
        ]

        response = self.client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=messages,
            temperature=0.3,
            max_tokens=500,
            timeout=settings.LLM_TIMEOUT,
        )

        summary = response.choices[0].message.content or ""
        return summary.strip()


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
