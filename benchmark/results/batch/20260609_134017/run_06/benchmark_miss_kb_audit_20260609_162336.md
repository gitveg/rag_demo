# Benchmark 未命中 API 审查报告

- 生成时间: 2026-06-09T16:23:36
- 分析结果数: 1

## Run: 20260609_154908
- 结果文件: `D:\Desktop\Genesis\phys_agent\benchmark\results\batch\20260609_134017\run_06\benchmark_20260609_154908.json`
- 任务数: 100
- miss 总数: 223
- KB 不存在: 0 (0.0%)
- KB 存在但未召回: 223 (100.0%)
- 检索参数: `{"rewrite_mode": "hyde", "hyde_route": "fourway", "n_api": 6, "n_code": 1, "n_snippet": 3, "n_error": 0, "n_units": 5, "tag_filter": null, "include_core_api": true, "core_api_limit": 40, "rerank": true, "rerank_top_n": 10, "rerank_oversample": 2.0}`

### Top KB 存在但未召回 API
- `genesis.surfaces.Default`: 45
- `genesis.options.renderers.Rasterizer`: 28
- `genesis.morphs.Box`: 25
- `genesis.morphs.Plane`: 23
- `genesis.surfaces.Rough`: 16
- `genesis.morphs.Sphere`: 13
- `genesis.Scene.add_camera`: 12
- `genesis.surfaces.Iron`: 9
- `genesis.options.morphs.Box`: 8
- `genesis.options.morphs.Plane`: 6
- `genesis.morphs.Cylinder`: 6
- `genesis.morphs.Mesh`: 3
- `genesis.surfaces.Glass`: 3
- `genesis.surfaces.Gold`: 3
- `genesis.Scene.add_sensor`: 3
