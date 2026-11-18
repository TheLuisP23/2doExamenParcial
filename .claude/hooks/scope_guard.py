#!/usr/bin/env python3
"""Hook PreToolUse (Edit|Write|MultiEdit|NotebookEdit) — subsistema de Alcance.

Reglas:
  1. Nunca: archivos .env reales, ~/.aws/*, credenciales/kubeconfig      → deny
  2. Con tarea activa: solo los archivos de su lista (+ PROGRESS.md)    → deny si no
  3. Sin tarea activa: prohibido tocar código/infra/pruebas             → deny
     (services/, frontend/, deploy/, tests/, .github/workflows/), salvo README.md
  4. Archivos del propio harness (.claude/hooks, .claude/settings.json, scripts/) → ask (humano decide)
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


def native(s: str) -> str:
    """Convierte rutas estilo Git Bash (/c/Users/...) a rutas nativas en Windows."""
    m = re.match(r"^/([a-zA-Z])/(.*)", s or "")
    return f"{m.group(1).upper()}:/{m.group(2)}" if (os.name == "nt" and m) else s


ROOT = Path(native(os.environ.get("CLAUDE_PROJECT_DIR", "")) or Path(__file__).resolve().parents[2]).resolve()
sys.path.insert(0, str(ROOT / "scripts"))
from harness_lib import CURRENT_TASK, path_allowed, read_json  # noqa: E402

IMPL_PREFIXES = ("services/", "frontend/", "deploy/", "tests/", ".github/workflows/", "docker-compose.yml")
HARNESS_FILES = (".claude/hooks/", ".claude/settings.json", "scripts/")
ALWAYS_OK = ["PROGRESS.md"]


def decide(decision: str, reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": decision,
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    sys.exit(0)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        sys.exit(0)
    ti = payload.get("tool_input") or {}
    raw = ti.get("file_path") or ti.get("notebook_path") or ti.get("path")
    if not raw:
        sys.exit(0)
    p = Path(native(raw))
    if not p.is_absolute():
        p = Path(native(payload.get("cwd", "")) or ROOT) / p
    p = p.resolve()
    name = p.name.lower()
    home = Path.home().resolve()

    # 1. secretos
    if (
        name == ".env"
        or (name.startswith(".env.") and name != ".env.example")
        or str(p).startswith(str(home / ".aws"))
        or name in {"credentials", "kubeconfig"}
        or re.search(r"\.(pem|key)$", name)
    ):
        decide("deny", f"Prohibido editar archivos de secretos ({p.name}). Usa .env.example con valores ficticios.")

    try:
        rel = p.relative_to(ROOT).as_posix()
    except ValueError:
        decide("ask", f"{p} está fuera del repositorio.")
        return

    cur = read_json(CURRENT_TASK)
    # 4. el harness se protege a sí mismo
    if rel.startswith(HARNESS_FILES):
        if cur is None or not path_allowed(rel, cur.get("files", [])):
            decide("ask", f"{rel} es parte del harness (verificación/alcance). Requiere aprobación humana.")
    if cur:
        allowed = cur.get("files", []) + ALWAYS_OK
        if not path_allowed(rel, allowed):
            decide(
                "deny",
                f"WIP=1: la tarea activa {cur['id']} no permite tocar {rel}. "
                f"Permitidos: {', '.join(allowed)}. Si hace falta, propón cambiar la tarea en tasks.md.",
            )
        sys.exit(0)
    if rel.startswith(IMPL_PREFIXES) and not rel.endswith("README.md"):
        decide(
            "deny",
            f"No hay tarea activa: no se puede editar {rel}. "
            "Sigue el flujo spec → plan → tasks y ejecuta `make task-start ID=TASK-…` (o /implement).",
        )
    sys.exit(0)


if __name__ == "__main__":
    main()
