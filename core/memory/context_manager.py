"""Memory context manager - single funnel for agent memory.

Follows guideline: "One memory funnel per agent."
This is the owned stage that produces effective context for the model.

Currently placeholder for future memory management features:
- Conversation history summarization
- Context window management
- Long-term memory retrieval
"""

import structlog

logger = structlog.get_logger(__name__)


class ContextManager:
    """Manages context and memory for agent invocations.

    This is the single entry point for memory operations.
    All context shaping, retrieval, and injection happens here.
    """

    def __init__(self, max_context_length: int = 4000):
        """Initialize context manager.

        Args:
            max_context_length: Maximum context length in tokens
        """
        self.max_context_length = max_context_length
        logger.info("context_manager_initialized", max_context_length=max_context_length)

    def prepare_context(self, article: str, question: str) -> dict:
        """Prepare context for agent invocation.

        Args:
            article: Original article text
            question: User question

        Returns:
            Dictionary with prepared context
        """
        # TODO: Add context trimming/summarization if article too long
        # TODO: Add conversation history if implementing multi-turn
        # TODO: Add retrieved context from vector store if needed

        context = {
            "article": article,
            "question": question,
            "article_length": len(article),
            "question_length": len(question),
        }

        logger.info(
            "context_prepared",
            article_length=context["article_length"],
            question_length=context["question_length"],
        )

        return context

    def should_chunk_article(self, article: str) -> bool:
        """Determine if article should be chunked based on length.

        Args:
            article: Article text

        Returns:
            True if article should be chunked
        """
        # Rough heuristic: 1 token ≈ 4 characters
        estimated_tokens = len(article) // 4

        if estimated_tokens > self.max_context_length:
            logger.warning(
                "article_too_long",
                estimated_tokens=estimated_tokens,
                max_tokens=self.max_context_length,
            )
            return True

        return False

    def chunk_article(self, article: str, chunk_size: int = 3000) -> list[str]:
        """Chunk article into smaller pieces.

        Args:
            article: Article text
            chunk_size: Target chunk size in characters

        Returns:
            List of article chunks
        """
        # Simple chunking by paragraphs or sentences
        # TODO: Implement smarter chunking (semantic, overlapping, etc.)

        chunks = []
        current_chunk = ""

        paragraphs = article.split("\n\n")

        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"

        if current_chunk:
            chunks.append(current_chunk.strip())

        logger.info("article_chunked", chunks_count=len(chunks))

        return chunks

