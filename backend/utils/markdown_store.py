"""Local filesystem store for extracted markdown blobs."""

from pathlib import Path

from core.config import settings


def save_markdown(isin: str, filename: str, markdown: str) -> str:
    """Save markdown to <BLOBSTORE_PATH>/<isin>/<stem>.md, return relative path."""
    root = Path(settings.BLOBSTORE_PATH)
    stem = Path(filename).stem
    rel_path = f"{isin}/{stem}.md"
    full_path = root / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(markdown, encoding="utf-8")
    return rel_path


def load_markdown(relative_path: str) -> str:
    """Read markdown back by relative path."""
    root = Path(settings.BLOBSTORE_PATH)
    return (root / relative_path).read_text(encoding="utf-8")
