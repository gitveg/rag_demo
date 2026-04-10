import inspect
import json
import math
import os
import sys

import genesis as gs

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_KB_DIR = os.path.join(_BASE_DIR, "knowledge_base")

# 从 indexers/ 下直接运行时，保证能 import rag_demo 根目录的 llm_utils
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

try:
    import dotenv

    dotenv.load_dotenv(os.path.join(_BASE_DIR, ".env"))
except ImportError:
    pass

# 唯一 API 知识库文件：默认流程在此写入清洗结果；enrich 在同一文件上原地增强
GENESIS_API_INDEX_FILE = os.path.join(_KB_DIR, "genesis_api_index.json")
FREQUENCY_FILE = os.path.join(_KB_DIR, "api_frequency_report.json")

METHOD_BLOCKLIST = {
    "json", "dict", "copy", "schema", "parse_raw", "parse_obj", "parse_file",
    "from_orm", "construct", "update_forward_refs", "validate", "model_construct",
    "model_copy", "model_dump", "model_dump_json",
    "model_json_schema", "model_validate",
    "keys", "values", "items", "get", "pop",
}

STRICT_WHITELIST_PREFIXES = [
    "genesis.Scene",
    "genesis.morphs",
    "genesis.materials",
    "genesis.states",
    "genesis.force_fields",
    "genesis.engine.materials",
    "genesis.engine.states",
    "genesis.engine.force_fields",
    "genesis.surfaces",
    "genesis.options",
]

# genesis/__init__.py 再导出 → 用户写作 gs.*；api_id 与 get_object_by_path 需与此一致
_ENGINE_EXPORT_TO_PUBLIC_PREFIXES: tuple[tuple[str, str], ...] = (
    ("genesis.engine.materials", "genesis.materials"),
    ("genesis.engine.states", "genesis.states"),
    ("genesis.engine.force_fields", "genesis.force_fields"),
)

ENRICH_SYSTEM_PROMPT = """
You are a Metadata Enrichment Agent for the Genesis Physics Engine API.
Your goal is to extract specific details from the raw docstring to fill in missing metadata.

Input: JSON object containing 'raw_docstring' and a 'tasks' object indicating what to generate.

Output: A JSON object with ONLY the requested fields:
1. "summary": (Generate ONLY if tasks.generate_summary is True) A concise 1-sentence summary.
2. "parameter_descs": A dictionary mapping "param_name" -> "description".
   - CRITICAL: Only provide descriptions for parameters that have specific UNITS (e.g., 'in meters'), CONSTRAINTS (e.g., 'must be > 0'), or AMBIGUITY.
   - CRITICAL: Leave the description EMPTY string "" if the parameter is self-explanatory (like 'color', 'pos', 'name').
   - Do NOT include type information in the description (we already have it).
3. "constraints": A list of strings extracting limitations/warnings (e.g., "Rigid does not support vis_mode").

Response Format: Pure JSON.
"""


def clean_type_str(annotation):
    if annotation == inspect.Parameter.empty:
        return "Any"
    if hasattr(annotation, "__name__"):
        type_str = annotation.__name__
    else:
        type_str = str(annotation)
    return type_str.replace("typing.", "").replace("genesis.", "gs.")


def get_summary_from_doc(obj):
    doc = inspect.getdoc(obj)
    if not doc:
        return "No summary available."
    first_paragraph = doc.split("\n\n")[0].replace("\n", " ")
    return first_paragraph[:150] + ("..." if len(first_paragraph) > 150 else "")


def canonicalize_public_api_id(api_id: str) -> str:
    for engine_prefix, public_prefix in _ENGINE_EXPORT_TO_PUBLIC_PREFIXES:
        if api_id.startswith(engine_prefix):
            return public_prefix + api_id[len(engine_prefix) :]
    return api_id


def get_object_by_path(api_id: str):
    """从 genesis.* 路径在 gs 上解析对象（与 canonicalize_public_api_id 一致）。"""
    parts = api_id.split(".")
    current = gs
    for part in parts[1:]:
        try:
            current = getattr(current, part)
        except AttributeError:
            return None
    return current


