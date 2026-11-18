#!/usr/bin/env python3
"""Gestión de tareas con WIP = 1 (subsistema de Alcance).

task.py list                 tareas, estado y si están listas (dependencias hechas)
task.py next                 próximas tareas listas
task.py current              tarea activa
task.py start TASK-ID        activa una tarea (falla si hay otra activa o dependencias pendientes)
task.py done  TASK-ID        ejecuta verify (asumiendo la tarea hecha), comprueba que los archivos
                             cambiados estén dentro de los permitidos y marca [x] en tasks.md
task.py abort                desactiva la tarea activa sin marcarla
task.py lint                 valida formato de todos los tasks.md
task.py files [TASK-ID]      archivos permitidos (de la activa por defecto)
"""

from __future__ import annotations

import datetime as dt
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from harness_lib import (  # noqa: E402
    CURRENT_TASK,
    ROOT,
    changed_files,
    head_sha,
    lint_tasks,
    load_requirements,
    load_tasks,
    path_allowed,
    read_json,
    set_task_done,
    write_json,
)

# Siempre editables durante una tarea (estado y bitácora).
ALWAYS_ALLOWED = ["PROGRESS.md", ".harness/**"]


def find(task_id: str):
    for t in load_tasks():
        if t.id == task_id:
            return t
    sys.exit(f"tarea desconocida: {task_id}")


def ready(t, by_id) -> bool:
    return not t.done and all(by_id[d].done for d in t.deps if d in by_id)


def cmd_list(only_ready: bool = False) -> int:
    tasks = load_tasks()
    by_id = {t.id: t for t in tasks}
    cur = (read_json(CURRENT_TASK) or {}).get("id")
    for t in tasks:
        if only_ready and not ready(t, by_id):
            continue
        state = "▶" if t.id == cur else ("✓" if t.done else ("○" if ready(t, by_id) else "·"))
        par = "[P]" if t.parallel else "   "
        print(f" {state} {t.id:<11} {par} {t.type:<8} {t.title}")
    if not only_ready:
        print("\n ✓ hecha  ▶ activa  ○ lista  · bloqueada por dependencias")
    return 0


def cmd_current() -> int:
    cur = read_json(CURRENT_TASK)
    if not cur:
        print("sin tarea activa (make task-start ID=...)")
        return 1
    print(f"activa: {cur['id']} — {cur['title']} (desde {cur['started_at']})")
    print("archivos permitidos:\n  " + "\n  ".join(cur["files"]))
    return 0


def cmd_start(task_id: str) -> int:
    cur = read_json(CURRENT_TASK)
    if cur and cur.get("id") != task_id:
        sys.exit(f"WIP=1: ya está activa {cur['id']}. Termínala (task done) o abórtala (task abort).")
    tasks = load_tasks()
    by_id = {t.id: t for t in tasks}
    t = find(task_id)
    if t.done:
        sys.exit(f"{task_id} ya está hecha")
    pending = [d for d in t.deps if d in by_id and not by_id[d].done]
    if pending:
        sys.exit(f"{task_id} depende de tareas pendientes: {', '.join(pending)}")
    write_json(
        CURRENT_TASK,
        {
            "id": t.id,
            "title": t.title,
            "type": t.type,
            "spec": t.spec,
            "reqs": t.reqs,
            "files": t.files,
            "started_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "start_commit": head_sha(),
            "baseline_dirty": changed_files(),
        },
    )
    print(f"▶ {t.id} activa — {t.title}\n  tipo: {t.type} · REQ: {', '.join(t.reqs) or '—'}")
    print("  archivos permitidos:\n    " + "\n    ".join(t.files))
    print(f"  hecho cuando: {t.done_when}")
    return 0


def cmd_done(task_id: str) -> int:
    cur = read_json(CURRENT_TASK)
    if not cur or cur.get("id") != task_id:
        sys.exit(f"{task_id} no es la tarea activa ({cur.get('id') if cur else 'ninguna'})")
    t = find(task_id)
    # 1) alcance: los archivos cambiados desde el inicio deben estar permitidos
    baseline = set(cur.get("baseline_dirty", []))
    touched = [f for f in changed_files(cur.get("start_commit")) if f not in baseline]
    allowed = t.files + ALWAYS_ALLOWED + [str(t.file.relative_to(ROOT)).replace("\\", "/")]
    outside = [f for f in touched if not path_allowed(f, allowed)]
    if outside:
        print("✗ archivos fuera del alcance de la tarea:\n  " + "\n  ".join(outside), file=sys.stderr)
        print("  revierte esos cambios o actualiza la tarea en tasks.md (con revisión humana).", file=sys.stderr)
        return 1
    # 2) verificación completa, considerando la tarea como hecha (trazabilidad en alcance)
    env = {**os.environ, "HARNESS_ASSUME_DONE": task_id}
    print(f"▶ make verify (asumiendo {task_id} hecha)…", flush=True)
    code = subprocess.run([sys.executable, str(ROOT / "scripts/verify.py")], cwd=ROOT, env=env).returncode
    if code != 0:
        print(f"✗ verify en rojo: {task_id} NO se marca como hecha.", file=sys.stderr)
        return 1
    set_task_done(t, True)
    CURRENT_TASK.unlink(missing_ok=True)
    scope = {"service-a": "a", "service-b": "b", "frontend": "front", "plataforma": "platform", "sistema": "system"}
    spec_scope = next((v for k, v in scope.items() if k in t.spec), "repo")
    kind = {"test": "test", "impl": "feat", "scaffold": "chore", "ops": "chore"}.get(t.type, "chore")
    print(f"✓ {task_id} marcada como hecha en {t.file.relative_to(ROOT)}")
    print(f'  commit sugerido: git add -A && git commit -m "{kind}({spec_scope}): {t.title.lower()} [{task_id}]"')
    print("  luego: actualiza PROGRESS.md y, si una feature quedó completa, make feature-pass ID=FEAT-…")
    return 0


def cmd_abort() -> int:
    cur = read_json(CURRENT_TASK)
    CURRENT_TASK.unlink(missing_ok=True)
    print(f"tarea {cur['id'] if cur else '(ninguna)'} desactivada (sin marcar)")
    return 0


def cmd_lint() -> int:
    errors = lint_tasks(load_tasks(), load_requirements())
    n = len(load_tasks())
    if errors:
        print("\n".join("  ✗ " + e for e in errors), file=sys.stderr)
        return 1
    print(f"  ✓ {n} tareas con formato válido")
    return 0


def cmd_files(task_id: str | None) -> int:
    if task_id is None:
        cur = read_json(CURRENT_TASK)
        if not cur:
            sys.exit("sin tarea activa")
        task_id = cur["id"]
    print("\n".join(find(task_id).files))
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "list":
        return cmd_list()
    if cmd == "next":
        return cmd_list(only_ready=True)
    if cmd == "current":
        return cmd_current()
    if cmd in {"start", "done"}:
        if not rest:
            sys.exit(f"uso: task.py {cmd} TASK-ID")
        return cmd_start(rest[0]) if cmd == "start" else cmd_done(rest[0])
    if cmd == "abort":
        return cmd_abort()
    if cmd == "lint":
        return cmd_lint()
    if cmd == "files":
        return cmd_files(rest[0] if rest else None)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
