#!/usr/bin/env python3
"""Valida feature_list.json (subsistema de Estado, constitución VIII.4).

1. Esquema JSON (scripts/feature_list.schema.json).
2. ids únicos; todo req_id existe en las specs; todo REQ de las specs está en alguna feature.
3. Append-only frente a una base git (por defecto HEAD; CI usa la rama destino):
   ninguna entrada de la base puede desaparecer ni cambiar sus campos inmutables
   (id, component, priority, req_ids, description, steps). Solo cambian passes/verified_*.

Uso: check_feature_list.py [--base REF] [--no-base]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from harness_lib import FEATURE_LIST, ROOT, git, load_requirements  # noqa: E402

IMMUTABLE = ("id", "component", "priority", "req_ids", "description", "steps")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get("FEATURE_BASE", "HEAD"))
    ap.add_argument("--no-base", action="store_true")
    args = ap.parse_args()

    errors: list[str] = []
    try:
        data = json.loads(FEATURE_LIST.read_text(encoding="utf-8"))
    except ValueError as exc:
        print(f"  ✗ feature_list.json no es JSON válido: {exc}", file=sys.stderr)
        return 1

    try:
        import jsonschema

        schema = json.loads((ROOT / "scripts/feature_list.schema.json").read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        for e in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
            errors.append(f"esquema: {'/'.join(map(str, e.path)) or '<raíz>'}: {e.message}")
    except ImportError:
        print("  ! jsonschema no instalado: se omite la validación de esquema", file=sys.stderr)

    features = data.get("features", [])
    ids = [f.get("id") for f in features]
    for d in sorted({i for i in ids if ids.count(i) > 1}):
        errors.append(f"id duplicado: {d}")

    reqs = load_requirements()
    covered: set[str] = set()
    for f in features:
        for r in f.get("req_ids", []):
            covered.add(r)
            if r not in reqs:
                errors.append(f"{f.get('id')}: req_id inexistente en specs: {r}")
    for r in sorted(set(reqs) - covered):
        errors.append(f"REQ sin feature: {r} ({reqs[r].spec})")

    if not args.no_base:
        base = git("show", f"{args.base}:feature_list.json")
        if base.returncode == 0:
            try:
                old = {f["id"]: f for f in json.loads(base.stdout).get("features", [])}
            except (ValueError, KeyError):
                old = {}
            new = {f.get("id"): f for f in features}
            for fid, of in old.items():
                nf = new.get(fid)
                if nf is None:
                    errors.append(f"entrada eliminada respecto a {args.base}: {fid} (prohibido)")
                    continue
                for k in IMMUTABLE:
                    if of.get(k) != nf.get(k):
                        errors.append(f"{fid}: campo inmutable '{k}' modificado respecto a {args.base} (prohibido)")
            pos_old = [i for i in old]
            pos_new = [f.get("id") for f in features if f.get("id") in old]
            if pos_old != pos_new:
                errors.append("las entradas existentes cambiaron de orden (append-only: añade al final)")
        else:
            print(f"  · sin {args.base}:feature_list.json en git: se omite el chequeo append-only")

    passing = sum(1 for f in features if f.get("passes"))
    print(f"feature_list: {len(features)} features, {passing} con passes=true, {len(covered)} REQ cubiertos")
    if errors:
        print("\n".join("  ✗ " + e for e in errors), file=sys.stderr)
        return 1
    print("  ✓ feature_list OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
