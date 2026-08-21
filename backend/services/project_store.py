from __future__ import annotations

import uuid
from pathlib import Path

from backend.services.config import RAW_DATA_DIR


class ProjectStoreService:
    def __init__(self) -> None:
        self.upload_dir = RAW_DATA_DIR / "uploads"
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def register_existing_path(self, source_path: Path) -> Path:
        if not source_path.exists():
            raise FileNotFoundError(f"Project path does not exist: {source_path}")
        return source_path.resolve()

    def save_upload(self, filename: str, content: bytes) -> Path:
        target = self.upload_dir / f"{uuid.uuid4()}_{filename}"
        target.write_bytes(content)
        return target
