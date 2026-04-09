import inspect
import json
import genesis as gs
import re
import os
import math

# -----------------------------------------------------------
# 辅助函数
# -----------------------------------------------------------
def clean_type_str(annotation):
    """清理类型注解，使其更易读"""
    if annotation == inspect.Parameter.empty:
        return "Any"
    
    # 获取类名或字符串表示
    if hasattr(annotation, "__name__"):
        type_str = annotation.__name__
    else:
        type_str = str(annotation)
    
    # 移除 typing 前缀，如 typing.List -> List
    return type_str.replace("typing.", "").replace("genesis.", "gs.")

def get_summary_from_doc(obj):
    """提取 Docstring 的第一句话作为 Summary"""
    doc = inspect.getdoc(obj)
    if not doc:
        return "No summary available."
    
    # 取第一段，并去除换行符，限制长度
    first_paragraph = doc.split('\n\n')[0].replace('\n', ' ')
    # 简单的截断策略，保证 summary 短小
    return first_paragraph[:150] + ("..." if len(first_paragraph) > 150 else "")

# genesis/__init__.py 从 genesis.engine 再导出到包顶层，用户写作 gs.<name>，api_id 应为 genesis.<name>.*
_ENGINE_EXPORT_TO_PUBLIC_PREFIXES: tuple[tuple[str, str], ...] = (
    # materials / states / force_fields：实现模块 genesis.engine.* → 公开 genesis.*
    ("genesis.engine.materials", "genesis.materials"),
    ("genesis.engine.states", "genesis.states"),
    ("genesis.engine.force_fields", "genesis.force_fields"),
)


def canonicalize_public_api_id(api_id: str) -> str:
    """
    将实现层路径规范为与 genesis/__init__.py 顶层导出一致的 api_id，
    以便与频率报告、清洗白名单、enricher 的 get_object_by_path(gs.*) 一致。
    """
    for engine_prefix, public_prefix in _ENGINE_EXPORT_TO_PUBLIC_PREFIXES:
        if api_id.startswith(engine_prefix):
            return public_prefix + api_id[len(engine_prefix) :]
    return api_id


def format_simplified_signature(name, sig):
    """
    生成极简签名，去除类型注解，只保留参数名和默认值。
    例如: add_entity(morph, material=None)
    """
    params_str_list = []
    
    for param_name, param in sig.parameters.items():
        if param_name == 'self': continue
        
        # 核心修改：完全忽略 param.annotation (类型注解)
        
        # 处理默认值
        if param.default != inspect.Parameter.empty:
            # 如果默认值是 None，显示 =None
            # 如果是字符串，显示 ='value'
            def_val = str(param.default)
            # 简单清理一下过长的默认值 (比如很长的 Tensor)
            if len(def_val) > 20: 
                def_val = "..." 
            params_str_list.append(f"{param_name}={def_val}")
        elif param.kind == inspect.Parameter.VAR_KEYWORD:
            params_str_list.append(f"**{param_name}")
        elif param.kind == inspect.Parameter.VAR_POSITIONAL:
            params_str_list.append(f"*{param_name}")
        else:
            # 必填参数，只放名字
            params_str_list.append(param_name)
            
    # 重新拼装
    return f"{name}({', '.join(params_str_list)})"

# -----------------------------------------------------------
# 核心提取逻辑
# -----------------------------------------------------------
def extract_strict_schema(obj, api_id, layer_tag):
    """
    完全符合 Target Schema 的提取函数
    """
    # 1. 基础字段
    entry = {
        "api_id": api_id,
        "type": "class" if inspect.isclass(obj) else "method",
        "signature": "",
        "summary": get_summary_from_doc(obj),
        "parameters": [],
        "constraints": [], # inspect 无法提取逻辑约束，初始化为空，等待 LLM 填充
        "domain_tags": [layer_tag.lower()] # 将层级转化为 Tag
    }

    # 2. 提取签名和参数
    try:
        # 确定目标对象 (如果是类，看 __init__)
        target_obj = obj.__init__ if inspect.isclass(obj) else obj
        
        # 获取签名对象
        sig = inspect.signature(target_obj)
        
        # A. 生成 Signature 字段
        # 获取短名用于签名显示，例如 genesis.Scene.add_entity -> add_entity
        short_name = api_id.split('.')[-1]
        entry["signature"] = format_simplified_signature(short_name, sig)

        # B. 生成 Parameters 列表
        for name, param in sig.parameters.items():
            if name == 'self': continue
            
            # 判断是否必填 (没有默认值就是必填)
            is_required = (param.default == inspect.Parameter.empty)
            
            # 获取默认值的字符串表示
            default_val = str(param.default) if not is_required else None
            
            # 类型清理
            type_str = clean_type_str(param.annotation)

            # 构造参数对象
            param_entry = {
                "name": name,
                "type": type_str,
                "desc": "", # 预留位：后续步骤通过 LLM 阅读 Docstring 来填充
                "required": is_required
            }
            
            # 如果是 **kwargs，特殊标记，方便后续 AI 识别并展开
            # 审查/生成代码时：遇到 [Auto-Detect] 就不要做参数名强约束，只把它当“该 API 存在可变关键字参数，细节不确定”。
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                param_entry["desc"] = "[Auto-Detect] Variable keyword arguments. Needs LLM expansion."
                param_entry["type"] = "Dict"
                param_entry["required"] = False

            entry["parameters"].append(param_entry)

    except (ValueError, TypeError):
        # 处理无法获取签名的情况 (如 C++ 绑定)
        entry["signature"] = f"{api_id.split('.')[-1]}(...args)"
        entry["parameters"] = [
            {"name": "*args", "type": "Any", "desc": "Unknown parameters", "required": False}
        ]

    return entry