def format_simplified_signature(name, sig):
    params_str_list = []
    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue
        if param.default != inspect.Parameter.empty:
            def_val = str(param.default)
            if len(def_val) > 20:
                def_val = "..."
            params_str_list.append(f"{param_name}={def_val}")
        elif param.kind == inspect.Parameter.VAR_KEYWORD:
            params_str_list.append(f"**{param_name}")
        elif param.kind == inspect.Parameter.VAR_POSITIONAL:
            params_str_list.append(f"*{param_name}")
        else:
            params_str_list.append(param_name)
    return f"{name}({', '.join(params_str_list)})"


def extract_strict_schema(obj, api_id, layer_tag):
    entry = {
        "api_id": api_id,
        "type": "class" if inspect.isclass(obj) else "method",
        "signature": "",
        "summary": get_summary_from_doc(obj),
        "parameters": [],
        "constraints": [],
        "domain_tags": [layer_tag.lower()],
    }

    try:
        target_obj = obj.__init__ if inspect.isclass(obj) else obj
        sig = inspect.signature(target_obj)
        short_name = api_id.split(".")[-1]
        entry["signature"] = format_simplified_signature(short_name, sig)

        for name, param in sig.parameters.items():
            if name == "self":
                continue
            is_required = param.default == inspect.Parameter.empty
            type_str = clean_type_str(param.annotation)
            param_entry = {
                "name": name,
                "type": type_str,
                "desc": "",
                "required": is_required,
            }
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                param_entry["desc"] = "[Auto-Detect] Variable keyword arguments. Needs LLM expansion."
                param_entry["type"] = "Dict"
                param_entry["required"] = False
            entry["parameters"].append(param_entry)

    except (ValueError, TypeError):
        entry["signature"] = f"{api_id.split('.')[-1]}(...args)"
        entry["parameters"] = [
            {"name": "*args", "type": "Any", "desc": "Unknown parameters", "required": False}
        ]

    return entry


def process_module(module, layer_tag, visited, recurse_submodules=True):
    results = []
    try:
        members = inspect.getmembers(module)
    except Exception:
        return results

    for name, obj in members:
        if name.startswith("_"):
            continue

        if inspect.ismodule(obj):
            if recurse_submodules and hasattr(obj, "__name__") and obj.__name__.startswith("genesis"):
                if not obj.__name__.startswith(module.__name__ + "."):
                    continue
                if obj.__name__ not in visited:
                    visited.add(obj.__name__)
                    results.extend(process_module(obj, layer_tag, visited, recurse_submodules=True))
            continue

        full_name = f"{module.__name__}.{name}"
        if full_name in visited:
            continue
        visited.add(full_name)

        api_id = canonicalize_public_api_id(full_name)

        if inspect.isclass(obj):
            if hasattr(obj, "__module__") and obj.__module__:
                if not obj.__module__.startswith("genesis"):
                    continue

            results.append(extract_strict_schema(obj, api_id, layer_tag))

            for method_name, method in inspect.getmembers(obj):
                if not (inspect.isfunction(method) or inspect.ismethod(method)):
                    continue
                if method_name.startswith("_"):
                    continue
                if method_name in METHOD_BLOCKLIST:
                    continue
                try:
                    real_func = inspect.unwrap(method)
                    if hasattr(real_func, "__module__") and real_func.__module__:
                        if not real_func.__module__.startswith("genesis"):
                            continue
                except Exception:
                    pass

                method_id = canonicalize_public_api_id(f"{full_name}.{method_name}")
                results.append(extract_strict_schema(method, method_id, layer_tag))

    return results


def _ensure_tag(domain_tags, tag):
    if not domain_tags:
        return [tag]
    if tag in domain_tags:
        return domain_tags
    return domain_tags + [tag]


def mark_core_apis(cleaned_data, freq_data, core_ratio=0.02, min_core=30, extra_core_allowlist=None):
    if not cleaned_data:
        return {"core_added": 0, "core_total": 0, "top_n": 0}

    api_ids_in_kb = set(item.get("api_id") for item in cleaned_data if item.get("api_id"))
    freq_rows = [row for row in (freq_data or []) if isinstance(row, dict) and row.get("api_name") in api_ids_in_kb]
    freq_rows.sort(key=lambda r: r.get("count", 0), reverse=True)

    top_n = max(min_core, int(math.ceil(len(cleaned_data) * core_ratio)))
    top_ids = set(row["api_name"] for row in freq_rows[:top_n])
    allowlist = set(a for a in (extra_core_allowlist or []) if a in api_ids_in_kb)
    target_core_ids = top_ids | allowlist

    added = 0
    core_total = 0
    for entry in cleaned_data:
        api_id = entry.get("api_id")
        if not api_id:
            continue
        domain_tags = entry.get("domain_tags") or []
        if api_id in target_core_ids:
            before = set(domain_tags)
            entry["domain_tags"] = _ensure_tag(domain_tags, "core")
            after = set(entry["domain_tags"])
            if "core" in after and "core" not in before:
                added += 1
        if "core" in (entry.get("domain_tags") or []):
            core_total += 1

    return {"core_added": added, "core_total": core_total, "top_n": top_n}


