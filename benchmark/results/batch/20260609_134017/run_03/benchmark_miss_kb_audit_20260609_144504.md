# Benchmark 未命中 API 审查报告

- 生成时间: 2026-06-09T14:45:04
- 分析结果数: 1

## Run: 20260609_141250
- 结果文件: `D:\Desktop\Genesis\phys_agent\benchmark\results\batch\20260609_134017\run_03\benchmark_20260609_141250.json`
- 任务数: 100
- miss 总数: 282
- KB 不存在: 0 (0.0%)
- KB 存在但未召回: 282 (100.0%)
- 检索参数: `{"rewrite_mode": "hyde", "hyde_route": "fourway", "n_api": 6, "n_code": 1, "n_snippet": 3, "n_error": 0, "n_units": 5, "tag_filter": null, "include_core_api": true, "core_api_limit": 40, "rerank": false, "rerank_top_n": null, "rerank_oversample": 2.0}`

### Top KB 存在但未召回 API
- `genesis.surfaces.Default`: 45
- `genesis.morphs.Plane`: 45
- `genesis.morphs.Box`: 34
- `genesis.options.renderers.Rasterizer`: 28
- `genesis.morphs.Sphere`: 23
- `genesis.surfaces.Rough`: 15
- `genesis.Scene.add_camera`: 13
- `genesis.options.morphs.Box`: 9
- `genesis.surfaces.Iron`: 9
- `genesis.morphs.Cylinder`: 8
- `genesis.options.morphs.Plane`: 8
- `genesis.options.morphs.Sphere`: 6
- `genesis.morphs.Mesh`: 5
- `genesis.surfaces.Gold`: 4
- `genesis.surfaces.Glass`: 3