# -----------------------------------------------------------
# 递归遍历器
# -----------------------------------------------------------

def process_module(module, layer_tag, visited, recurse_submodules=True):
    """
    [增强版 v2] 递归提取模块信息，增加 Pydantic 噪音过滤
    """
    results = []
    
    try:
        members = inspect.getmembers(module)
    except Exception:
        return results

    for name, obj in members:
        if name.startswith("_"): continue
        
        # 1. 处理子模块
        # 注意：当 module=genesis(gs) 时，如果递归进入所有子模块，会导致全库都被打上同一个 layer_tag。
        # 因此这里提供 recurse_submodules 开关：用于“只抽取顶层 API”，不下钻子模块。
        if inspect.ismodule(obj):
            if recurse_submodules and hasattr(obj, "__name__") and obj.__name__.startswith("genesis"):
                if not obj.__name__.startswith(module.__name__ + "."):
                    continue
                if obj.__name__ not in visited:
                    visited.add(obj.__name__)
                    results.extend(process_module(obj, layer_tag, visited, recurse_submodules=True))
            continue

        full_name = f"{module.__name__}.{name}"
        if full_name in visited: continue
        visited.add(full_name)

        api_id = canonicalize_public_api_id(full_name)

        # 2. 提取类
        if inspect.isclass(obj):
            # 过滤掉非 genesis 定义的类
            if hasattr(obj, "__module__") and obj.__module__:
                if not obj.__module__.startswith("genesis"): continue

            results.append(extract_strict_schema(obj, api_id, layer_tag))
            
            # 3. [关键修改] 提取类方法时的严格过滤
            for method_name, method in inspect.getmembers(obj):
                # A. 必须是函数或方法
                if not (inspect.isfunction(method) or inspect.ismethod(method)): continue
                
                # B. 忽略私有方法
                if method_name.startswith("_"): continue

                # C. [新增] 名称黑名单过滤 (秒杀 Pydantic 噪音)
                if method_name in METHOD_BLOCKLIST:
                    continue

                # D. [新增] 严格来源检查 (Deep Inspection)
                try:
                    # 解包 wrapper (如果有装饰器) 找到真身
                    real_func = inspect.unwrap(method)
                    # 检查定义该方法的模块
                    if hasattr(real_func, "__module__") and real_func.__module__:
                        # 如果这个方法是 pydantic 或 python 原生定义的，丢弃
                        # 只保留 genesis 自己写的方法
                        if not real_func.__module__.startswith("genesis"):
                            continue
                except Exception:
                    pass # 如果无法解包，暂时放过，依靠名字过滤

                method_id = canonicalize_public_api_id(f"{full_name}.{method_name}")
                results.append(extract_strict_schema(method, method_id, layer_tag))
                
    return results

# -----------------------------------------------------------
# Core API 打标逻辑
# -----------------------------------------------------------
def _ensure_tag(domain_tags, tag):
    if not domain_tags:
        return [tag]
    if tag in domain_tags:
        return domain_tags
    return domain_tags + [tag]

