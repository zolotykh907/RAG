import numpy as np
import faiss


def create_embeddings(texts, model, batch_size=32):
    """creating embeddings for input texts.

    Args:
        texts (list[str]): list of texts.
        model: model for generating embeddings.
        batch_size (int, optional): The number of texts to process in one batch.

    Returns:
        numpy.ndarray: array of embeddings.
    """
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True
    )

    return embeddings