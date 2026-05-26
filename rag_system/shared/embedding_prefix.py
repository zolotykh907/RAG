from typing import Iterable, List, Optional


def uses_e5_prefix(model_name: Optional[str]) -> bool:
    """Return whether an embedding model expects E5 query/passage prefixes.

    Args:
        model_name: Optional embedding model name.

    Returns:
        True if the model name looks like an E5 model, otherwise False.
    """
    return bool(model_name and "e5" in model_name.lower())


def prepare_embedding_texts(
    model_name: Optional[str],
    texts: Iterable[str],
    is_query: bool,
) -> List[str]:
    """Prepare texts before embedding.

    Args:
        model_name: Optional embedding model name.
        texts: Texts to prepare.
        is_query: If True, use the E5 query prefix; otherwise use the passage prefix.

    Returns:
        Texts prepared for the selected embedding model.
    """
    raw_texts = [str(text) for text in texts]
    if not uses_e5_prefix(model_name):
        return raw_texts

    prefix = "query: " if is_query else "passage: "
    return [_add_prefix_once(text, prefix) for text in raw_texts]


def _add_prefix_once(text: str, prefix: str) -> str:
    """Add an embedding prefix unless text already has a known prefix."""
    lowered = text.lstrip().lower()
    if lowered.startswith("query:") or lowered.startswith("passage:"):
        return text
    return prefix + text