def build_index():
    """从 genesis 包抽取 API Schema，仅在内存中返回，不写单独 raw 文件。"""
    print("🛠️  正在执行符合 Target Schema 的 API 提取...")
    kb_data = []
    visited = set()
    targets = [
        (gs, "engine", False),
        (gs.morphs, "geometry", True),
        (gs.materials, "material", True),
        (gs.states, "engine", True),
        (gs.force_fields, "engine", True),
        (gs.surfaces, "surface", True),
        (gs.options, "config", True),
    ]

    for target in targets:
        mod, tag, recurse = target if len(target) == 3 else (*target, True)
        kb_data.extend(process_module(mod, tag, visited, recurse_submodules=recurse))

    print("✅ 抽取完成（未写盘；清洗阶段写入 genesis_api_index.json）")
    print(f"📊 总条目数: {len(kb_data)}")
    if kb_data:
        print("\n🔎 Schema 校验 (Preview First Entry):")
        print(json.dumps(kb_data[0], indent=2, ensure_ascii=False))
    return kb_data


def clean_knowledge_base(raw_data):
    """按频率表与白名单清洗 raw_data，写入 GENESIS_API_INDEX_FILE。"""
    print("🧹 开始执行 API 知识库数据清洗...")

    if not raw_data:
        print("❌ 错误: 无原始 API 数据（请先 build_index）。")
        return

    if not os.path.exists(FREQUENCY_FILE):
        print(f"❌ 错误: 找不到频率报告 {FREQUENCY_FILE}")
        return

    with open(FREQUENCY_FILE, "r", encoding="utf-8") as f:
        freq_data = json.load(f)

    used_apis_set = set(item["api_name"] for item in freq_data)
    print(f"📊 频率报告中包含 {len(used_apis_set)} 个实战 API。")

    cleaned_data = []
    dropped_count = 0
    kept_reasons = {"frequency": 0, "whitelist": 0}

    for api_entry in raw_data:
        api_id = api_entry["api_id"]
        should_keep = False
        reason = ""

        if api_id in used_apis_set:
            should_keep, reason = True, "frequency"
        else:
            for prefix in STRICT_WHITELIST_PREFIXES:
                if api_id.startswith(prefix):
                    should_keep, reason = True, "whitelist"
                    break

        if should_keep:
            cleaned_data.append(api_entry)
            kept_reasons[reason] += 1
        else:
            dropped_count += 1
            if dropped_count <= 5 or "CTRL_MODE" in api_id:
                print(f"   [丢弃] {api_id} (既不在频率表，也不在白名单)")

    extra_core_allowlist = {
        "genesis.init",
        "genesis.Scene",
        "genesis.Scene.add_entity",
        "genesis.Scene.build",
        "genesis.Scene.step",
    }
    core_stats = mark_core_apis(
        cleaned_data=cleaned_data,
        freq_data=freq_data,
        core_ratio=0.02,
        min_core=30,
        extra_core_allowlist=extra_core_allowlist,
    )
    print(
        f"🏷️ Core API 打标完成：新增 {core_stats['core_added']}，"
        f"当前 core 总数 {core_stats['core_total']}（top_n={core_stats['top_n']}）"
    )

    save_video_api = {
        "api_id": "genesis.Scene.viewer.save_video",
        "type": "method",
        "signature": "save_video(filename=None)",
        "summary": (
            "Save the stored frames from the viewer to a video file (e.g. MP4). "
            "Use after scene.viewer is running with record enabled: call scene.start_recording() before stepping, "
            "then scene.viewer.save_video(filename='out.mp4') after simulation (or use Viewer.close_external() then save_video)."
        ),
        "parameters": [
            {
                "name": "filename",
                "type": "str | None",
                "desc": "Path to save the video file. If None, a file dialog is opened.",
                "required": False,
            }
        ],
        "constraints": [],
        "domain_tags": ["engine", "core"],
    }
    if not any(e.get("api_id") == save_video_api["api_id"] for e in cleaned_data):
        cleaned_data.append(save_video_api)
        print(f"   📌 已注入 Core API: {save_video_api['api_id']}")

    with open(GENESIS_API_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

    total_raw = len(raw_data)
    reduction_rate = (dropped_count / total_raw) * 100 if total_raw else 0
    print("\n" + "=" * 40)
    print("✅ 清洗完成！统计报告：")
    print(f"   原始 API 数量: {total_raw}")
    print(f"   清洗后 API 数量: {len(cleaned_data)}")
    print(f"   🗑️  剔除数量: {dropped_count} (压缩率: {reduction_rate:.1f}%)")
    print("-" * 40)
    print(f"   因频率保留: {kept_reasons['frequency']}")
    print(f"   因白名单保留: {kept_reasons['whitelist']}")
    print(f"   结果已保存至: {GENESIS_API_INDEX_FILE}")
    print("=" * 40)


def _parse_llm_json_response(text: str) -> dict:
    if not text:
        return {}
    cleaned = text.replace("```json", "").replace("```", "").strip()
    return json.loads(cleaned)


def enrich_knowledge_base() -> bool:
    """读取 genesis_api_index.json，用 LLM 补全后写回同一文件。成功返回 True。"""
    from tqdm import tqdm

    from llm_utils import LLMClient

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ 请设置环境变量 DEEPSEEK_API_KEY（可在 rag_demo/.env 中配置）。")
        return False

    if not os.path.exists(GENESIS_API_INDEX_FILE):
        print(f"❌ 找不到文件: {GENESIS_API_INDEX_FILE}（请先运行 python indexer_api.py 生成）")
        return False

    llm = LLMClient(
        provider="openai",
        api_key=api_key,
        base_url=os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com"),
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    )

    with open(GENESIS_API_INDEX_FILE, "r", encoding="utf-8") as f:
        kb_data = json.load(f)

    print(f"🚀 开始精准增强 {len(kb_data)} 个 API...")
    enriched_data = []

    for entry in tqdm(kb_data, desc="Enriching", unit="api"):
        api_id = entry["api_id"]
        needs_summary = entry.get("summary", "No summary available.") == "No summary available."

        obj = get_object_by_path(api_id)
        raw_doc = inspect.getdoc(obj) if obj is not None else None
        if not raw_doc:
            enriched_data.append(entry)
            continue

        user_content = json.dumps(
            {
                "api_name": api_id,
                "signature": entry["signature"],
                "raw_docstring": raw_doc,
                "parameter_list": [p["name"] for p in entry["parameters"]],
                "tasks": {
                    "generate_summary": needs_summary,
                    "extract_parameter_descs": True,
                    "extract_constraints": True,
                },
            },
            indent=2,
        )
        messages = [
            {"role": "system", "content": ENRICH_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        try:
            response = llm.chat(messages, temperature=0.1)
            if response is None:
                raise ValueError("LLM 返回空")
            ai_result = _parse_llm_json_response(response)

            if needs_summary and ai_result.get("summary"):
                entry["summary"] = ai_result["summary"]

            ai_param_descs = ai_result.get("parameter_descs", {})
            for param in entry["parameters"]:
                pname = param["name"]
                if pname in ai_param_descs and ai_param_descs[pname]:
                    param["desc"] = ai_param_descs[pname]

            new_constraints = ai_result.get("constraints", [])
            if new_constraints:
                entry["constraints"] = new_constraints

        except Exception as e:
            tqdm.write(f"[Error] {api_id}: {e}")

        enriched_data.append(entry)

    with open(GENESIS_API_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(enriched_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 增强完成！结果已写回: {GENESIS_API_INDEX_FILE}")
    return True


def _print_usage():
    print(
        "用法:\n"
        "  python indexer_api.py         索引抽取 + 清洗 → knowledge_base/genesis_api_index.json（不调用 LLM）\n"
        "  python indexer_api.py enrich  仅 LLM 增强（读取并写回 genesis_api_index.json）"
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in ("-h", "--help", "help"):
            _print_usage()
            sys.exit(0)
        if cmd == "enrich":
            sys.exit(0 if enrich_knowledge_base() else 1)
        print(f"❌ 未知参数: {cmd!r}\n")
        _print_usage()
        sys.exit(1)

    kb = build_index()
    clean_knowledge_base(kb)
