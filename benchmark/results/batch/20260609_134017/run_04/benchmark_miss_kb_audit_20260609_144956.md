# Benchmark 未命中 API 审查报告

- 生成时间: 2026-06-09T14:49:56
- 分析结果数: 1

## Run: 20260609_144506
- 结果文件: `D:\Desktop\Genesis\phys_agent\benchmark\results\batch\20260609_134017\run_04\benchmark_20260609_144506.json`
- 任务数: 100
- miss 总数: 321
- KB 不存在: 0 (0.0%)
- KB 存在但未召回: 321 (100.0%)
- 检索参数: `{"rewrite_mode": "none", "hyde_route": "unit", "n_api": 6, "n_code": 1, "n_snippet": 3, "n_error": 0, "n_units": 5, "tag_filter": null, "include_core_api": true, "core_api_limit": 40, "rerank": true, "rerank_top_n": 10, "rerank_oversample": 2.0}`

### Top KB 存在但未召回 API
- `genesis.morphs.Plane`: 70
- `genesis.surfaces.Default`: 45
- `genesis.morphs.Box`: 33
- `genesis.morphs.Sphere`: 32
- `genesis.options.renderers.Rasterizer`: 28
- `genesis.Scene.add_camera`: 12
- `genesis.options.morphs.Sphere`: 10
- `genesis.surfaces.Rough`: 10
- `genesis.options.morphs.Plane`: 10
- `genesis.morphs.Cylinder`: 9
- `genesis.options.morphs.Box`: 9
- `genesis.surfaces.Iron`: 9
- `genesis.morphs.MJCF`: 4
- `genesis.morphs.Mesh`: 4
- `genesis.Scene.add_sensor`: 4
