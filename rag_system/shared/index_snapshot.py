import json
import os
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import faiss
import numpy as np


@dataclass(frozen=True)
class IndexArtifacts:
    """Paths that make up one consistent index snapshot."""

    processed_data_path: str
    embeddings_path: str
    index_path: str
    snapshot_id: Optional[str] = None


class IndexSnapshotStore:
    """Publish and resolve index snapshots through an atomic current pointer."""

    pointer_filename = "current_index.json"
    snapshots_dirname = "index_snapshots"

    def __init__(
        self,
        data_dir: str,
        processed_data_path: str,
        embeddings_path: str,
        index_path: str,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.snapshot_dir = self.data_dir / self.snapshots_dirname
        self.pointer_path = self.data_dir / self.pointer_filename
        self.legacy_artifacts = IndexArtifacts(
            processed_data_path=str(Path(processed_data_path)),
            embeddings_path=str(Path(embeddings_path)),
            index_path=str(Path(index_path)),
        )

    @classmethod
    def from_config(cls, config: Any) -> "IndexSnapshotStore":
        processed_data_path = str(config.processed_data_path)
        index_path = str(config.index_path)
        data_dir = str(getattr(config, "data_dir", "") or Path(processed_data_path).parent)
        embeddings_path = str(getattr(config, "embeddings_path", "") or Path(data_dir) / "embeddings.npy")
        return cls(
            data_dir=data_dir,
            processed_data_path=processed_data_path,
            embeddings_path=embeddings_path,
            index_path=index_path,
        )

    def current_artifacts(self) -> IndexArtifacts:
        """Return the currently published snapshot, or legacy paths if no pointer exists."""
        if not self.pointer_path.exists():
            return self.legacy_artifacts

        with open(self.pointer_path, "r", encoding="utf-8") as f:
            pointer = json.load(f)

        snapshot_id = pointer["snapshot"]
        snapshot_path = self.snapshot_dir / snapshot_id
        return IndexArtifacts(
            processed_data_path=str(snapshot_path / "processed_data.json"),
            embeddings_path=str(snapshot_path / "embeddings.npy"),
            index_path=str(snapshot_path / "index.index"),
            snapshot_id=snapshot_id,
        )

    def load_processed_data(self) -> List[Dict[str, Any]]:
        artifacts = self.current_artifacts()
        if not os.path.exists(artifacts.processed_data_path):
            return []
        with open(artifacts.processed_data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("Processed data must be a list")
        return data

    def load_embeddings(self) -> Optional[np.ndarray]:
        artifacts = self.current_artifacts()
        if not os.path.exists(artifacts.embeddings_path):
            return None
        return np.load(artifacts.embeddings_path)

    def publish(
        self,
        processed_data: List[Dict[str, Any]],
        embeddings: np.ndarray,
        index: Any,
    ) -> IndexArtifacts:
        """Write a complete snapshot, then atomically publish it via pointer replacement."""
        embeddings = np.array(embeddings, dtype=np.float32)
        self._validate_snapshot(processed_data, embeddings, index)

        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid.uuid4().hex
        staging_path = self.snapshot_dir / f".{snapshot_id}.tmp"
        final_path = self.snapshot_dir / snapshot_id

        try:
            staging_path.mkdir()
            processed_data_path = staging_path / "processed_data.json"
            embeddings_path = staging_path / "embeddings.npy"
            index_path = staging_path / "index.index"

            with open(processed_data_path, "w", encoding="utf-8") as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=2)
            with open(embeddings_path, "wb") as f:
                np.save(f, embeddings)
            faiss.write_index(index, str(index_path))

            manifest = {
                "version": 1,
                "snapshot": snapshot_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "items_count": len(processed_data),
                "embedding_shape": list(embeddings.shape),
            }
            with open(staging_path / "manifest.json", "w", encoding="utf-8") as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)

            os.replace(staging_path, final_path)
            self._replace_pointer(snapshot_id, len(processed_data))

            return IndexArtifacts(
                processed_data_path=str(final_path / "processed_data.json"),
                embeddings_path=str(final_path / "embeddings.npy"),
                index_path=str(final_path / "index.index"),
                snapshot_id=snapshot_id,
            )
        except Exception:
            if staging_path.exists():
                shutil.rmtree(staging_path)
            if final_path.exists() and not self._pointer_references(snapshot_id):
                shutil.rmtree(final_path)
            raise

    def clear(self) -> None:
        if self.pointer_path.exists():
            os.remove(self.pointer_path)
        if self.snapshot_dir.exists():
            shutil.rmtree(self.snapshot_dir)

        for path in (
            self.legacy_artifacts.processed_data_path,
            self.legacy_artifacts.embeddings_path,
            self.legacy_artifacts.index_path,
        ):
            if os.path.exists(path):
                os.remove(path)

    def _replace_pointer(self, snapshot_id: str, items_count: int) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        pointer_tmp = self.pointer_path.with_suffix(".json.tmp")
        pointer_data = {
            "version": 1,
            "snapshot": snapshot_id,
            "items_count": items_count,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(pointer_tmp, "w", encoding="utf-8") as f:
            json.dump(pointer_data, f, ensure_ascii=False, indent=2)
        os.replace(pointer_tmp, self.pointer_path)

    def _pointer_references(self, snapshot_id: str) -> bool:
        if not self.pointer_path.exists():
            return False
        try:
            with open(self.pointer_path, "r", encoding="utf-8") as f:
                return json.load(f).get("snapshot") == snapshot_id
        except Exception:
            return False

    @staticmethod
    def _validate_snapshot(
        processed_data: List[Dict[str, Any]],
        embeddings: np.ndarray,
        index: Any,
    ) -> None:
        if embeddings.ndim != 2:
            raise ValueError("Embeddings must be a 2D array")
        if len(processed_data) != embeddings.shape[0]:
            raise ValueError(
                f"Processed data count ({len(processed_data)}) must match embeddings count ({embeddings.shape[0]})"
            )
        if index.ntotal != len(processed_data):
            raise ValueError(f"FAISS index size ({index.ntotal}) must match processed data count ({len(processed_data)})")
