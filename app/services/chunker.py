"""Text chunking for PDF documents."""

from langchain_text_splitters import RecursiveCharacterTextSplitter

# Chunk size in characters (~1000 tokens)
CHUNK_SIZE = 4000
CHUNK_OVERLAP = 200


def split_text_into_chunks(text: str) -> list[str]:
    """
    Split text into chunks using RecursiveCharacterTextSplitter.

    Strategy:
    - Small documents (≤ CHUNK_SIZE): single chunk, no API overhead
    - Large documents: split by paragraphs → lines → sentences → words

    Args:
        text: Text from PDF

    Returns:
        List of text chunks
    """
    if not text or not text.strip():
        return []

    text = text.strip()

    # Small documents: single chunk
    if len(text) <= CHUNK_SIZE:
        return [text]

    # Large documents: recursive splitting
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", ", ", " ", ""],
        length_function=len,
    )

    return splitter.split_text(text)


def get_chunk_count(text: str) -> int:
    """Return the number of chunks that would be created from text."""
    return len(split_text_into_chunks(text))
