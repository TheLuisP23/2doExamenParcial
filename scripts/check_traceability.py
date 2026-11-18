#!/usr/bin/env python3
"""Trazabilidad REQ <-> test (constitución IV.2, ADR-0008).

Falla si:
  1. una prueba no referencia ningún REQ-*  (siempre);
  2. una prueba referencia un REQ-* que no existe en specs/*/spec.md  (siempre);
  3. un REQ *en alcance* no tiene ninguna prueba que lo referencie.
     En alcance = REQ de tareas marcadas [x] + REQ de features con passes=true
     (+ tareas en HARNESS_ASSUME_DONE). Con --all, todos los REQ.

Uso: check_traceability.py [--all] [--report] [--req REQ-A-001 ...] [--require-passing]
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from harness_lib import discover_tests, load_features, load_requirements, load_tasks  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="exigir test para todos los REQ (release)")
    ap.add_argument("--report", action="store_true", help="imprimir matriz REQ -> tests")
    ap.add_argument("--req", nargs="*", default=None, help="limitar el chequeo a estos REQ")
    ap.add_argument("--require-passing", action="store_true", help="los REQ deben tener al menos un test que no sea xfail/skip")
    args = ap.parse_args()

    reqs = load_requirements()
    tests = discover_tests()
    tasks = load_tasks()
    errors: list[str] = []

    by_req: dict[str, list] = defaultdict(list)
    for t in tests:
        if not t.reqs:
            errors.append(f"test sin REQ: {t.file}::{t.name}")
        for r in t.reqs:
            if r not in reqs:
                errors.append(f"test referencia REQ inexistente {r}: {t.file}::{t.name}")
            by_req[r].append(t)

    assume = {x.strip() for x in os.environ.get("HARNESS_ASSUME_DONE", "").split(",") if x.strip()}
    if args.req is not None:
        scope = set(args.req)
        scope_reason = "--req"
    elif args.all:
        scope = set(reqs)
        scope_reason = "--all"
    else:
        scope = set()
        for t in tasks:
            if t.done or t.id in assume:
                scope |= set(t.reqs)
        try:
            for f in load_features().get("features", []):
                if f.get("passes"):
                    scope |= set(f.get("req_ids", []))
        except (OSError, ValueError):
            pass
        scope_reason = "tareas [x] + features passes=true"

    for r in sorted(scope):
        if r not in reqs:
            errors.append(f"REQ en alcance desconocido: {r}")
            continue
        cases = by_req.get(r, [])
        if not cases:
            errors.append(f"REQ sin test: {r} ({reqs[r].spec}) — {reqs[r].title}")
        elif args.require_passing and all(c.expected_fail for c in cases):
            errors.append(f"REQ solo con tests en rojo/saltados: {r}")

    if args.report:
        print(f"{'REQ':<12} {'P':<3} {'tests':>5}  {'rojo':>4}  spec")
        for rid in sorted(reqs):
            cs = by_req.get(rid, [])
            red = sum(1 for c in cs if c.expected_fail)
            mark = "*" if rid in scope else " "
            print(f"{rid:<12}{mark}{reqs[rid].priority:<3} {len(cs):>5}  {red:>4}  {reqs[rid].spec}")
        print("(* = en alcance)")

    covered = sum(1 for r in reqs if by_req.get(r))
    print(f"trazabilidad: {len(reqs)} REQ, {len(tests)} tests, {covered} REQ con test, {len(scope)} en alcance ({scope_reason})")
    if errors:
        print("\n".join("  ✗ " + e for e in errors), file=sys.stderr)
        return 1
    print("  ✓ trazabilidad OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
