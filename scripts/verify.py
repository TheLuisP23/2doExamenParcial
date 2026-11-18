#!/usr/bin/env python3
"""`make verify`: la única definición de "hecho" (constitución IV.4).

Pasos (en orden):
  harness    — formato de tareas, feature_list.json, trazabilidad
  contracts  — openapi.yaml válidos + reglas de la casa
  service-a  — ruff, ruff format, mypy, pytest unit/integration/contract + cobertura ≥ 80 %
  service-b  — npm run lint / typecheck / test:unit / test:integration / test:contract
  frontend   — ídem
  cross      — pytest de tests/system, tests/platform, tests/smoke
  terraform  — fmt -check, init -backend=false, validate, test
  k8s        — kubeconform -strict sobre deploy/k8s
  eksctl     — eksctl create cluster --dry-run sobre el ClusterConfig renderizado
  secrets    — gitleaks

Un componente cuyo manifiesto aún no existe se marca SKIP; si su tarea scaffold está [x], es FAIL
(ADR-0008). Resultado en .harness/last-verify.json (lo usan task.py, el hook Stop y end-session).

Uso: verify.py [--only paso,paso] [--release] [--keep-going]
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from harness_lib import LAST_VERIFY, ROOT, head_sha, load_tasks, worktree_fingerprint, write_json  # noqa: E402

PY = sys.executable
K8S_VERSION = os.environ.get("K8S_SCHEMA_VERSION", "1.36.0")
KUBECONFORM_IMAGE = "ghcr.io/yannh/kubeconform:v0.6.7"
GITLEAKS_IMAGE = "zricethezav/gitleaks:v8.21.2"
IS_WIN = os.name == "nt"

PASS, FAIL, SKIP, WARN = "PASS", "FAIL", "SKIP", "WARN"
results: list[tuple[str, str, str, float]] = []


def which(cmd: str) -> str | None:
    return shutil.which(cmd)


def run(
    name: str,
    cmd: list[str] | str,
    cwd: Path = ROOT,
    env: dict | None = None,
    ok_codes: tuple[int, ...] = (0,),
    skip_codes: tuple[int, ...] = (),
) -> str:
    print(f"\n▶ [{name}] {cmd if isinstance(cmd, str) else ' '.join(cmd)}", flush=True)
    t0 = time.time()
    full_env = {**os.environ, **(env or {})}
    try:
        if isinstance(cmd, list) and IS_WIN:
            exe = shutil.which(cmd[0])
            if exe:
                cmd = [exe, *cmd[1:]]
        proc = subprocess.run(cmd, cwd=cwd, env=full_env, shell=isinstance(cmd, str))
        code = proc.returncode
    except FileNotFoundError as exc:
        results.append((name, FAIL, f"no encontrado: {exc.filename}", time.time() - t0))
        return FAIL
    dur = time.time() - t0
    if code in ok_codes:
        status, note = PASS, ""
    elif code in skip_codes:
        status, note = SKIP, f"código {code} (sin pruebas)"
    else:
        status, note = FAIL, f"código {code}"
    results.append((name, status, note, dur))
    return status


def record(name: str, status: str, note: str) -> None:
    print(f"\n▶ [{name}] {status}: {note}", flush=True)
    results.append((name, status, note, 0.0))


def scaffold_done(task_id: str) -> bool:
    assume = {x.strip() for x in os.environ.get("HARNESS_ASSUME_DONE", "").split(",")}
    return any(t.id == task_id and (t.done or t.id in assume) for t in load_tasks())


def missing(name: str, manifest: Path, scaffold_task: str) -> bool:
    """True si hay que saltar el componente; registra SKIP o FAIL."""
    if manifest.exists():
        return False
    if scaffold_done(scaffold_task):
        record(name, FAIL, f"{manifest.relative_to(ROOT)} no existe pero {scaffold_task} está hecha")
    else:
        record(name, SKIP, f"{manifest.relative_to(ROOT)} aún no existe ({scaffold_task} pendiente)")
    return True


def docker_ok() -> bool:
    if not which("docker"):
        return False
    return subprocess.run(["docker", "info"], capture_output=True).returncode == 0


# ----------------------------------------------------------------------------- pasos
def step_harness(release: bool) -> None:
    run("harness:tasks", [PY, "scripts/task.py", "lint"])
    run("harness:feature-list", [PY, "scripts/check_feature_list.py"])
    run("harness:traceability", [PY, "scripts/check_traceability.py", *(["--all", "--require-passing"] if release else [])])


def step_contracts(release: bool) -> None:
    run("contracts", [PY, "scripts/check_contracts.py"])


def step_service_a(release: bool) -> None:
    d = ROOT / "services/service-a"
    if missing("service-a", d / "pyproject.toml", "TASK-A-01"):
        return
    if not which("uv"):
        record("service-a", FAIL, "uv no instalado (pip install uv)")
        return
    env = {"COVERAGE_FILE": str(ROOT / ".harness/.coverage-a")}
    run("service-a:lint", ["uv", "run", "ruff", "check", "."], cwd=d)
    run("service-a:format", ["uv", "run", "ruff", "format", "--check", "."], cwd=d)
    run("service-a:typecheck", ["uv", "run", "mypy", "src"], cwd=d)
    run("service-a:unit", ["uv", "run", "pytest", "tests/unit", "--cov=books", "--cov-report="], cwd=d, env=env, skip_codes=(5,))
    if (d / "tests/integration").exists():
        if not docker_ok():
            record("service-a:integration", FAIL, "Docker no disponible (Testcontainers)")
        else:
            run(
                "service-a:integration",
                ["uv", "run", "pytest", "tests/integration", "--cov=books", "--cov-append", "--cov-report="],
                cwd=d,
                env=env,
                skip_codes=(5,),
            )
    # antes de TASK-A-03 aún no hay código que cubrir: un umbral no alcanzado se reporta como SKIP
    cov_skip = () if scaffold_done("TASK-A-03") else (1,)
    run("service-a:coverage", ["uv", "run", "coverage", "report", "--fail-under=80"], cwd=d, env=env, skip_codes=cov_skip)
    if (d / "tests/contract").exists():
        run("service-a:contract", ["uv", "run", "pytest", "tests/contract"], cwd=d, skip_codes=(5,))


def _npm_component(name: str, d: Path, scaffold: str) -> None:
    if missing(name, d / "package.json", scaffold):
        return
    if not (d / "node_modules").exists():
        record(name, FAIL, "node_modules no existe: ejecuta ./init.sh (npm ci)")
        return
    for script in ("lint", "typecheck", "test:unit", "test:integration", "test:contract"):
        if script == "test:integration" and not docker_ok():
            record(f"{name}:{script}", FAIL, "Docker no disponible (Testcontainers)")
            continue
        run(f"{name}:{script}", ["npm", "run", "--silent", script], cwd=d)


def step_service_b(release: bool) -> None:
    _npm_component("service-b", ROOT / "services/service-b", "TASK-B-01")


def step_frontend(release: bool) -> None:
    _npm_component("frontend", ROOT / "frontend", "TASK-F-01")


def step_cross(release: bool) -> None:
    dirs = [p for p in ("tests/system", "tests/platform", "tests/smoke") if any((ROOT / p).glob("test_*.py"))]
    if not dirs:
        record("cross-tests", SKIP, "aún no hay pruebas en tests/system|platform|smoke")
        return
    run("cross-tests", [PY, "-m", "pytest", "-q", *dirs], skip_codes=(5,))


def step_terraform(release: bool) -> None:
    d = ROOT / "deploy/terraform"
    if not list(d.glob("*.tf")):
        record("terraform", SKIP, "deploy/terraform sin *.tf (TASK-P-04 pendiente)")
        return
    if not which("terraform"):
        record("terraform", FAIL, "terraform no instalado")
        return
    run("terraform:fmt", ["terraform", "fmt", "-check", "-recursive"], cwd=d)
    run("terraform:init", ["terraform", "init", "-backend=false", "-input=false", "-no-color"], cwd=d)
    run("terraform:validate", ["terraform", "validate", "-no-color"], cwd=d)
    if list((d / "tests").glob("*.tftest.hcl")):
        run("terraform:test", ["terraform", "test", "-no-color"], cwd=d)


def step_k8s(release: bool) -> None:
    d = ROOT / "deploy/k8s"
    files = [p for p in d.rglob("*.y*ml")]
    if not files:
        record("k8s:kubeconform", SKIP, "deploy/k8s sin manifiestos (TASK-P-08 pendiente)")
        return
    args = ["-strict", "-summary", "-kubernetes-version", K8S_VERSION]
    if which("kubeconform"):
        run("k8s:kubeconform", ["kubeconform", *args, str(d)])
    elif docker_ok():
        run("k8s:kubeconform", ["docker", "run", "--rm", "-v", f"{d}:/k8s:ro", KUBECONFORM_IMAGE, *args, "/k8s"])
    else:
        record("k8s:kubeconform", FAIL, "kubeconform no instalado y Docker no disponible")


def step_eksctl(release: bool) -> None:
    cfg = ROOT / "deploy/eksctl/cluster.yaml"
    if not cfg.exists():
        record("eksctl:dry-run", SKIP, "deploy/eksctl/cluster.yaml no existe (TASK-P-06 pendiente)")
        return
    if not which("eksctl") or not which("aws"):
        record("eksctl:dry-run", SKIP, "eksctl/aws no instalados")
        return
    sts = subprocess.run(
        [
            "aws",
            "sts",
            "get-caller-identity",
            "--query",
            "Account",
            "--output",
            "text",
            "--cli-connect-timeout",
            "5",
            "--cli-read-timeout",
            "10",
        ],
        capture_output=True,
        text=True,
    )
    if sts.returncode != 0:
        record("eksctl:dry-run", SKIP, "sin credenciales AWS (el dry-run consulta la API)")
        return
    rendered = ROOT / ".harness/cluster.rendered.yaml"
    rendered.parent.mkdir(exist_ok=True)
    rendered.write_text(cfg.read_text(encoding="utf-8").replace("${AWS_ACCOUNT_ID}", sts.stdout.strip()), encoding="utf-8")
    proc_status = run("eksctl:dry-run", ["eksctl", "create", "cluster", "-f", str(rendered), "--dry-run"])
    if proc_status == PASS:
        rendered.unlink(missing_ok=True)


def step_secrets(release: bool) -> None:
    args = ["detect", "--no-git", "--redact", "--no-banner", "-c", ".gitleaks.toml"]
    if which("gitleaks"):
        run("secrets:gitleaks", ["gitleaks", *args, "--source", "."])
    elif docker_ok():
        run(
            "secrets:gitleaks",
            ["docker", "run", "--rm", "-v", f"{ROOT}:/repo:ro", "-w", "/repo", GITLEAKS_IMAGE, *args, "--source", "/repo"],
        )
    else:
        record("secrets:gitleaks", WARN, "gitleaks no instalado y Docker no disponible (CI lo ejecuta)")


STEPS = {
    "harness": step_harness,
    "contracts": step_contracts,
    "service-a": step_service_a,
    "service-b": step_service_b,
    "frontend": step_frontend,
    "cross": step_cross,
    "terraform": step_terraform,
    "k8s": step_k8s,
    "eksctl": step_eksctl,
    "secrets": step_secrets,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="pasos separados por coma: " + ",".join(STEPS))
    ap.add_argument("--release", action="store_true", help="trazabilidad completa (todos los REQ con test en verde)")
    args = ap.parse_args()
    selected = [s.strip() for s in args.only.split(",") if s.strip()] or list(STEPS)
    unknown = [s for s in selected if s not in STEPS]
    if unknown:
        print(f"pasos desconocidos: {unknown}", file=sys.stderr)
        return 2

    fingerprint = worktree_fingerprint()
    t0 = time.time()
    for s in selected:
        STEPS[s](args.release)

    print("\n" + "═" * 72 + "\n RESUMEN make verify\n" + "═" * 72)
    for name, status, note, dur in results:
        icon = {"PASS": "✓", "FAIL": "✗", "SKIP": "·", "WARN": "!"}[status]
        print(f" {icon} {status:<4} {name:<28} {dur:6.1f}s  {note}")
    failed = [r for r in results if r[1] == FAIL]
    ok = not failed
    print("═" * 72)
    print(
        f" {'VERDE' if ok else 'ROJO'} · {sum(r[1] == PASS for r in results)} pass, {len(failed)} fail, "
        f"{sum(r[1] == SKIP for r in results)} skip, {sum(r[1] == WARN for r in results)} warn · {time.time() - t0:.0f}s"
    )

    if not args.only:  # solo una verificación completa cuenta como evidencia
        write_json(
            LAST_VERIFY,
            {
                "ok": ok,
                "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "commit": head_sha(),
                "fingerprint": fingerprint,
                "release": args.release,
                "assume_done": os.environ.get("HARNESS_ASSUME_DONE", ""),
                "steps": [{"name": n, "status": s, "note": no} for n, s, no, _ in results],
            },
        )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
