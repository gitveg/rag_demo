"""
执行指定目录下 examples/*.py，记录哪些脚本跑不通以及对应报错信息。

设计目标：
1) 逻辑尽量复用 build_mem_execute.py 的“报错段落抽取”方式；
2) 对 examples 统一设置 PYTEST_VERSION=1，尽量缩短运行时长，减少误判为“跑不通”；
3) 输出 JSON（全量结果）+ TXT（失败摘要），便于你人工逐个排查并删除。
4) 可选：根据 JSON 删除执行失败的 .py（见 --delete-failed；默认 dry-run，需 --yes 才真正删除）。
"""

import argparse
import os
import json
import re
import subprocess
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional


_THIS_DIR = os.path.dirname(os.path.abspath(__file__))              # .../Genesis/rag_demo/mem_builder
_RAG_DEMO_DIR = os.path.dirname(_THIS_DIR)                        # .../Genesis/rag_demo
_GENESIS_DIR = os.path.dirname(_RAG_DEMO_DIR)                     # .../Genesis
_DEFAULT_EXAMPLES_DIR = os.path.join(_GENESIS_DIR, "examples")  # .../Genesis/examples
_DEFAULT_KB_DIR = os.path.join(_RAG_DEMO_DIR, "knowledge_base") # .../Genesis/rag_demo/knowledge_base


TRACEBACK_START = "Traceback (most recent call last):"
GENESIS_ERROR_MARKER = "[Genesis]"
ERROR_MARKER = "[ERROR]"


def extract_error_segment(raw_output: str) -> str:
    """
    从完整输出中截取「完整报错信息」：
    从 "Traceback (most recent call last):" 开头，
    到包含 "[Genesis] ... [ERROR] ..." 的那一行结尾。
    若找不到开头则返回整段输出（但会在调用方做截断）。
    """
    if not raw_output or not raw_output.strip():
        return raw_output

    start = raw_output.find(TRACEBACK_START)
    if start == -1:
        return raw_output.strip()

    rest = raw_output[start:]
    lines = rest.split("\n")
    end_line_idx = -1
    for i, line in enumerate(lines):
        if GENESIS_ERROR_MARKER in line and ERROR_MARKER in line:
            end_line_idx = i
            break

    if end_line_idx >= 0:
        segment = "\n".join(lines[: end_line_idx + 1])
    else:
        segment = rest
    return segment.strip()


def iter_py_files(examples_dir: str, recursive: bool) -> List[str]:
    py_files: List[str] = []
    if recursive:
        for root, _, files in os.walk(examples_dir):
            for f in files:
                if f.endswith(".py"):
                    py_files.append(os.path.join(root, f))
    else:
        for f in os.listdir(examples_dir):
            if f.endswith(".py"):
                py_files.append(os.path.join(examples_dir, f))
    return sorted(py_files)


def _extract_script_path_from_traceback(text: str, basename: str) -> Optional[str]:
    """从 Traceback 的 `File \"...\"` 行中解析与 basename 匹配的脚本绝对路径。"""
    if not text or not basename:
        return None
    for m in re.finditer(r'File\s+"([^"]+)"', text):
        path = m.group(1)
        norm = path.replace("\\", "/")
        if norm.endswith(basename) or os.path.basename(path) == basename:
            if os.path.isfile(path):
                return path
    return None


def _find_paths_by_basename(root: str, basename: str) -> List[str]:
    out: List[str] = []
    for dirpath, _, filenames in os.walk(root):
        if basename in filenames:
            out.append(os.path.join(dirpath, basename))
    return sorted(out)


def resolve_failed_script_path(
    examples_dir: str,
    entry: Dict[str, Any],
) -> Optional[str]:
    """
    根据 JSON 单条 result 解析磁盘上的 .py 路径。
    优先用 error_extract/error_raw 里的 Traceback 路径；否则在 examples_dir 下按文件名搜索。
    """
    basename = entry.get("id") or ""
    if not basename.endswith(".py"):
        return None
    err_blob = (entry.get("error_extract") or "") + "\n" + (entry.get("error_raw") or "")
    p = _extract_script_path_from_traceback(err_blob, basename)
    if p:
        return p
    candidates = _find_paths_by_basename(examples_dir, basename)
    if len(candidates) == 1:
        return candidates[0]
    return None


