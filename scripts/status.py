#!/usr/bin/env python3
"""Resumen de estado para humanos y agentes (`make status`, /status, init.sh).

Imprime: secciones clave de PROGRESS.md, tarea activa, progreso por spec, próximas tareas listas,
próximas features con passes=false y el resultado de la última verificación.
Uso: status.py [--brief]
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from harness_lib import CURRENT_TASK, LAST_VERIFY, ROOT, load_features, load_tasks, read_json  # noqa: E402

SECTIONS = ("Fase actual", "En curso", "Siguiente", "Bloqueos")
PRIO = {"P1": 0, "P2": 1, "P3": 2}


def progress_sections() -> dict[str, str]:
    p = ROOT / "PROGRESS.md"
    if not p.exists():
        return {}
    text = p.read_text(encoding="utf-8")
    out = {}
    for name in SECTIONS:
        m = re.search(rf"^## {re.escape(name)}\s*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
        if m:
            body = "\n".join(line for line in m.group(1).strip().splitlines() if not line.startswith("<!--"))
            out[name] = body.strip() or "—"
    return out


def main() -> int:
    brief = "--brief" in sys.argv
    print("━━ ESTADO DEL PROYECTO " + "━" * 50)
    for k, v in progress_sections().items():
        lines = v.splitlines()
        print(f"■ {k}: " + (lines[0] if lines else "—"))
        for line in lines[1 : (3 if brief else 8)]:
            print(f"    {line}")

    cur = read_json(CURRENT_TASK)
    print(f"■ Tarea activa: {cur['id']} — {cur['title']}" if cur else "■ Tarea activa: ninguna")

    tasks = load_tasks()
    by_id = {t.id: t for t in tasks}
    per_spec: dict[str, list[int]] = {}
    for t in tasks:
        d = per_spec.setdefault(t.spec, [0, 0])
        d[0] += t.done
        d[1] += 1
    print("■ Tareas: " + " · ".join(f"{s.split('-', 1)[1]} {a}/{b}" for s, (a, b) in per_spec.items()))

    ready = [t for t in tasks if not t.done and all(by_id[d].done for d in t.deps if d in by_id)]
    print("■ Próximas tareas listas:")
    for t in ready[: 4 if brief else 8]:
        print(f"    ○ {t.id}{' [P]' if t.parallel else ''} — {t.title}")

    feats = load_features()["features"]
    pending = sorted((f for f in feats if not f["passes"]), key=lambda f: (PRIO[f["priority"]], f["id"]))
    print(f"■ Features: {len(feats) - len(pending)}/{len(feats)} con passes=true. Siguientes pendientes:")
    for f in pending[: 5 if brief else 10]:
        print(f"    ○ {f['id']} ({f['priority']}) {f['description'][:80]}")

    last = read_json(LAST_VERIFY)
    if last:
        print(f"■ Último verify: {'VERDE' if last['ok'] else 'ROJO'} · {last['at']} · commit {str(last.get('commit'))[:10]}")
    else:
        print("■ Último verify: nunca ejecutado (make verify)")
    print("━" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
