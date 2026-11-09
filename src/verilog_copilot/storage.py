"""Minimal artifact storage: run directories, hashing, collision-refusing writes."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


class OutputExistsError(FileExistsError):
    """The requested run directory or artifact already exists."""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def create_run_dir(path: Path) -> Path:
    """Create a fresh run directory. Refuses to reuse an existing path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.mkdir(exist_ok=False)
    except FileExistsError as exc:
        raise OutputExistsError(f"output path already exists, refusing to overwrite: {path}") from exc
    return path.resolve()


def copy_file_exclusive(src: Path, dst: Path) -> None:
    """Copy ``src`` to ``dst``; fails if ``dst`` already exists."""
    try:
        with open(src, "rb") as fin, open(dst, "xb") as fout:
            for block in iter(lambda: fin.read(1024 * 1024), b""):
                fout.write(block)
    except FileExistsError as exc:
        raise OutputExistsError(f"artifact already exists: {dst}") from exc


def write_json_exclusive(path: Path, data: Any) -> None:
    """Atomically publish JSON at ``path``; never replaces an existing file.

    Writes a temp file in the same directory, fsyncs it, then hard-links it into
    place (``link`` fails if the target exists), so readers never observe a
    partial file and earlier artifacts are never overwritten.
    """
    path = Path(path)
    text = json.dumps(data, indent=2, sort_keys=False) + "\n"
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, 0o644)  # mkstemp creates 0600; match other artifacts
        try:
            os.link(tmp, path)
        except FileExistsError as exc:
            raise OutputExistsError(f"artifact already exists: {path}") from exc
    finally:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
