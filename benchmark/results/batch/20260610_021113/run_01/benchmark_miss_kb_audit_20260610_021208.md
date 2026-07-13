# Benchmark 未命中 API 审查报告

- 生成时间: 2026-06-10T02:12:08
- 分析结果数: 1

## Run: 20260610_021113
- 结果文件: `D:\Desktop\Genesis\Genesis-main\rag_demo\benchmark\results\batch\20260610_021113\run_01\benchmark_20260610_021113.json`
- 任务数: 100
- miss 总数: 331
- KB 不存在: 0 (0.0%)
- KB 存在但未召回: 331 (100.0%)
- 检索参数: `{"rewrite_mode": "none", "hyde_route": "unit", "n_api": 6, "n_code": 1, "n_snippet": 3, "n_error": 0, "n_units": 5, "tag_filter": null, "include_core_api": true, "core_api_limit": 40, "rerank": false, "rerank_top_n": null, "rerank_oversample": 2.0}`

### Top KB 存在但未召回 API
- `genesis.morphs.Plane`: 72
- `genesis.surfaces.Default`: 45
- `genesis.morphs.Box`: 34
- `genesis.morphs.Sphere`: 33
- `genesis.options.renderers.Rasterizer`: 28
- `genesis.Scene.add_camera`: 13
- `genesis.surfaces.Rough`: 11
- `genesis.options.morphs.Sphere`: 10
- `genesis.options.morphs.Plane`: 10
- `genesis.morphs.Cylinder`: 9
- `genesis.options.morphs.Box`: 9
- `genesis.surfaces.Iron`: 9
- `genesis.morphs.Mesh`: 5
- `genesis.Scene.add_sensor`: 5
- `genesis.morphs.MJCF`: 4
