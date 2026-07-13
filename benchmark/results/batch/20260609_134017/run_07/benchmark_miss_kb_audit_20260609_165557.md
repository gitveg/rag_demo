# Benchmark 未命中 API 审查报告

- 生成时间: 2026-06-09T16:55:57
- 分析结果数: 1

## Run: 20260609_162338
- 结果文件: `D:\Desktop\Genesis\phys_agent\benchmark\results\batch\20260609_134017\run_07\benchmark_20260609_162338.json`
- 任务数: 100
- miss 总数: 112
- KB 不存在: 0 (0.0%)
- KB 存在但未召回: 112 (100.0%)
- 检索参数: `{"rewrite_mode": "hyde", "hyde_route": "unit", "n_api": 6, "n_code": 1, "n_snippet": 3, "n_error": 0, "n_units": 5, "tag_filter": null, "include_core_api": true, "core_api_limit": 40, "rerank": true, "rerank_top_n": 8, "rerank_oversample": 2.0}`

### Top KB 存在但未召回 API
- `genesis.options.renderers.Rasterizer`: 28
- `genesis.surfaces.Default`: 23
- `genesis.surfaces.Rough`: 11
- `genesis.surfaces.Iron`: 9
- `genesis.Scene.add_camera`: 4
- `genesis.morphs.Cylinder`: 4
- `genesis.morphs.Box`: 4
- `genesis.surfaces.Gold`: 3
- `genesis.morphs.Plane`: 2
- `genesis.morphs.URDF`: 2
- `genesis.surfaces.Glass`: 2
- `genesis.surfaces.Metal`: 2
- `genesis.surfaces.Emission`: 2
- `genesis.surfaces.Aluminium`: 2
- `genesis.Scene.add_emitter`: 2
