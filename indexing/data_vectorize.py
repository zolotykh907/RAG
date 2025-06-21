import numpy as np
import faiss


def create_embeddings(texts, model, batch_size=32):
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True
    )

    return embeddings


def create_faiss(embeddings, index_path="data/RuBQ_index.index"):
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)

    index.add(np.array(embeddings, dtype=np.float32))

    faiss.write_index(index, index_path)