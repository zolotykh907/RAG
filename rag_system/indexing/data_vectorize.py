import os
from typing import List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from rag_system.shared.embedding_prefix import prepare_embedding_texts


def create_embeddings(
    texts: List[str],
    model: SentenceTransformer,
    batch_size: int = 32,
    model_name: Optional[str] = None,
    is_query: bool = False,
) -> np.ndarray:
    """Create embeddings for input texts.

    Args:
        texts: Texts to embed.
        model: SentenceTransformer model for generating embeddings.
        batch_size: Number of texts to process in one batch.
        model_name: Optional embedding model name used for model-specific preprocessing.
        is_query: If True, prepare texts as query embeddings.

    Returns:
        L2-normalized float32 array of embeddings.
    """
    import faiss

    prepared_texts = prepare_embedding_texts(model_name, texts, is_query=is_query)

    embeddings = model.encode(
        prepared_texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True
    )

    embeddings = np.array(embeddings, dtype=np.float32)
    faiss.normalize_L2(embeddings)

    return embeddings


def check_existing_embeddings(embeddings_path: str) -> bool:
    """Check whether an embeddings file exists on disk.

    Args:
        embeddings_path: Path to the .npy embeddings file.

    Returns:
        bool: True if the file exists, False otherwise.
    """
    return os.path.exists(embeddings_path)


def load_embeddings(embeddings_path: str) -> Optional[np.ndarray]:
    """Load embeddings from disk if the file exists.

    Args:
        embeddings_path: Path to the .npy embeddings file.

    Returns:
        numpy.ndarray if the file exists, None otherwise.
    """
    if check_existing_embeddings(embeddings_path):
        return np.load(embeddings_path)
    return None


def save_embeddings(embeddings: np.ndarray, embeddings_path: str) -> None:
    """Save embeddings atomically: write to a temp file then rename.

    Args:
        embeddings: Numpy array of embeddings to persist.
        embeddings_path: Destination path for the .npy file.

    Raises:
        Exception: If the file cannot be written or atomically replaced.
    """
    tmp_path = embeddings_path + ".tmp"
    try:
        with open(tmp_path, "wb") as f:
            np.save(f, embeddings)
        os.replace(tmp_path, embeddings_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
