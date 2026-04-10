"""一次性审计：知识单元 code 中的 Genesis API 是否被 key_apis 覆盖。"""
import ast
import json
import os
import re

COMMON_API_BLOCKLIST = {
    "genesis.init",
    "genesis.Scene",
    "genesis.Scene.__init__",
    "genesis.Scene.build",
    "genesis.Scene.step",
    "genesis.Scene.reset",
}


class GenesisImportVisitor(ast.NodeVisitor):
    def __init__(self):
        self.api_calls = set()
        self.imports = {}

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name == "genesis":
                self.imports[alias.asname or "genesis"] = "genesis"
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and node.module.startswith("genesis"):
            for alias in node.names:
                self.imports[alias.asname or alias.name] = f"{node.module}.{alias.name}"
        self.generic_visit(node)

    def visit_Attribute(self, node):
        full_name = self._get_full_name(node)
        if full_name and full_name.startswith("genesis."):
            self.api_calls.add(full_name)
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            full_name = self._get_full_name(node.func)
            if full_name and full_name.startswith("genesis."):
                self.api_calls.add(full_name)
        self.generic_visit(node)

    def _get_full_name(self, node):
        if isinstance(node, ast.Attribute):
            prefix = self._get_full_name(node.value)
            if prefix:
                return f"{prefix}.{node.attr}"
        elif isinstance(node, ast.Name):
            if node.id in self.imports:
                return self.imports[node.id]
        return None


def gs_refs_in_code(code: str) -> set:
    out = set()
    for m in re.finditer(
        r"\bgs\.([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)", code
    ):
        out.add("genesis." + m.group(1))
    return out


def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kb_path = os.path.join(base, "knowledge_base", "genesis_api_index.json")
    units_path = os.path.join(base, "knowledge_base", "genesis_knowledge_units.json")

    with open(kb_path, encoding="utf-8") as f:
        known_apis = {e["api_id"] for e in json.load(f) if e.get("api_id")}
    with open(units_path, encoding="utf-8") as f:
        units = json.load(f)

    ast_mismatch = 0
    parse_fail = 0
    gs_gap_units = []

    for u in units:
        code = u.get("code") or ""
        key = set(u.get("key_apis") or [])
        try:
            tree = ast.parse(code)
        except SyntaxError:
            parse_fail += 1
            continue
        v = GenesisImportVisitor()
        v.visit(tree)
        in_kb = {a for a in v.api_calls if a in known_apis}
        filtered = {a for a in in_kb if a not in COMMON_API_BLOCKLIST}
        if filtered != key:
            ast_mismatch += 1

        gs_cands = {a for a in gs_refs_in_code(code) if a in known_apis}
        gs_cands -= COMMON_API_BLOCKLIST
        missing_gs = gs_cands - key
        if missing_gs:
            gs_gap_units.append(
                (u.get("unit_id"), sorted(missing_gs), len(missing_gs))
            )

    print(f"units total: {len(units)}")
    print(f"AST parse fail: {parse_fail}")
    print(
        "AST-filtered (indexer rules) != key_apis: "
        f"{ast_mismatch} / {len(units) - parse_fail}"
    )
    print(
        "units with gs.* (in KB) present in source but missing from key_apis: "
        f"{len(gs_gap_units)}"
    )
    print("\n--- sample units with gs.* gap (first 12) ---")
    for uid, miss, n in gs_gap_units[:12]:
        print(f"  {uid}: missing {n} -> {miss[:10]}{'...' if len(miss) > 10 else ''}")


if __name__ == "__main__":
    main()
