from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .models import RepoContext


PYTHON_FUNCTION = re.compile(r"^def\s+([A-Za-z_]\w*)\s*\(", re.MULTILINE)


class RepoAnalyzer:
    """Small, best-effort repository analyzer; intentionally strongest on the payment demo."""

    def analyze(self, repository: Path, issue: str | None = None, diff: str | None = None) -> RepoContext:
        root = repository.resolve()
        python_files = [path for path in root.rglob("*.py") if "__pycache__" not in path.parts]
        test_files = [path.relative_to(root).as_posix() for path in python_files if "test" in path.parts or path.name.startswith("test_")]
        source_files = [path for path in python_files if path.relative_to(root).as_posix() not in test_files]
        changed = self._changed_files(root, diff)
        if not changed:
            changed = [path.relative_to(root).as_posix() for path in source_files]
        symbols: list[str] = []
        source_text = ""
        for path in source_files:
            text = path.read_text(errors="ignore")
            source_text += text.lower() + "\n"
            symbols.extend(PYTHON_FUNCTION.findall(text))
        issue_text = (issue or "").lower()
        signals = [signal for signal in ("payment", "webhook", "event", "fulfillment", "entitlement", "access") if signal in source_text or signal in issue_text]
        summary = issue or self._summarize(signals, symbols)
        return RepoContext(
            root=str(root), language="python" if python_files else "unknown", framework=None,
            changed_files=changed, tests=sorted(test_files), affected_symbols=sorted(set(symbols)),
            domain_signals=signals, change_summary=summary,
        )

    @staticmethod
    def _summarize(signals: list[str], symbols: list[str]) -> str:
        if "payment" in signals or "webhook" in signals:
            return "Payment webhook fulfillment behavior changed."
        return f"Changed behavior around {', '.join(symbols[:3]) or 'repository code'}."

    @staticmethod
    def _changed_files(root: Path, supplied_diff: str | None) -> list[str]:
        if supplied_diff:
            return sorted(set(re.findall(r"(?:\+\+\+ b/|--- a/)([^\s]+)", supplied_diff)))
        if not (root / ".git").exists():
            return []
        process = subprocess.run(["git", "diff", "--name-only", "HEAD~1..HEAD"], cwd=root, text=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        return [line for line in process.stdout.splitlines() if line]
