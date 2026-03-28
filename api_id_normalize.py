"""
将 AST / 用户代码里常见的「顶层再导出」路径映射为知识库中的规范 api_id 前缀。

genesis/__init__.py 从 genesis.options 引入 morphs、sensors 等，故 gs.morphs.* 在 AST 中
常为 genesis.morphs.*，而 KB 条目多为 genesis.options.morphs.*。
"""
from __future__ import annotations

from typing import Optional, Set

# (公开前缀, 知识库规范前缀)
_PUBLIC_TO_CANONICAL_PREFIXES: tuple[tuple[str, str], ...] = (
    ("genesis.morphs.", "genesis.options.morphs."),
    ("genesis.sensors.", "genesis.options.sensors."),
    ("genesis.renderers.", "genesis.options.renderers."),
    ("genesis.surfaces.", "genesis.options.surfaces."),
    ("genesis.textures.", "genesis.options.textures."),
)


def normalize_api_id_for_kb(api_id: str) -> str:
    if not api_id or not api_id.startswith("genesis."):
        return api_id
    for public, canonical in _PUBLIC_TO_CANONICAL_PREFIXES:
        if api_id.startswith(public):
            return canonical + api_id[len(public) :]
    return api_id


def resolve_api_to_known(api_id: str, known_apis: Set[str]) -> Optional[str]:
    """若原始或归一化后的 id 在白名单中，返回应写入索引的规范 id（优先保留 KB 中已存在的写法）。"""
    if api_id in known_apis:
        return api_id
    normalized = normalize_api_id_for_kb(api_id)
    if normalized in known_apis:
        return normalized
    return None