def delete_failed_from_json(
    input_json: str,
    examples_dir: Optional[str],
    dry_run: bool,
) -> None:
    with open(input_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    root = examples_dir or data.get("examples_dir")
    if not root or not os.path.isdir(root):
        print(f"❌ 无法确定 examples 根目录（请传 --examples-dir 或检查 JSON 中的 examples_dir）: {root}")
        return

    results = data.get("results") or []
    failed = [r for r in results if not r.get("success")]
    if not failed:
        print("没有失败记录，无需删除。")
        return

    print(f"根据 {input_json}：共 {len(failed)} 条失败记录，根目录: {root}")
    if dry_run:
        print("（dry-run，未真正删除；确认后请加 --yes）")

    deleted = 0
    skipped = 0
    for r in failed:
        bid = r.get("id", "?")
        path = resolve_failed_script_path(root, r)
        if not path:
            alts = _find_paths_by_basename(root, bid) if bid.endswith(".py") else []
            if len(alts) > 1:
                print(f"  [SKIP] {bid} — 同名文件多处存在，请从报错中手动删除：")
                for a in alts:
                    print(f"         {a}")
            else:
                print(f"  [SKIP] {bid} — 无法解析路径")
            skipped += 1
            continue
        if dry_run:
            print(f"  [would delete] {path}")
        else:
            try:
                os.remove(path)
                print(f"  [deleted] {path}")
                deleted += 1
            except OSError as e:
                print(f"  [FAIL] {path} — {e}")
                skipped += 1

    if not dry_run:
        print(f"\n完成：已删除 {deleted} 个文件，跳过/失败 {skipped} 个。")
    else:
        print(f"\n预览结束：将尝试处理 {len(failed)} 个失败项（跳过 {skipped} 个无法解析）。")


def run_one(script_path: str, env: dict, timeout_seconds: int) -> Dict[str, Any]:
    fname = os.path.basename(script_path)

    try:
        result = subprocess.run(
            [sys.executable, "-u", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=timeout_seconds,
        )
        raw = (result.stdout or "").strip()
        if result.returncode == 0:
            return {"id": fname, "success": True}

        err_extract = extract_error_segment(raw)
        return {
            "id": fname,
            "success": False,
            "returncode": result.returncode,
            "error_raw": raw[-6000:],  # 避免落盘过大
            "error_extract": err_extract[:6000],
        }
    except subprocess.TimeoutExpired:
        return {
            "id": fname,
            "success": False,
            "timeout_seconds": timeout_seconds,
            "error_raw": f"(Timeout after {timeout_seconds}s)",
            "error_extract": f"(Timeout after {timeout_seconds}s)",
        }
    except Exception as e:
        raw = str(e)
        return {
            "id": fname,
            "success": False,
            "error_raw": raw[-6000:],
            "error_extract": raw[:6000],
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--examples-dir",
        type=str,
        required=False,
        default=None,
        help="examples 根目录；执行模式默认 Genesis/examples；删除模式默认使用 JSON 内 examples_dir",
    )
    parser.add_argument("--recursive", action="store_true", help="是否递归查找子目录 .py")
    parser.add_argument("--timeout", type=int, default=600, help="每个脚本超时时间（秒）")
    parser.add_argument(
        "--output-json",
        type=str,
        default=os.path.join(
            _DEFAULT_KB_DIR,
            "genesis_execute_examples_results.json",
        ),
        help="输出 JSON 路径",
    )
    parser.add_argument(
        "--output-txt",
        type=str,
        default=os.path.join(
            _DEFAULT_KB_DIR,
            "genesis_execute_examples_failures.txt",
        ),
        help="失败用例摘要输出 TXT 路径",
    )
    parser.add_argument(
        "--delete-failed",
        action="store_true",
        help="不执行扫描；根据 genesis_execute_examples_results.json 中 success=false 的项删除对应 .py",
    )
    parser.add_argument(
        "--input-json",
        type=str,
        default=None,
        help="与 --delete-failed 联用：指定结果 JSON（默认与 --output-json 相同）",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="与 --delete-failed 联用：真正删除文件；省略则仅打印将要删除的路径（dry-run）",
    )
    args = parser.parse_args()

    input_json = args.input_json or args.output_json
    if args.delete_failed:
        if not os.path.isfile(input_json):
            print(f"❌ 找不到结果文件: {input_json}")
            return
        delete_failed_from_json(
            input_json=input_json,
            examples_dir=args.examples_dir,
            dry_run=not args.yes,
        )
        return

    examples_dir = args.examples_dir or _DEFAULT_EXAMPLES_DIR
    if not os.path.exists(examples_dir):
        print(f"❌ examples-dir 不存在: {examples_dir}")
        return

    # 你的目标是“指定 examples 文件夹下所有子目录的 .py 都跑一遍”
    py_files = iter_py_files(examples_dir, recursive=True)
    if not py_files:
        print(f"❌ 在目录未找到 .py: {examples_dir}")
        return

    env = os.environ.copy()
    # 让 examples 内置逻辑尽量走“测试短跑模式”
    env["PYTEST_VERSION"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONUTF8"] = "1"

    results: List[Dict[str, Any]] = []
    print(f"🚀 Executing {len(py_files)} example scripts ...")

    total = len(py_files)
    for i, script_path in enumerate(py_files, start=1):
        fname = os.path.basename(script_path)
        print(f"[{i}/{total}] {fname}")
        r = run_one(script_path, env=env, timeout_seconds=args.timeout)
        results.append(r)
        if r.get("success"):
            print(f"    -> [OK]")
        else:
            if r.get("timeout_seconds") is not None:
                print(f"    -> [FAIL] timeout={r.get('timeout_seconds')}s")
            else:
                rc = r.get("returncode")
                extra = f" returncode={rc}" if rc is not None else ""

                err_extract = (r.get("error_extract") or "").strip()
                # 取 1-2 行可读预览：优先含 Traceback / [Genesis] / [ERROR]
                previews: List[str] = []
                for ln in err_extract.splitlines():
                    s = ln.strip()
                    if not s:
                        continue
                    if "Traceback" in s or "[Genesis]" in s or "[ERROR]" in s or "GenesisException" in s:
                        previews.append(s[:220])
                    if len(previews) >= 2:
                        break
                if not previews:
                    # 兜底：直接取前两行
                    all_lines = [ln.strip() for ln in err_extract.splitlines() if ln.strip()]
                    previews = [all_lines[0][:220], all_lines[1][:220]] if len(all_lines) >= 2 else (
                        [all_lines[0][:220]] if all_lines else ["(no error_extract)"]
                    )

                print(f"    -> [FAIL]{extra}")
                for p in previews:
                    print(f"       {p}")

    out = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "examples_dir": examples_dir,
        "timeout_seconds": args.timeout,
        "recursive": True,
        "results": results,
    }

    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    failures = [r for r in results if not r.get("success")]
    os.makedirs(os.path.dirname(args.output_txt), exist_ok=True)
    with open(args.output_txt, "w", encoding="utf-8") as f:
        f.write(f"Failures: {len(failures)}/{len(results)}\n")
        f.write("=" * 80 + "\n")
        for r in failures:
            f.write(f"\n[FAIL] {r.get('id')}\n")
            if r.get("returncode") is not None:
                f.write(f"returncode: {r.get('returncode')}\n")
            if r.get("timeout_seconds") is not None:
                f.write(f"timeout_seconds: {r.get('timeout_seconds')}\n")
            f.write("\n--- error_extract ---\n")
            f.write(r.get("error_extract", "") + "\n")

    print(f"\n✅ Done. Failures: {len(failures)}/{len(results)}")
    print(f"JSON: {args.output_json}")
    print(f"TXT : {args.output_txt}")


if __name__ == "__main__":
    main()

