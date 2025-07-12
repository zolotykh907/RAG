import os
import numpy as np


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


def check_existing_embeddings(embeddings_path):
        return os.path.exists(embeddings_path)


def load_embeddings(embeddings_path):
    if check_existing_embeddings(embeddings_path):
        return np.load(embeddings_path)
    return None


def save_embeddings(embeddings, embeddings_path):
    np.save(embeddings_path, embeddings)