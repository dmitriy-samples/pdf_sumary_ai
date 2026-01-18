"""Document summarization with Map-Reduce strategy using LangChain."""

import asyncio
import logging
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.rate_limiters import InMemoryRateLimiter

from app.config import (
    LLM_PROVIDER, OPENAI_API_KEY, OPENAI_MODEL, GOOGLE_API_KEY, GEMINI_MODEL,
    IONET_API_KEY, IONET_BASE_URL, IONET_MODEL,
    LLM_TEMPERATURE, LLM_MAX_TOKENS, RATE_LIMIT_RPM
)
from app.services.chunker import split_text_into_chunks

logger = logging.getLogger(__name__)

# Shared rate limiter for all LLM calls (thread-safe, async-safe)
rate_limiter = InMemoryRateLimiter(
    requests_per_second=RATE_LIMIT_RPM / 60.0,
    check_every_n_seconds=0.5,
    max_bucket_size=1,
)


def _create_llm() -> BaseChatModel:
    """Create LLM instance based on configured provider."""
    if LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            rate_limiter=rate_limiter,
        )
    elif LLM_PROVIDER == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is required when LLM_PROVIDER=gemini")
        return ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=LLM_TEMPERATURE,
            max_output_tokens=LLM_MAX_TOKENS,
            rate_limiter=rate_limiter,
        )
    elif LLM_PROVIDER == "ionet":
        from langchain_openai import ChatOpenAI
        if not IONET_API_KEY:
            raise ValueError("IONET_API_KEY is required when LLM_PROVIDER=ionet")
        return ChatOpenAI(
            model=IONET_MODEL,
            api_key=IONET_API_KEY,
            base_url=IONET_BASE_URL,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            rate_limiter=rate_limiter,
        )
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}. Use 'openai', 'gemini', or 'ionet'")


# Initialize LLM based on provider
llm = _create_llm()
logger.info(f"Using LLM provider: {LLM_PROVIDER}")

# Prompts
MAP_SYSTEM = """You are a document summarizer. Summarize the following section of a document.
Focus on key points, main ideas, and important details.
Keep the summary concise but informative."""

REDUCE_SYSTEM = """You are a document summarizer. You are given summaries of different sections from a single document.
Combine these into one coherent, well-structured summary.
Use markdown formatting for better readability.
Highlight the most important points and maintain logical flow."""


async def _summarize_chunk(chunk: str) -> str:
    """Summarize a single chunk of text."""
    messages = [
        SystemMessage(content=MAP_SYSTEM),
        HumanMessage(content=f"Summarize this section:\n\n{chunk}"),
    ]
    response = await llm.ainvoke(messages)
    return response.content


async def _combine_summaries(summaries: list[str]) -> str:
    """Combine multiple summaries into final summary."""
    combined_text = "\n\n---\n\n".join(summaries)
    messages = [
        SystemMessage(content=REDUCE_SYSTEM),
        HumanMessage(content=f"Combine these section summaries into a final summary:\n\n{combined_text}"),
    ]
    response = await llm.ainvoke(messages)
    return response.content


async def summarize_text(text: str) -> str:
    """
    Generate summary using Map-Reduce strategy with async parallel processing.

    For small documents: direct summarization
    For large documents: chunk -> summarize each in parallel -> combine

    Args:
        text: Full document text (markdown)

    Returns:
        Final summary in markdown format
    """
    if not text or not text.strip():
        return "No content to summarize."

    # Split into semantic chunks
    chunks = split_text_into_chunks(text)
    chunk_count = len(chunks)

    logger.info(f"Document split into {chunk_count} chunks")

    # Small document: single-pass summarization
    if chunk_count <= 1:
        logger.info("Single chunk - direct summarization")
        return await _summarize_chunk(chunks[0] if chunks else text)

    # Large document: Map-Reduce with parallel processing
    logger.info(f"Map-Reduce: summarizing {chunk_count} chunks in parallel")

    # Map: summarize all chunks in parallel
    chunk_summaries = await asyncio.gather(
        *[_summarize_chunk(chunk) for chunk in chunks]
    )
    chunk_summaries = list(chunk_summaries)

    # Reduce: combine summaries
    # If too many summaries, do hierarchical reduction
    max_summaries_per_reduce = 10

    while len(chunk_summaries) > max_summaries_per_reduce:
        logger.info(f"Hierarchical reduce: {len(chunk_summaries)} -> batches of {max_summaries_per_reduce}")
        batches = [
            chunk_summaries[i:i + max_summaries_per_reduce]
            for i in range(0, len(chunk_summaries), max_summaries_per_reduce)
        ]
        chunk_summaries = await asyncio.gather(
            *[_combine_summaries(batch) for batch in batches]
        )
        chunk_summaries = list(chunk_summaries)

    logger.info("Final reduce step")
    final_summary = await _combine_summaries(chunk_summaries)

    return final_summary
