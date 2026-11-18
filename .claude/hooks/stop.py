#!/usr/bin/env python3
"""Hook Stop — subsistemas de Verificación y Ciclo de vida.

Antes de que el agente dé el turno por terminado:
  1. Si el árbol cambió desde el último verify verde → ejecuta `make verify` (o scripts/verify.py).
     Si falla → bloquea el cierre UNA vez con el resumen (el agente debe arreglar o explicar).
  2. Si hay cambios sin reflejar en PROGRESS.md → bloquea UNA vez para recordarlo.
`stop_hook_active` evita bucles: el segundo intento de parar siempre se permite.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def native(s: str) -> str:
    """Convierte rutas estilo Git Bash (/c/Users/...) a rutas nativas en Windows."""
    m = re.match(r"^/([a-zA-Z])/(.*)", s or "")
    return f"{m.group(1).upper()}:/{m.group(2)}" if (os.name == "nt" and m) else s


ROOT = Path(native(os.environ.get("CLAUDE_PROJECT_DIR", "")) or Path(__file__).resolve().parents[2]).resolve()
sys.path.insert(0, str(ROOT / "scripts"))
from harness_lib import LAST_VERIFY, changed_files, read_json, worktree_fingerprint  # noqa: E402


def block(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    sys.exit(0)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    if payload.get("stop_hook_active"):
        sys.exit(0)

    dirty = [f for f in changed_files() if not f.startswith(".harness/")]
    last = read_json(LAST_VERIFY) or {}
    if dirty and not (last.get("ok") and last.get("fingerprint") == worktree_fingerprint()):
        # En Windows, "bash" desde Python puede resolver al bash de WSL: usar este mismo intérprete.
        cmd = ["make", "verify"] if shutil.which("make") else [sys.executable, str(ROOT / "scripts/verify.py")]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-30:])
            block(
                "`make verify` está en ROJO. Una tarea no está hecha hasta que verify pase. "
                "Corrige los fallos o explica al usuario por qué quedan pendientes.\n\n" + tail
            )

    if dirty and "PROGRESS.md" not in dirty:
        block(
            "Hay cambios en el árbol pero PROGRESS.md no se actualizó. Actualiza las secciones "
            "Hecho / En curso / Siguiente / Bloqueos / Decisiones antes de terminar "
            "(al cerrar la sesión: `make end-session`)."
        )
    sys.exit(0)


if __name__ == "__main__":
    main()
