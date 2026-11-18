#!/usr/bin/env python3
"""Hook PostToolUse (Edit|Write|MultiEdit) — subsistema de Verificación (bucle rápido).

Formatea y lintea el archivo editado según su tipo. Si queda un error, sale con código 2 y el
mensaje llega al agente para que lo corrija en el acto.

  .py (service-a)          uv run ruff format + ruff check --fix
  .py (scripts, tests/)    ruff (de .venv-tools) format + check --fix
  .ts/.tsx/.js/.css/.json  prettier --write (+ eslint --fix en ts/tsx/js) si hay node_modules
  .tf / .tftest.hcl        terraform fmt
  deploy/k8s/*.yaml        kubeconform -strict (si está instalado)
  openapi.yaml             scripts/check_contracts.py
  feature_list.json        scripts/check_feature_list.py
  specs/*/tasks.md         scripts/task.py lint
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
TOOLS_BIN = ROOT / ".venv-tools" / ("Scripts" if os.name == "nt" else "bin")
PY = str(next((p for p in (TOOLS_BIN / "python.exe", TOOLS_BIN / "python") if p.exists()), sys.executable))
problems: list[str] = []


def tool(name: str) -> str | None:
    for cand in (TOOLS_BIN / f"{name}.exe", TOOLS_BIN / name):
        if cand.exists():
            return str(cand)
    return shutil.which(name)


def run(cmd: list[str], cwd: Path, label: str, report: bool = True) -> None:
    exe = shutil.which(cmd[0]) or cmd[0]
    try:
        r = subprocess.run(
            [exe, *cmd[1:]], cwd=cwd, capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace"
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        problems.append(f"[{label}] no se pudo ejecutar: {exc}")
        return
    if r.returncode != 0 and report:
        out = (r.stdout + r.stderr).strip().splitlines()
        problems.append(f"[{label}]\n" + "\n".join(out[-25:]))


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        sys.exit(0)
    ti = payload.get("tool_input") or {}
    raw = ti.get("file_path") or ti.get("notebook_path")
    if not raw:
        sys.exit(0)
    p = Path(native(raw)).resolve()
    if not p.exists():
        sys.exit(0)
    try:
        rel = p.relative_to(ROOT).as_posix()
    except ValueError:
        sys.exit(0)
    sa, sb, fe = ROOT / "services/service-a", ROOT / "services/service-b", ROOT / "frontend"

    if p.suffix == ".py":
        if rel.startswith("services/service-a/") and shutil.which("uv") and (sa / "pyproject.toml").exists():
            run(["uv", "run", "ruff", "format", str(p)], sa, "ruff format", report=False)
            run(["uv", "run", "ruff", "check", "--fix", str(p)], sa, "ruff check")
        elif ruff := tool("ruff"):
            run([ruff, "format", str(p)], ROOT, "ruff format", report=False)
            run([ruff, "check", "--fix", str(p)], ROOT, "ruff check")
    elif p.suffix in {".ts", ".tsx", ".js", ".mjs", ".cjs", ".css", ".json"} and rel != "feature_list.json":
        for base in (sb, fe):
            if rel.startswith(base.relative_to(ROOT).as_posix() + "/") and (base / "node_modules").exists():
                run(["npx", "--no-install", "prettier", "--write", str(p)], base, "prettier", report=False)
                if p.suffix in {".ts", ".tsx", ".js", ".mjs", ".cjs"}:
                    run(["npx", "--no-install", "eslint", "--fix", str(p)], base, "eslint")
    elif p.suffix in {".tf", ".hcl"} and shutil.which("terraform"):
        run(["terraform", "fmt", str(p)], ROOT, "terraform fmt")
    elif rel.startswith("deploy/k8s/") and p.suffix in {".yaml", ".yml"} and shutil.which("kubeconform"):
        run(
            ["kubeconform", "-strict", "-summary", "-kubernetes-version", os.environ.get("K8S_SCHEMA_VERSION", "1.36.0"), str(p)],
            ROOT,
            "kubeconform",
        )

    if p.name == "openapi.yaml":
        run([PY, "scripts/check_contracts.py", str(p)], ROOT, "check_contracts")
    if rel == "feature_list.json":
        run([PY, "scripts/check_feature_list.py"], ROOT, "check_feature_list")
    if rel.startswith("specs/") and p.name in {"tasks.md", "spec.md"}:
        run([PY, "scripts/task.py", "lint"], ROOT, "task lint")

    if problems:
        print(f"post_edit: problemas en {rel}:\n" + "\n\n".join(problems), file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
