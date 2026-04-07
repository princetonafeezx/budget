from __future__ import annotations

import csv
import json
import os
import uuid
import warnings
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, cast

from parsing import parse_amount
from schemas import CategorizedRecord

CATEGORIZED_FIELDS = [ 
    "date", 
    "merchant", 
    "amount", 
    "category", 
    "subcategory", 
    "confidence", 
    "match_type", 
]

def _atomic_write_file(path: Path, write: Callable[[Path], None]) -> None: 
    """Write to a unique temp file in the same directory, then replace ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True) 
    tmp = path.parent / f".{path.name}.tmp.{uuid.uuid4().hex}" 
    try:
        write(tmp)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    try:
        os.replace(tmp, path)
    except OSError:
        tmp.unlink(missing_ok=True)
        raise

def get_data_dir(base_dir: str | Path | None = None) -> Path:  
    if base_dir is not None:
        root = Path(base_dir)
    else:
        env = (os.environ.get("LEDGERLOGIC_DATA_DIR") or "").strip()
        if env:
            root = Path(env).expanduser()
        else:
            root = Path.cwd() / "ledgerlogic_data"
    root.mkdir(parents=True, exist_ok=True)
    return root
