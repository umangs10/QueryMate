"""Response utilities — extract clean text from LLM responses.

Gemini 2.5 "thinking" models may return structured content parts
instead of plain strings. This module normalizes all formats into
clean text.
"""


def extract_text(content) -> str:
    """Extract plain text from an LLM response content field.

    Handles three formats:
    1. Plain string → returned as-is.
    2. List of dicts with 'text' keys → joined text parts.
    3. List of other objects → converted to string.

    Args:
        content: The ``response.content`` value from an LLM call.

    Returns:
        A clean text string.
    """
    # Plain string — most common case
    if isinstance(content, str):
        return content

    # List of content parts (gemini-2.5-flash thinking model)
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict) and "text" in part:
                text_parts.append(part["text"])
            elif isinstance(part, str):
                text_parts.append(part)
        if text_parts:
            return "\n".join(text_parts)
        # Fallback: stringify the whole list
        return str(content)

    # Fallback for any other type
    return str(content)
