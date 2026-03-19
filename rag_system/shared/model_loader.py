import os
from pathlib import Path


def get_hf_cache_model_path(model_name):
    """Find model path in local HuggingFace cache.

    Args:
        model_name (str): HuggingFace model name (e.g. 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2').

    Returns:
        str: Path to the latest snapshot directory.

    Raises:
        FileNotFoundError: If model is not found in local cache.
    """
    model_cache_name = model_name.replace('/', '--')
    cache_dir = os.path.join(
        Path.home(),
        ".cache",
        "huggingface",
        "hub",
        f"models--{model_cache_name}",
        "snapshots"
    )

    if not os.path.exists(cache_dir):
        raise FileNotFoundError(f"Model {model_name} not found in local cache {cache_dir}.")

    snapshots = [d for d in os.listdir(cache_dir) if os.path.isdir(os.path.join(cache_dir, d))]
    if not snapshots:
        raise FileNotFoundError(f"Model {model_name} not found in local cache {cache_dir}.")

    # Pick the snapshot with the most files — alphabetical sort is unreliable when
    # multiple snapshots exist (e.g. one partial and one full download).
    def _snapshot_file_count(name: str) -> int:
        path = os.path.join(cache_dir, name)
        return sum(1 for _ in os.walk(path))

    latest_snapshot = max(snapshots, key=_snapshot_file_count)
    return os.path.join(cache_dir, latest_snapshot)
