from typing import Iterable, List, Optional


def uses_e5_prefix(model_name: Optional[str]) -> bool:
    """Return True for E5 embedding models that expect query/passage prefixes."""
    return bool(model_name and "e5" in model_name.lower())


def prepare_embedding_texts(
    model_name: Optional[str],
    texts: Iterable[str],
    is_query: bool,
) -> List[str]:
    """Prepare texts before embedding.

    E5 models are trained with explicit prefixes:
    - query: for user questions;
    - passage: for indexed documents.
    """
    raw_texts = [str(text) for text in texts]
    if not uses_e5_prefix(model_name):
        return raw_texts

    prefix = "query: " if is_query else "passage: "
    return [_add_prefix_once(text, prefix) for text in raw_texts]


def _add_prefix_once(text: str, prefix: str) -> str:
    lowered = text.lstrip().lower()
    if lowered.startswith("query:") or lowered.startswith("passage:"):
        return text
    return prefix + text
