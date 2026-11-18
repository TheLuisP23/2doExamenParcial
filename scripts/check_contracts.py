#!/usr/bin/env python3
"""Valida los contratos OpenAPI (constitución III).

1. Validez estructural OpenAPI 3.1 (openapi-spec-validator).
2. Reglas de la casa:
   - existen GET /health/live y GET /health/ready (REQ-SYS-003);
   - toda respuesta 4xx/5xx usa application/problem+json (REQ-SYS-006);
   - cada operación tiene operationId único y un REQ-* en summary/description;
   - todos los REQ-* citados existen en las specs.

Uso: check_contracts.py [ruta/openapi.yaml ...]   (por defecto specs/*/contracts/openapi.yaml)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from harness_lib import REQ_RE, ROOT, load_requirements  # noqa: E402

try:
    import yaml
    from openapi_spec_validator import validate
    from openapi_spec_validator.readers import read_from_filename
except ImportError:  # pragma: no cover
    print("faltan dependencias: instala scripts/requirements-tools.txt (./init.sh lo hace)", file=sys.stderr)
    sys.exit(2)

METHODS = {"get", "put", "post", "delete", "patch", "head", "options"}


def resolve(spec: dict, obj: dict) -> dict:
    while isinstance(obj, dict) and "$ref" in obj:
        ref = obj["$ref"]
        node = spec
        for part in ref.lstrip("#/").split("/"):
            node = node[part]
        obj = node
    return obj


def house_rules(path: Path, spec: dict, reqs: set[str]) -> list[str]:
    errs: list[str] = []
    paths = spec.get("paths", {})
    for hp in ("/health/live", "/health/ready"):
        if "get" not in paths.get(hp, {}):
            errs.append(f"falta GET {hp}")
    op_ids: list[str] = []
    for p, item in paths.items():
        for method, op in item.items():
            if method not in METHODS:
                continue
            where = f"{method.upper()} {p}"
            oid = op.get("operationId")
            if not oid:
                errs.append(f"{where}: sin operationId")
            op_ids.append(oid)
            text = f"{op.get('summary', '')} {op.get('description', '')}"
            cited = REQ_RE.findall(text)
            if not cited:
                errs.append(f"{where}: summary/description no cita ningún REQ-*")
            for r in cited:
                if r not in reqs:
                    errs.append(f"{where}: cita REQ inexistente {r}")
            for code, resp in op.get("responses", {}).items():
                if str(code)[0] in "45" and not p.startswith("/health/"):  # /health/* usa Health (REQ-SYS-006)
                    content = resolve(spec, resp).get("content", {})
                    if "application/problem+json" not in content:
                        errs.append(f"{where} {code}: debe usar application/problem+json")
    dups = {o for o in op_ids if o and op_ids.count(o) > 1}
    for d in dups:
        errs.append(f"operationId duplicado: {d}")
    return [f"{path.relative_to(ROOT)}: {e}" for e in errs]


def main(argv: list[str]) -> int:
    files = [Path(a).resolve() for a in argv] or sorted(ROOT.glob("specs/*/contracts/openapi.yaml"))
    if not files:
        print("no hay contratos que validar")
        return 0
    reqs = set(load_requirements())
    errors: list[str] = []
    for f in files:
        try:
            spec_dict, _ = read_from_filename(str(f))
            validate(spec_dict)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{f.relative_to(ROOT)}: OpenAPI inválido: {str(exc).splitlines()[0]}")
            continue
        spec = yaml.safe_load(f.read_text(encoding="utf-8"))
        if not str(spec.get("openapi", "")).startswith("3.1"):
            errors.append(f"{f.relative_to(ROOT)}: se exige OpenAPI 3.1.x")
        errors += house_rules(f, spec, reqs)
        print(f"  · {f.relative_to(ROOT)}: {spec['info']['title']} v{spec['info']['version']}")
    if errors:
        print("\n".join("  ✗ " + e for e in errors), file=sys.stderr)
        return 1
    print(f"  ✓ {len(files)} contrato(s) válidos")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