def mark_core_apis(cleaned_data, freq_data, core_ratio=0.02, min_core=30, extra_core_allowlist=None):
    """
    将一小部分“常用且重要”的 API 追加 domain_tags=['core']，用于 RAG 时无条件注入上下文，降低幻觉。

    规则：
    - 从频率报告中按 count 排序，取 top core_ratio（默认 2%）作为 core 候选
    - 额外允许通过 allowlist 强行标 core（兜底关键基础 API）
    """
    if not cleaned_data:
        return {"core_added": 0, "core_total": 0, "top_n": 0}

    api_ids_in_kb = set(item.get("api_id") for item in cleaned_data if item.get("api_id"))

    # 频率表：api_name -> count
    freq_rows = [row for row in (freq_data or []) if isinstance(row, dict) and row.get("api_name") in api_ids_in_kb]
    freq_rows.sort(key=lambda r: r.get("count", 0), reverse=True)

    top_n = max(min_core, int(math.ceil(len(cleaned_data) * core_ratio)))
    top_ids = set([row["api_name"] for row in freq_rows[:top_n]])

    allowlist = set(extra_core_allowlist or [])
    allowlist = set([api for api in allowlist if api in api_ids_in_kb])

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

# -----------------------------------------------------------
# 主执行入口
# -----------------------------------------------------------
def build_index():
    print("🛠️  正在执行符合 Target Schema 的 API 提取...")
    
    kb_data = []
    visited = set()
    
    # 定义白名单模块 (二八定律)
    # 说明：
    # - 这里的 layer_tag 用于“领域/模块分类”（geometry/material/...），不是“重要性 core”。
    # - “重要性 core”由 clean_knowledge_base() 中基于频率报告的 mark_core_apis() 负责追加。
    # - 对 genesis(gs) 这一层：只抽取顶层 API（不递归子模块），避免全库都被打同一个标签。
    targets = [
        (gs, "engine", False),          # 顶层：Scene/init 等（不下钻）
        (gs.morphs, "geometry", True),  # 几何体
        (gs.materials, "material", True), # 材质
        (gs.states, "engine", True),   # 仿真状态（engine.states → gs.states）
        (gs.force_fields, "engine", True),  # 力场（engine.force_fields → gs.force_fields）
        (gs.surfaces, "surface", True), # 表面属性
        (gs.options, "config", True),   # 配置项 (包含 Solver, Vis 等)
    ]

    # 执行提取
    for target in targets:
        # 兼容旧格式 (mod, tag) 与新格式 (mod, tag, recurse_submodules)
        if len(target) == 2:
            mod, tag = target
            recurse = True
        else:
            mod, tag, recurse = target
        kb_data.extend(process_module(mod, tag, visited, recurse_submodules=recurse))
        
    # 保存结果
    with open(API_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(kb_data, f, indent=2, ensure_ascii=False)
        
    print(f"✅ 提取完成！生成文件: {API_INDEX_FILE}")
    print(f"📊 总条目数: {len(kb_data)}")
    
    # 打印一条预览，检查是否符合 Schema
    if kb_data:
        print("\n🔎 Schema 校验 (Preview First Entry):")
        print(json.dumps(kb_data[0], indent=2, ensure_ascii=False))

def clean_knowledge_base():
    print("🧹 开始执行 API 知识库数据清洗...")
    
    # 1. 加载数据
    if not os.path.exists(API_INDEX_FILE) or not os.path.exists(FREQUENCY_FILE):
        print("❌ 错误: 找不到输入文件，请检查文件名。")
        return

    with open(API_INDEX_FILE, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    with open(FREQUENCY_FILE, "r", encoding="utf-8") as f:
        freq_data = json.load(f)

    # 2. 构建“实战白名单”集合 (从频率表中提取)
    # 我们只关心 api_name，不关心具体次数，只要出现过就认为是有用的
    used_apis_set = set([item['api_name'] for item in freq_data])
    print(f"📊 频率报告中包含 {len(used_apis_set)} 个实战 API。")

    cleaned_data = []
    dropped_count = 0
    kept_reasons = {"frequency": 0, "whitelist": 0}

    # 3. 核心清洗循环
    for api_entry in raw_data:
        api_id = api_entry['api_id']
        
        should_keep = False
        reason = ""

        # 规则 A: 是否在频率表中出现过？
        # 注意：需要处理模糊匹配，比如 freq 表里可能有 genesis.Scene，但这能保住 genesis.Scene.__init__
        # 但为了严谨，我们先看精确匹配
        if api_id in used_apis_set:
            should_keep = True
            reason = "frequency"
        
        # 规则 B: 是否属于严格白名单模块？
        # 如果不在频率表里，但它是核心模块下的 API，也保留 (防止范例覆盖不全)
        else:
            for prefix in STRICT_WHITELIST_PREFIXES:
                if api_id.startswith(prefix):
                    should_keep = True
                    reason = "whitelist"
                    break
        
        # 执行保留或丢弃
        if should_keep:
            cleaned_data.append(api_entry)
            kept_reasons[reason] += 1
        else:
            dropped_count += 1
            # 调试：打印几个被丢弃的典型，确认逻辑是否正确
            if dropped_count <= 5 or "CTRL_MODE" in api_id:
                print(f"   [丢弃] {api_id} (既不在频率表，也不在白名单)")

    # 3.5 给少量关键 API 打 core tag（用于运行时固定注入上下文）
    # 兜底：把最基础的“搭场景必备 API”强行标 core，避免示例覆盖不全导致幻觉
    EXTRA_CORE_ALLOWLIST = {
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
        extra_core_allowlist=EXTRA_CORE_ALLOWLIST,
    )
    print(f"🏷️ Core API 打标完成：新增 {core_stats['core_added']}，当前 core 总数 {core_stats['core_total']}（top_n={core_stats['top_n']}）")

    # 3.6 手动注入：Viewer.save_video（场景通过 scene.viewer 访问，用于保存仿真录屏为视频），标为 core
    SAVE_VIDEO_API = {
        "api_id": "genesis.Scene.viewer.save_video",
        "type": "method",
        "signature": "save_video(filename=None)",
        "summary": "Save the stored frames from the viewer to a video file (e.g. MP4). Use after scene.viewer is running with record enabled: call scene.start_recording() before stepping, then scene.viewer.save_video(filename='out.mp4') after simulation (or use Viewer.close_external() then save_video).",
        "parameters": [
            {"name": "filename", "type": "str | None", "desc": "Path to save the video file. If None, a file dialog is opened.", "required": False}
        ],
        "constraints": [],
        "domain_tags": ["engine", "core"],
    }
    if not any(e.get("api_id") == SAVE_VIDEO_API["api_id"] for e in cleaned_data):
        cleaned_data.append(SAVE_VIDEO_API)
        print(f"   📌 已注入 Core API: {SAVE_VIDEO_API['api_id']}")

    # 4. 保存结果
    with open(CLEANED_KB_FILE, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

    # 5. 打印统计
    total_raw = len(raw_data)
    total_clean = len(cleaned_data)
    reduction_rate = (dropped_count / total_raw) * 100

    print("\n" + "="*40)
    print("✅ 清洗完成！统计报告：")
    print(f"   原始 API 数量: {total_raw}")
    print(f"   清洗后 API 数量: {total_clean}")
    print(f"   🗑️  剔除数量: {dropped_count} (压缩率: {reduction_rate:.1f}%)")
    print("-" * 40)
    print(f"   因频率保留: {kept_reasons['frequency']}")
    print(f"   因白名单保留: {kept_reasons['whitelist']}")
    print(f"   结果已保存至: {CLEANED_KB_FILE}")
    print("="*40)

if __name__ == "__main__":
    import os as _os
    _BASE_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    _KB_DIR   = _os.path.join(_BASE_DIR, "knowledge_base")

    API_INDEX_FILE  = _os.path.join(_KB_DIR, "genesis_api_index_v6.json")
    FREQUENCY_FILE  = _os.path.join(_KB_DIR, "api_frequency_report.json")
    CLEANED_KB_FILE = _os.path.join(_KB_DIR, "genesis_knowledge_base_clean.json")
    STRICT_WHITELIST_PREFIXES = [
    "genesis.Scene",          # 核心场景类及其方法
    "genesis.morphs",         # 几何体
    "genesis.materials",      # 材质（与 gs.materials 一致）
    "genesis.states",         # 状态（与 gs.states 一致）
    "genesis.force_fields",   # 力场（与 gs.force_fields 一致）
    "genesis.engine.materials",  # 旧版索引未规范化时的兜底
    "genesis.engine.states",
    "genesis.engine.force_fields",
    "genesis.surfaces",       # 表面参数
    "genesis.options",        # 配置项
    ]
    # ================= 新增：噪音方法黑名单 =================
    # 这些是 Pydantic、Python Object 或其他 Mixin 带来的常见无用方法
    METHOD_BLOCKLIST = {
        "json", "dict", "copy", "schema", "parse_raw", "parse_obj", "parse_file",
        "from_orm", "construct", "update_forward_refs", "validate", "model_construct",
        "model_copy", "model_dump", "model_dump_json", # Pydantic V2
        "model_json_schema", "model_validate",         # Pydantic V2
        "keys", "values", "items", "get", "pop",       # Dict-like noise
    }
    build_index()
    clean_knowledge_base()