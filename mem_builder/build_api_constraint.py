#!/usr/bin/env python3
"""
Build API constraints from GenesisAgent runtime failures.

Pipeline (adapted for rag_demo):
1) Load prompt tasks from JSON.
2) For each prompt: call GenesisAgent.solve() → save generated code → execute via subprocess → capture stderr.
3) Parse error events from stderr (regex → LLM fallback).
4) Map error events to API IDs in genesis_api_index.json.
5) Generate constraints (judge LLM optional) and aggregate.
6) Write api_constraint.json.

Usage:
  python build_api_constraint.py --run-agent --judge-provider gemini --judge-api-key YOUR_KEY
  python build_api_constraint.py --no-run-agent --logs-file path/to/stderr.log
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# 确保能 import rag_demo 根目录和 mem_builder 下的模块
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAG_DEMO_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, RAG_DEMO_ROOT)
sys.path.insert(0, SCRIPT_DIR)


def _read_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1B\[[0-9;]*[A-Za-z]", "", text or "")


# ================= Data Classes =================
@dataclass
class ErrorEvent:
    error_type: str
    error_message: str
    traceback_excerpt: str
    raw_line: str
    confidence: str


@dataclass
class MappedEvent:
    api_id: str
    error_type: str
    error_message: str
    traceback_excerpt: str
    raw_line: str
    prompt_id: str
    prompt_query: str
    confidence: str
    inferred_symbol: str


# ================= Judge LLM =================
class JudgeLLM:
    def __init__(
        self,
        provider: str = "none",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.provider = (provider or "none").lower()
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.client = None
        self.genai_types = None
        self.enabled = False

        if self.provider == "none":
            return
        if self.provider == "openai":
            try:
                from openai import OpenAI

                self.client = OpenAI(api_key=api_key, base_url=base_url)
                self.model = self.model or "gpt-4o-mini"
                self.enabled = True
            except Exception as e:
                print(f"[JudgeLLM] OpenAI init failed, fallback heuristic: {e}")
        elif self.provider == "gemini":
            try:
                from google import genai
                from google.genai import types

                self.client = genai.Client(api_key=api_key)
                self.genai_types = types
                self.model = self.model or "gemini-2.0-flash"
                self.enabled = True
            except Exception as e:
                print(f"[JudgeLLM] Gemini init failed, fallback heuristic: {e}")
        else:
            print(f"[JudgeLLM] Unsupported provider '{provider}', fallback heuristic.")

    def _ask_openai(self, system_prompt: str, user_prompt: str) -> Optional[dict]:
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
            )
            content = (resp.choices[0].message.content or "").strip()
            return _safe_json(content)
        except Exception as e:
            print(f"[JudgeLLM] OpenAI call failed: {e}")
            return None

    def _ask_gemini(self, system_prompt: str, user_prompt: str) -> Optional[dict]:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=self.genai_types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.1,
                ),
            )
            content = (response.text or "").strip()
            return _safe_json(content)
        except Exception as e:
            print(f"[JudgeLLM] Gemini call failed: {e}")
            return None

    def build_constraints(
        self,
        api_entry: dict,
        mapped_events: List[MappedEvent],
    ) -> List[str]:
        if not self.enabled:
            return _heuristic_constraints(mapped_events)

        system_prompt = (
            "You are a strict API constraint judge for Genesis physics engine API usage failures.\n"
            "Given runtime error evidence and API metadata, produce concise, prescriptive constraints "
            "that prevent code-generation hallucinations.\n\n"
            "A GOOD constraint tells the agent WHAT TO DO or WHAT NOT TO DO in concrete terms:\n"
            "  Bad:  \"Avoid this runtime failure pattern: Scene is already built.\"\n"
            "  Good: \"Must be called before scene.build(); calling after build() causes runtime error.\"\n"
            "  Bad:  \"Avoid this runtime failure pattern: Cloth material only supports Mesh morph.\"\n"
            "  Good: \"The `cloth` material only accepts Mesh morph (not Box, Sphere, etc.).\"\n"
            "  Bad:  \"Avoid this runtime failure pattern: File not found.\"\n"
            "  Good: \"URDF file path must be a valid absolute or relative path to an existing .urdf file; "
            "do not fabricate paths like 'robot.urdf' or 'genesis/assets/...'.\"\n\n"
            "Rules:\n"
            "1) Output JSON only: {\"constraints\": [\"...\"]}\n"
            "2) 1-5 constraints, each one sentence, under 200 chars.\n"
            "3) Every constraint MUST be prescriptive — tell the agent what to do/not do specifically.\n"
            "4) If the same root cause appears in multiple error_events, merge into one constraint.\n"
            "5) Never copy-paste the raw error message; always generalize into a rule.\n"
            "6) No markdown, no generic summaries."
        )
        user_prompt = json.dumps(
            {
                "api": {
                    "api_id": api_entry.get("api_id"),
                    "signature": api_entry.get("signature", ""),
                    "summary": api_entry.get("summary", ""),
                },
                "error_events": [asdict(e) for e in mapped_events[:8]],
            },
            ensure_ascii=False,
            indent=2,
        )
        if self.provider == "openai":
            data = self._ask_openai(system_prompt, user_prompt)
        else:
            data = self._ask_gemini(system_prompt, user_prompt)

        if not isinstance(data, dict):
            return _heuristic_constraints(mapped_events)
        constraints = data.get("constraints", [])
        if not isinstance(constraints, list):
            return _heuristic_constraints(mapped_events)
        out = []
        for c in constraints:
            c = str(c).strip()
            if c:
                out.append(c)
        return out or _heuristic_constraints(mapped_events)


# ================= JSON / heuristic helpers =================
def _safe_json(raw: str) -> Optional[dict]:
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", raw or "")
        if not m:
            return None
        try:
            return json.loads(m.group(0))
        except Exception:
            return None


def _heuristic_constraints(events: List[MappedEvent]) -> List[str]:
    cons = []
    for e in events:
        msg = e.error_message
        m1 = re.search(
            r"([A-Za-z_][A-Za-z0-9_\.]*)\(\) got an unexpected keyword argument '([^']+)'",
            msg,
        )
        if m1:
            fn, kw = m1.group(1), m1.group(2)
            cons.append(
                f"Do not pass unsupported keyword '{kw}' to {fn}; follow the exact signature."
            )
            continue
        m1b = re.search(
            r"([A-Za-z_][A-Za-z0-9_\.]*)\(\) got multiple values for argument '([^']+)'",
            msg,
        )
        if m1b:
            fn, arg = m1b.group(1), m1b.group(2)
            cons.append(
                f"Do not pass argument '{arg}' twice when calling {fn}; avoid mixing conflicting positional and keyword values."
            )
            continue
        m2 = re.search(
            r"'([A-Za-z_][A-Za-z0-9_]*)' object has no attribute '([A-Za-z_][A-Za-z0-9_]*)'",
            msg,
        )
        if m2:
            cls, meth = m2.group(1), m2.group(2)
            cons.append(
                f"Do not call non-existent method '{meth}' on {cls}; verify available API methods first."
            )
            continue
        m3 = re.search(r"([A-Za-z_][A-Za-z0-9_\.]*)\(\) missing .* argument", msg)
        if m3:
            fn = m3.group(1)
            cons.append(f"{fn} requires mandatory arguments; do not omit required parameters.")
            continue
        m4 = re.search(
            r"([A-Za-z_][A-Za-z0-9_\.]*)\(\) takes \d+ positional arguments? but \d+ (?:were|was) given",
            msg,
        )
        if m4:
            fn = m4.group(1)
            cons.append(
                f"Use the correct argument arity when calling {fn}; do not pass extra positional arguments."
            )
            continue
        if " is not callable" in msg:
            cons.append(
                "Do not call non-callable objects as functions; check whether the API is a method, property, or object instance."
            )
            continue
        m5 = re.search(r"name '([A-Za-z_][A-Za-z0-9_]*)' is not defined", msg)
        if m5:
            sym = m5.group(1)
            cons.append(
                f"Do not use undefined symbol '{sym}'; verify imports and use canonical Genesis API names."
            )
            continue
        m6 = re.search(r"No module named '([^']+)'", msg)
        if m6:
            mod = m6.group(1)
            cons.append(
                f"Do not import non-existent module '{mod}'; verify package path and Genesis namespace."
            )
            continue
        # GenesisException: Unrecognized attribute
        m7 = re.search(r"Unrecognized attribute:\s*(\S+)", msg)
        if m7:
            attr = m7.group(1)
            cons.append(
                f"Do not pass unrecognized attribute '{attr}'; it is not a valid parameter for this API."
            )
            continue
        cons.append(f"Avoid this runtime failure pattern: {msg}")
    seen = set()
    out = []
    for c in cons:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out[:5]


# ================= Prompt Loading =================
def load_prompts(prompts_file: str, prompt_key: str, task_id_key: str) -> List[dict]:
    data = _read_json(prompts_file)
    prompts = []
    if isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, dict):
                q = str(item.get(prompt_key, "")).strip()
                if not q:
                    continue
                prompts.append(
                    {
                        "task_id": str(item.get(task_id_key, f"task_{i:03d}")),
                        "query": q,
                    }
                )
    elif isinstance(data, dict):
        for i, item in enumerate(data.get("prompts", [])):
            if isinstance(item, str):
                q = item.strip()
                if q:
                    prompts.append({"task_id": f"task_{i:03d}", "query": q})
    return prompts


# ================= Code Execution =================
def execute_generated_code(
    code: str,
    task_id: str,
    workspace_dir: str,
    timeout_s: int = 120,
    python_executable: str = "",
) -> Tuple[str, str, int]:
    """
    保存生成的代码到 workspace 并执行，返回 (stdout, stderr, returncode)。
    """
    abs_workspace = os.path.abspath(workspace_dir)
    os.makedirs(abs_workspace, exist_ok=True)
    script_path = os.path.join(abs_workspace, f"{task_id}.py")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(code)

    python = python_executable or sys.executable

    env = os.environ.copy()
    env.setdefault("GENESIS_OFFSCREEN", "1")
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        proc = subprocess.run(
            [python, script_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
            cwd=abs_workspace,
            env=env,
        )
        return proc.stdout or "", proc.stderr or "", proc.returncode
    except subprocess.TimeoutExpired:
        return "", f"TimeoutExpired after {timeout_s}s", -999
    except Exception as e:
        return "", str(e), -1


# ================= Error Parsing =================
def parse_error_events(log_text: str) -> List[ErrorEvent]:
    text = _strip_ansi(log_text or "")
    lines = text.splitlines()
    events: List[ErrorEvent] = []

    tb_pat = re.compile(r"^(?P<etype>[A-Za-z_]\w*(?:Error|Exception)):\s*(?P<msg>.+)$")
    gen_pat = re.compile(
        r"\[Genesis\].*\[ERROR\].*?(?P<etype>[A-Za-z_]\w*(?:Error|Exception)):\s*(?P<msg>.+)$"
    )

    for idx, ln in enumerate(lines):
        ln_s = ln.strip()
        m = gen_pat.search(ln_s)
        if m:
            events.append(
                ErrorEvent(
                    error_type=m.group("etype"),
                    error_message=m.group("msg").strip(),
                    traceback_excerpt=_traceback_block_near(lines, idx),
                    raw_line=ln_s,
                    confidence="high",
                )
            )
            continue
        m = tb_pat.match(ln_s)
        if m:
            if ln_s.startswith("Error:"):
                continue
            events.append(
                ErrorEvent(
                    error_type=m.group("etype"),
                    error_message=m.group("msg").strip(),
                    traceback_excerpt=_traceback_block_near(lines, idx),
                    raw_line=ln_s,
                    confidence="medium",
                )
            )

    uniq = []
    seen = set()
    for e in events:
        k = (e.error_type, e.error_message)
        if k not in seen:
            seen.add(k)
            uniq.append(e)
    return uniq


def _window(lines: List[str], idx: int, before: int, after: int) -> str:
    s = max(0, idx - before)
    e = min(len(lines), idx + after + 1)
    return "\n".join(lines[s:e]).strip()


def _traceback_block_near(lines: List[str], idx: int) -> str:
    start = idx
    for i in range(idx, -1, -1):
        if "Traceback (most recent call last):" in lines[i]:
            start = i
            break
    return "\n".join(lines[start : idx + 1]).strip()


# ================= API KB Loading =================
def load_api_kb(api_index_file: str) -> Tuple[Dict[str, dict], set, set]:
    rows = _read_json(api_index_file)
    by_id = {}
    ids = set()
    class_ids = set()
    for r in rows:
        if not isinstance(r, dict):
            continue
        api_id = r.get("api_id")
        if not api_id:
            continue
        by_id[api_id] = r
        ids.add(api_id)
        if r.get("type") == "class":
            class_ids.add(api_id)
    return by_id, ids, class_ids


def _symbol_from_error_message(msg: str) -> str:
    # Standard Python error patterns
    patterns = [
        r"([A-Za-z_][A-Za-z0-9_\.]*)\(\) got an unexpected keyword argument",
        r"([A-Za-z_][A-Za-z0-9_\.]*)\(\) missing .* argument",
        r"([A-Za-z_][A-Za-z0-9_\.]*)\(\) got multiple values for argument",
        r"([A-Za-z_][A-Za-z0-9_\.]*)\(\) takes \d+ positional arguments? but \d+ (?:were|was) given",
    ]
    for p in patterns:
        m = re.search(p, msg)
        if m:
            return m.group(1)
    m = re.search(
        r"'([A-Za-z_][A-Za-z0-9_]*)' object has no attribute '([A-Za-z_][A-Za-z0-9_]*)'",
        msg,
    )
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    m = re.search(r"name '([A-Za-z_][A-Za-z0-9_]*)' is not defined", msg)
    if m:
        return m.group(1)
    return ""


def _symbol_from_traceback(traceback_excerpt: str) -> str:
    """从 traceback 中提取用户代码中的 gs.xxx.yyy( 调用作为 API 符号。"""
    # 匹配 gs.morphs.Box( / gs.materials.Rigid( / gs.Scene( / scene.add_entity( 等
    gs_pat = re.compile(r"(gs\.[A-Za-z_][A-Za-z0-9_\.]*)\s*\(")
    scene_pat = re.compile(r"scene\.([A-Za-z_][A-Za-z0-9_]*)\s*\(")

    # Genesis 内部符号，不应作为 API 符号
    _skip_suffixes = (
        "Exception", "Error", "raise_exception", "raise_warning",
        "logger", "logging", "destroy",
    )

    best_gs = ""
    best_scene = ""
    for line in traceback_excerpt.splitlines():
        line = line.strip()
        # 跳过库内部帧
        if "genesis" in line and ("genesis\\" in line or "genesis/" in line):
            if re.search(r"genesis[\\/](options|utils|__init__|logging)", line):
                continue
        m = gs_pat.search(line)
        if m:
            sym = m.group(1)
            # 跳过 Genesis 内部符号
            if any(s in sym for s in _skip_suffixes):
                continue
            best_gs = sym
        m = scene_pat.search(line)
        if m:
            best_scene = m.group(1)

    # 优先返回 gs.xxx.yyy 形式（可直接映射到知识库）
    if best_gs:
        return best_gs.replace("gs.", "genesis.")
    if best_scene:
        return f"genesis.Scene.{best_scene}"
    return ""


def resolve_api_id(symbol: str, known_ids: set, class_ids: set) -> Optional[str]:
    if not symbol:
        return None
    cands = []
    s = symbol.strip()
    if s.startswith("genesis."):
        cands.append(s)
    else:
        cands.append(f"genesis.{s}")

    # 先尝试原始路径，再尝试 api_id_normalize 归一化路径
    for c in cands:
        if c in known_ids:
            return c
    # 归一化：gs.morphs.Box → genesis.options.morphs.Box
    for c in cands:
        normalized = _normalize_api_id(c)
        if normalized != c and normalized in known_ids:
            return normalized
    # Fallback to class-level API
    for c in cands:
        parts = c.split(".")
        if len(parts) >= 3:
            cls = ".".join(parts[:2])
            if cls in class_ids:
                return cls
            cls_normalized = _normalize_api_id(cls)
            if cls_normalized != cls and cls_normalized in class_ids:
                return cls_normalized
    return None


def _normalize_api_id(api_id: str) -> str:
    """将 gs.morphs.X → genesis.options.morphs.X 等路径归一化。"""
    from api_id_normalize import normalize_api_id_for_kb
    return normalize_api_id_for_kb(api_id)


def map_events_to_api(
    events: List[ErrorEvent],
    known_ids: set,
    class_ids: set,
    prompt_id: str,
    prompt_query: str,
) -> List[MappedEvent]:
    out: List[MappedEvent] = []
    for e in events:
        symbol = _symbol_from_error_message(e.error_message)
        # Fallback: 从 traceback 提取 API 调用（处理 GenesisException 等）
        if not symbol:
            symbol = _symbol_from_traceback(e.traceback_excerpt)
        api_id = resolve_api_id(symbol, known_ids, class_ids)
        if not api_id:
            continue
        out.append(
            MappedEvent(
                api_id=api_id,
                error_type=e.error_type,
                error_message=e.error_message,
                traceback_excerpt=e.traceback_excerpt,
                raw_line=e.raw_line,
                prompt_id=prompt_id,
                prompt_query=prompt_query,
                confidence=e.confidence,
                inferred_symbol=symbol,
            )
        )
    return out


# ================= Aggregate =================
def aggregate_constraints(
    mapped: List[MappedEvent],
    api_by_id: Dict[str, dict],
    judge: JudgeLLM,
    max_examples_per_api: int,
) -> dict:
    grouped: Dict[str, List[MappedEvent]] = defaultdict(list)
    for m in mapped:
        grouped[m.api_id].append(m)

    apis_out = []
    for api_id, events in sorted(grouped.items()):
        api_entry = api_by_id.get(api_id, {"api_id": api_id})
        constraints = judge.build_constraints(api_entry, events)
        error_examples = []
        seen = set()
        for e in events:
            msg = e.error_message.strip()
            if msg and msg not in seen:
                seen.add(msg)
                error_examples.append(msg)
            if len(error_examples) >= max_examples_per_api:
                break

        apis_out.append(
            {
                "api_id": api_id,
                "constraints": constraints,
                "error_examples": error_examples,
                "event_count": len(events),
                "sources": sorted({e.prompt_id for e in events}),
            }
        )

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": {
            "api_count": len(apis_out),
            "mapped_event_count": len(mapped),
        },
        "apis": apis_out,
    }


# ================= Main =================
def main():
    default_workspace = os.path.join(RAG_DEMO_ROOT, "workspace", "constraint_build")
    default_api_index = os.path.join(RAG_DEMO_ROOT, "knowledge_base", "genesis_api_index.json")
    default_prompts = os.path.join(RAG_DEMO_ROOT, "benchmark", "query.json")
    default_output = os.path.join(RAG_DEMO_ROOT, "knowledge_base", "api_constraint.json")

    p = argparse.ArgumentParser(description="Build API constraints from GenesisAgent runtime failures.")
    p.add_argument(
        "--prompts-file",
        default=default_prompts,
        help="Prompt source JSON file.",
    )
    p.add_argument("--prompt-key", default="query", help="Field name for prompt text.")
    p.add_argument("--task-id-key", default="task_id", help="Field name for task id.")
    p.add_argument("--max-prompts", type=int, default=0, help="0 means all prompts.")
    # run mode
    p.add_argument(
        "--run-agent",
        dest="run_agent",
        action="store_true",
        default=True,
        help="Run GenesisAgent for each prompt (default: true).",
    )
    p.add_argument(
        "--no-run-agent",
        dest="run_agent",
        action="store_false",
        help="Do not run agent, parse existing logs only.",
    )
    p.add_argument(
        "--logs-file",
        default="",
        help="Existing stderr log to parse in no-run mode.",
    )
    # paths
    p.add_argument("--api-index-file", default=default_api_index, help="genesis_api_index.json path.")
    p.add_argument("--output-file", default=default_output, help="Output api_constraint.json path.")
    p.add_argument("--workspace", default=default_workspace, help="Workspace for generated scripts.")
    # execution
    p.add_argument("--timeout-s", type=int, default=120, help="Timeout per code execution (seconds).")
    p.add_argument("--max-examples-per-api", type=int, default=6)
    p.add_argument(
        "--python",
        default="",
        help="Python executable for running generated code (default: sys.executable). "
             "Example: D:/anaconda/envs/env_genesis/python.exe",
    )
    # agent config
    p.add_argument(
        "--rewrite-mode",
        choices=["none", "translate", "hyde"],
        default="hyde",
        help="Query rewriting mode for agent (default: hyde).",
    )
    # Judge LLM
    p.add_argument("--judge-provider", default="none", choices=["none", "openai", "gemini"])
    p.add_argument("--judge-model", default="")
    p.add_argument("--judge-api-key", default="")
    p.add_argument("--judge-base-url", default="")

    args = p.parse_args()

    prompts = load_prompts(args.prompts_file, args.prompt_key, args.task_id_key)
    if args.max_prompts > 0:
        prompts = prompts[: args.max_prompts]
    if not prompts:
        raise ValueError(f"No prompts loaded from {args.prompts_file}")

    api_by_id, known_ids, class_ids = load_api_kb(args.api_index_file)

    judge = JudgeLLM(
        provider=args.judge_provider,
        model=args.judge_model or None,
        api_key=args.judge_api_key or None,
        base_url=args.judge_base_url or None,
    )

    all_mapped: List[MappedEvent] = []
    runs_meta = []

    if args.run_agent:
        # ---- Import agent lazily (only when running) ----
        from agent import GenesisAgent

        print(f"[build_api_constraint] Initializing GenesisAgent (rewrite_mode={args.rewrite_mode})...")
        agent = GenesisAgent(rewrite_mode=args.rewrite_mode)

        print(f"[build_api_constraint] Running {len(prompts)} prompts through GenesisAgent...")

        pipeline_t0 = time.time()
        for i, row in enumerate(prompts, 1):
            task_id = row["task_id"]
            query = row["query"]
            short_q = re.sub(r"\s+", " ", query).strip()[:88]
            task_t0 = time.time()

            print(f"\n[{i}/{len(prompts)}] task_id={task_id}")
            print(f"  prompt: {short_q}{'...' if len(query) > 88 else ''}")

            # Stage 1: Agent generates code
            try:
                result = agent.solve(query, save_code=False)
                code = result["code"]
                key_apis = result.get("key_apis", [])
                print(f"  [stage] agent done | code_len={len(code)} | key_apis={key_apis[:5]}")
            except Exception as e:
                print(f"  [stage] agent failed: {e}")
                code = ""
                key_apis = []

            # Stage 2: Execute generated code
            stdout, stderr, returncode = "", "", -1
            if code and not code.startswith("# Error:"):
                try:
                    stdout, stderr, returncode = execute_generated_code(
                        code, task_id, args.workspace, timeout_s=args.timeout_s,
                        python_executable=args.python,
                    )
                    print(f"  [stage] executed | rc={returncode} | stderr_len={len(stderr)}")
                except Exception as e:
                    stderr = str(e)
                    returncode = -1
                    print(f"  [stage] execution error: {e}")
            else:
                print(f"  [stage] skipped execution (no valid code)")

            # Stage 3: Parse errors (stdout contains Python tracebacks, stderr may have logging noise)
            combined_output = f"{stdout}\n{stderr}"
            events = parse_error_events(combined_output)
            mapped = map_events_to_api(events, known_ids, class_ids, task_id, query)
            all_mapped.extend(mapped)

            elapsed = time.time() - task_t0
            avg = (time.time() - pipeline_t0) / i
            eta = max(0.0, avg * (len(prompts) - i))

            runs_meta.append(
                {
                    "task_id": task_id,
                    "return_code": returncode,
                    "code_length": len(code),
                    "key_apis": key_apis[:10],
                    "event_count": len(events),
                    "mapped_count": len(mapped),
                    "elapsed_s": round(elapsed, 1),
                }
            )
            print(
                f"  [stage] events={len(events)}, mapped={len(mapped)} | "
                f"elapsed={elapsed:.1f}s, eta={eta/60:.1f}m"
            )

        total_elapsed = time.time() - pipeline_t0
        print(f"\n[build_api_constraint] All tasks finished in {total_elapsed/60:.1f}m")

    else:
        # ---- Parse-only mode ----
        if not args.logs_file or not os.path.exists(args.logs_file):
            raise ValueError(
                f"No-run mode requires a valid logs file. Current value: {args.logs_file!r}"
            )
        with open(args.logs_file, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        events = parse_error_events(text)
        all_mapped = map_events_to_api(events, known_ids, class_ids, prompt_id="logs_only", prompt_query="N/A")
        runs_meta.append(
            {
                "task_id": "logs_only",
                "return_code": 0,
                "event_count": len(events),
                "mapped_count": len(all_mapped),
            }
        )

    # ---- Aggregate constraints ----
    result = aggregate_constraints(
        mapped=all_mapped,
        api_by_id=api_by_id,
        judge=judge,
        max_examples_per_api=args.max_examples_per_api,
    )
    result["run_meta"] = runs_meta
    result["config"] = {
        "prompts_file": args.prompts_file,
        "api_index_file": args.api_index_file,
        "judge_provider": args.judge_provider,
        "judge_model": args.judge_model,
        "run_agent": bool(args.run_agent),
        "rewrite_mode": args.rewrite_mode,
    }
    _write_json(args.output_file, result)
    print(f"\n[build_api_constraint] Output written: {args.output_file}")
    print(
        f"[build_api_constraint] mapped events={result['summary']['mapped_event_count']}, "
        f"apis={result['summary']['api_count']}"
    )


if __name__ == "__main__":
    main()
