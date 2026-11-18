#!/usr/bin/env python3
"""`make end-session`: dejar el repositorio en estado limpio (subsistema de Ciclo de vida).

1. make verify completo.
2. Actualiza el bloque automático de PROGRESS.md (entre <!-- AUTO:BEGIN --> y <!-- AUTO:END -->).
3. docker compose down (si hay contenedores del proyecto).
4. Recordatorio de coste si el clúster EKS existe.
5. Falla si el árbol git no está limpio (hay que hacer commit de PROGRESS.md y del trabajo).
"""

from __future__ import annotations

import datetime as dt
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from harness_lib import CURRENT_TASK, ROOT, changed_files, head_sha, load_features, load_tasks, read_json  # noqa: E402

CLUSTER = os.environ.get("EKS_CLUSTER_NAME", "biblioteca-eks")
REGION = os.environ.get("AWS_REGION", "us-east-1")


def update_progress(verify_ok: bool) -> None:
    p = ROOT / "PROGRESS.md"
    text = p.read_text(encoding="utf-8")
    tasks = load_tasks()
    feats = load_features()["features"]
    cur = read_json(CURRENT_TASK)
    block = "\n".join(
        [
            "<!-- AUTO:BEGIN (lo escribe scripts/end_session.py; no editar a mano) -->",
            f"- Última sesión cerrada: {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}",
            f"- `make verify`: {'VERDE' if verify_ok else 'ROJO'} · HEAD `{(head_sha() or 'sin commits')[:10]}`",
            f"- Tareas hechas: {sum(t.done for t in tasks)}/{len(tasks)} · Features passes=true: "
            f"{sum(f['passes'] for f in feats)}/{len(feats)}",
            f"- Tarea activa al cerrar: {cur['id'] if cur else 'ninguna'}",
            "<!-- AUTO:END -->",
        ]
    )
    new = re.sub(r"<!-- AUTO:BEGIN.*?<!-- AUTO:END -->", block, text, flags=re.S)
    if new == text and "AUTO:BEGIN" not in text:
        new = text.rstrip() + "\n\n## Último cierre automático\n" + block + "\n"
    p.write_text(new, encoding="utf-8")


def main() -> int:
    print("▶ 1/5 verify")
    verify_ok = subprocess.run([sys.executable, str(ROOT / "scripts/verify.py")], cwd=ROOT).returncode == 0
    print("▶ 2/5 PROGRESS.md (bloque automático)")
    update_progress(verify_ok)
    print("▶ 3/5 docker compose down")
    if shutil.which("docker") and (ROOT / "docker-compose.yml").exists():
        subprocess.run(["docker", "compose", "down"], cwd=ROOT)
    print("▶ 4/5 recursos AWS")
    if shutil.which("aws"):
        r = subprocess.run(
            [
                "aws",
                "eks",
                "describe-cluster",
                "--name",
                CLUSTER,
                "--region",
                REGION,
                "--query",
                "cluster.status",
                "--output",
                "text",
                "--cli-connect-timeout",
                "5",
            ],
            capture_output=True,
            text=True,
        )
        if r.returncode == 0:
            print(
                f"  ! el clúster {CLUSTER} existe ({r.stdout.strip()}) y genera coste. "
                "Si terminaste las pruebas: make infra-down (requiere confirmación)."
            )
        else:
            print("  · clúster no encontrado o sin credenciales")
    print("▶ 5/5 árbol git")
    dirty = [f for f in changed_files() if not f.startswith(".harness/")]
    problems = []
    if not verify_ok:
        problems.append("make verify está en ROJO")
    if dirty:
        problems.append(
            "árbol git sucio:\n    "
            + "\n    ".join(dirty)
            + "\n  → actualiza las secciones manuales de PROGRESS.md y haz commit "
            "(p. ej. `docs(progress): cierre de sesión`)."
        )
    if problems:
        print("✗ la sesión NO queda limpia:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 1
    print("✓ sesión cerrada: verify verde, contenedores detenidos, árbol limpio")
    return 0


if __name__ == "__main__":
    sys.exit(main())
