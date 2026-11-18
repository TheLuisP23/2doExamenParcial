#!/usr/bin/env python3
"""Única vía para marcar una feature como pasada (`make feature-pass ID=FEAT-A-01`).

Requisitos para pasar a passes=true:
  1. todas las tareas que cubren alguno de sus REQ están [x];
  2. cada REQ tiene al menos una prueba que no está en rojo/saltada;
  3. la última verificación completa (.harness/last-verify.json) está en verde y corresponde
     exactamente al árbol de trabajo actual (huella) — si no, se ejecuta verify de nuevo.
Escribe passes=true, verified_at y verified_commit. Nunca toca otros campos.

  feature.py pass FEAT-ID
  feature.py list [--pending]
"""

from __future__ import annotations

import datetime as dt
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from harness_lib import (  # noqa: E402
    LAST_VERIFY,
    ROOT,
    discover_tests,
    head_sha,
    load_features,
    load_tasks,
    read_json,
    save_features,
    worktree_fingerprint,
)


def cmd_list(pending: bool) -> int:
    for f in load_features()["features"]:
        if pending and f["passes"]:
            continue
        mark = "✓" if f["passes"] else "○"
        print(f" {mark} {f['id']:<10} {f['priority']} {', '.join(f['req_ids']):<40} {f['description'][:70]}")
    return 0


def cmd_pass(fid: str) -> int:
    data = load_features()
    feat = next((f for f in data["features"] if f["id"] == fid), None)
    if feat is None:
        sys.exit(f"feature desconocida: {fid}")
    if feat["passes"]:
        print(f"{fid} ya tiene passes=true")
        return 0
    reqs = set(feat["req_ids"])
    errors: list[str] = []
    open_tasks = [t.id for t in load_tasks() if reqs & set(t.reqs) and not t.done]
    if open_tasks:
        errors.append(f"tareas pendientes que cubren sus REQ: {', '.join(open_tasks)}")
    tests = discover_tests()
    for r in sorted(reqs):
        green = [t for t in tests if r in t.reqs and not t.expected_fail]
        if not green:
            errors.append(f"{r}: no hay ninguna prueba en verde (sin xfail/skip) que lo referencie")
    if errors:
        print(f"✗ {fid} no puede marcarse:\n  " + "\n  ".join(errors), file=sys.stderr)
        return 1
    last = read_json(LAST_VERIFY) or {}
    if not (last.get("ok") and last.get("fingerprint") == worktree_fingerprint()):
        print("▶ la última verificación no corresponde al árbol actual: ejecutando verify…", flush=True)
        if subprocess.run([sys.executable, str(ROOT / "scripts/verify.py")], cwd=ROOT).returncode != 0:
            print(f"✗ verify en rojo: {fid} no se marca", file=sys.stderr)
            return 1
    sha = head_sha()
    if not sha:
        sys.exit("se necesita al menos un commit para registrar la evidencia")
    feat["passes"] = True
    feat["verified_at"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    feat["verified_commit"] = sha[:12]
    save_features(data)
    print(f"✓ {fid} passes=true (commit {sha[:12]}). Haz commit: chore(state): {fid} passes")
    return 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["pass"] and len(argv) == 2:
        return cmd_pass(argv[1])
    if argv[:1] == ["list"]:
        return cmd_list("--pending" in argv)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
