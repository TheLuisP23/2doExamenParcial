"""Librería compartida del harness: parseo de specs, tareas, features y pruebas.

Sin dependencias externas (solo stdlib) para que hooks y scripts arranquen rápido en cualquier
máquina. Ver docs/harness.md.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Consolas de Windows (cp1252) no imprimen ✓/✗/→: forzar UTF-8 en todos los scripts del harness.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
SPECS = ROOT / "specs"
HARNESS_DIR = ROOT / ".harness"
FEATURE_LIST = ROOT / "feature_list.json"
CURRENT_TASK = HARNESS_DIR / "current-task.json"
LAST_VERIFY = HARNESS_DIR / "last-verify.json"

REQ_RE = re.compile(r"\bREQ-(?:SYS|A|B|F|P)-\d{3}\b")
REQ_HEADING_RE = re.compile(r"^###\s+(REQ-(?:SYS|A|B|F|P)-\d{3})\s+[—-]\s+(.+?)\s*\((P[1-3])\)\s*$", re.M)
TASK_LINE_RE = re.compile(r"^- \[( |x|X)\] \*\*(TASK-[A-Z]+-\d{2})\*\*(\s+\[P\])?\s+[—-]\s+(.+?)\s*$")
TASK_FIELD_RE = re.compile(r"^\s{2}- (Tipo|Depende de|REQ|Archivos|Hecho cuando):\s*(.*)$")
TASK_TYPES = {"scaffold", "test", "impl", "ops"}

# Pruebas que NO cuentan como evidencia de "pasa": fallo esperado (TDD en rojo, ADR-0008) o saltadas.
XFAIL_PY = re.compile(r"xfail")
XFAIL_TS = re.compile(r"\.(fails|fail|skip|todo)\b")

SKIP_DIRS = {
    "node_modules",
    ".venv",
    ".venv-tools",
    ".git",
    "dist",
    "build",
    ".terraform",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "coverage",
    ".harness",
}


# --------------------------------------------------------------------------- specs
@dataclass
class Requirement:
    id: str
    title: str
    priority: str
    spec: str


def load_requirements() -> dict[str, Requirement]:
    reqs: dict[str, Requirement] = {}
    for spec in sorted(SPECS.glob("*/spec.md")):
        text = spec.read_text(encoding="utf-8")
        for m in REQ_HEADING_RE.finditer(text):
            rid, title, prio = m.group(1), m.group(2), m.group(3)
            if rid in reqs:
                raise ValueError(f"REQ duplicado {rid} en {spec} y {reqs[rid].spec}")
            reqs[rid] = Requirement(rid, title, prio, spec.parent.name)
    return reqs


# --------------------------------------------------------------------------- tasks
@dataclass
class Task:
    id: str
    title: str
    done: bool
    parallel: bool
    spec: str
    file: Path
    line: int
    type: str = ""
    deps: list[str] = field(default_factory=list)
    reqs: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    done_when: str = ""


def _split_list(value: str) -> list[str]:
    value = value.strip()
    if value in {"", "—", "-"}:
        return []
    return [v.strip() for v in value.split(",") if v.strip() and v.strip() not in {"—", "-"}]


def load_tasks() -> list[Task]:
    tasks: list[Task] = []
    for tf in sorted(SPECS.glob("*/tasks.md")):
        current: Task | None = None
        for i, line in enumerate(tf.read_text(encoding="utf-8").splitlines(), start=1):
            m = TASK_LINE_RE.match(line)
            if m:
                current = Task(
                    id=m.group(2),
                    title=m.group(4),
                    done=m.group(1).lower() == "x",
                    parallel=bool(m.group(3)),
                    spec=tf.parent.name,
                    file=tf,
                    line=i,
                )
                tasks.append(current)
                continue
            f = TASK_FIELD_RE.match(line)
            if f and current is not None:
                key, val = f.group(1), f.group(2)
                if key == "Tipo":
                    current.type = val.strip()
                elif key == "Depende de":
                    current.deps = _split_list(val)
                elif key == "REQ":
                    current.reqs = _split_list(val)
                elif key == "Archivos":
                    current.files = re.findall(r"`([^`]+)`", val)
                elif key == "Hecho cuando":
                    current.done_when = val.strip()
    return tasks


def lint_tasks(tasks: list[Task], reqs: dict[str, Requirement]) -> list[str]:
    errors: list[str] = []
    ids = [t.id for t in tasks]
    known = set(ids)
    for dup in {i for i in ids if ids.count(i) > 1}:
        errors.append(f"TASK duplicada: {dup}")
    for t in tasks:
        where = f"{t.file.relative_to(ROOT)}:{t.line} {t.id}"
        if t.type not in TASK_TYPES:
            errors.append(f"{where}: 'Tipo' debe ser uno de {sorted(TASK_TYPES)} (es '{t.type}')")
        if not t.files:
            errors.append(f"{where}: sin 'Archivos' permitidos")
        if not t.done_when:
            errors.append(f"{where}: sin 'Hecho cuando'")
        if t.type in {"test", "impl"} and not t.reqs:
            errors.append(f"{where}: una tarea {t.type} debe cubrir al menos un REQ")
        for r in t.reqs:
            if r not in reqs:
                errors.append(f"{where}: REQ desconocido {r}")
        for d in t.deps:
            if d not in known:
                errors.append(f"{where}: dependencia desconocida {d}")
    # ciclos
    graph = {t.id: t.deps for t in tasks}
    state: dict[str, int] = {}

    def visit(n: str, stack: list[str]) -> None:
        if state.get(n) == 1:
            errors.append("ciclo de dependencias: " + " -> ".join(stack + [n]))
            return
        if state.get(n) == 2:
            return
        state[n] = 1
        for d in graph.get(n, []):
            visit(d, stack + [n])
        state[n] = 2

    for n in graph:
        visit(n, [])
    return errors


def set_task_done(task: Task, done: bool = True) -> None:
    lines = task.file.read_text(encoding="utf-8").splitlines(keepends=True)
    idx = task.line - 1
    mark = "x" if done else " "
    lines[idx] = re.sub(r"^- \[( |x|X)\]", f"- [{mark}]", lines[idx], count=1)
    task.file.write_text("".join(lines), encoding="utf-8")


def glob_to_regex(pattern: str) -> re.Pattern[str]:
    out = ""
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if pattern.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
            continue
        if pattern.startswith("**", i):
            out += ".*"
            i += 2
            continue
        if c == "*":
            out += "[^/]*"
        elif c == "?":
            out += "[^/]"
        else:
            out += re.escape(c)
        i += 1
    return re.compile("^" + out + "$")


def path_allowed(rel_path: str, patterns: list[str]) -> bool:
    rel_path = rel_path.replace("\\", "/")
    return any(glob_to_regex(p).match(rel_path) for p in patterns)


# --------------------------------------------------------------------------- tests
@dataclass
class TestCase:
    file: str
    name: str
    reqs: list[str]
    expected_fail: bool


def _iter_files(patterns: tuple[str, ...]) -> list[Path]:
    found: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if any(re.fullmatch(p, fn) for p in patterns):
                found.append(Path(dirpath) / fn)
    return sorted(found)


def _py_tests(path: Path) -> list[TestCase]:
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return [TestCase(str(path.relative_to(ROOT)), "<syntax-error>", [], False)]
    module_reqs: list[str] = []
    module_xfail = False
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "pytestmark" for t in node.targets):
            seg = ast.get_source_segment(src, node) or ""
            module_reqs += REQ_RE.findall(seg)
            module_xfail |= bool(XFAIL_PY.search(seg))
    cases: list[TestCase] = []

    def deco_text(n: ast.AST) -> str:
        return "\n".join(ast.get_source_segment(src, d) or "" for d in getattr(n, "decorator_list", []))

    def handle_fn(fn: ast.FunctionDef | ast.AsyncFunctionDef, inherited: list[str], inh_xfail: bool, prefix: str) -> None:
        if not fn.name.startswith("test"):
            return
        text = deco_text(fn) + "\n" + (ast.get_docstring(fn) or "")
        reqs = sorted(set(inherited + module_reqs + REQ_RE.findall(text)))
        xf = inh_xfail or module_xfail or bool(XFAIL_PY.search(deco_text(fn)))
        cases.append(TestCase(str(path.relative_to(ROOT)).replace("\\", "/"), prefix + fn.name, reqs, xf))

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            handle_fn(node, [], False, "")
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            ctext = deco_text(node) + "\n" + (ast.get_docstring(node) or "")
            creqs = REQ_RE.findall(ctext)
            cx = bool(XFAIL_PY.search(deco_text(node)))
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    handle_fn(sub, creqs, cx, node.name + "::")
    return cases


_TS_CALL = re.compile(r"\b(describe|it|test)((?:\.\w+)*)\s*\(\s*(['\"`])((?:\\.|(?!\3).)*)\3", re.S)


def _ts_tests(path: Path) -> list[TestCase]:
    src = path.read_text(encoding="utf-8")
    cases: list[TestCase] = []
    describe_reqs: list[str] = []
    for m in _TS_CALL.finditer(src):
        kind, mods, title = m.group(1), m.group(2), m.group(4)
        if kind == "describe":
            describe_reqs = REQ_RE.findall(title)
            continue
        # test.fail() dentro del cuerpo (Playwright) se detecta por proximidad
        body = src[m.end() : m.end() + 400]
        xf = bool(XFAIL_TS.search(mods)) or "test.fail()" in body
        reqs = sorted(set(REQ_RE.findall(title) + describe_reqs))
        cases.append(TestCase(str(path.relative_to(ROOT)).replace("\\", "/"), title, reqs, xf))
    return cases


_TF_RUN = re.compile(r'^\s*run\s+"([^"]+)"\s*\{', re.M)


def _tf_tests(path: Path) -> list[TestCase]:
    src = path.read_text(encoding="utf-8")
    cases: list[TestCase] = []
    lines = src.splitlines()
    for m in _TF_RUN.finditer(src):
        lineno = src[: m.start()].count("\n")
        comments = []
        j = lineno - 1
        while j >= 0 and lines[j].strip().startswith(("#", "//")):
            comments.append(lines[j])
            j -= 1
        reqs = sorted(set(REQ_RE.findall(m.group(1) + "\n".join(comments))))
        cases.append(TestCase(str(path.relative_to(ROOT)).replace("\\", "/"), m.group(1), reqs, False))
    return cases


def discover_tests() -> list[TestCase]:
    cases: list[TestCase] = []
    for p in _iter_files((r"test_.*\.py", r".*_test\.py")):
        cases += _py_tests(p)
    for p in _iter_files((r".*\.(test|spec)\.(ts|tsx|js|mjs)",)):
        cases += _ts_tests(p)
    for p in _iter_files((r".*\.tftest\.hcl",)):
        cases += _tf_tests(p)
    return cases


# --------------------------------------------------------------------------- features
def load_features(path: Path = FEATURE_LIST) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_features(data: dict, path: Path = FEATURE_LIST) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- git / estado
def git(*args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", check=check
    )


def head_sha() -> str | None:
    r = git("rev-parse", "HEAD")
    return r.stdout.strip() if r.returncode == 0 else None


def changed_files(since: str | None = None) -> list[str]:
    files: set[str] = set()
    if since:
        r = git("diff", "--name-only", since)
        files |= {f for f in r.stdout.splitlines() if f}
    r = git("status", "--porcelain", "--untracked-files=all")
    for line in r.stdout.splitlines():
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        files.add(path.strip('"'))
    return sorted(files)


def worktree_fingerprint() -> str:
    """Huella del árbol de trabajo (HEAD + diff + no rastreados) para cachear verify."""
    h = hashlib.sha256()
    h.update((head_sha() or "no-head").encode())
    h.update(git("diff", "HEAD").stdout.encode("utf-8", "replace"))
    for f in sorted(git("ls-files", "--others", "--exclude-standard").stdout.splitlines()):
        p = ROOT / f
        h.update(f.encode())
        if p.is_file():
            h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


def read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
