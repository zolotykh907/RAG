import numpy as np
from sentence_transformers import SentenceTransformer
import faiss


def create_embeddings(texts, model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", batch_size=32):
    model = SentenceTransformer(model_name)
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