from __future__ import annotations

import hashlib
import shutil
import tempfile
from pathlib import Path


HIDDEN_TEST_NAMES = {"test_hidden.py"}


def protected_copy(repository: Path) -> Path:
    workspace = Path(tempfile.mkdtemp(prefix="patchgap-protected-"))
    shutil.copytree(repository, workspace, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
    return workspace


def agent_copy(repository: Path) -> Path:
    """Copy only code and public tests into a provider-visible workspace."""
    workspace = protected_copy(repository)
    for hidden in workspace.rglob("test_*.py"):
        if hidden.name in HIDDEN_TEST_NAMES:
            hidden.unlink()
    return workspace


def manifest(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }
