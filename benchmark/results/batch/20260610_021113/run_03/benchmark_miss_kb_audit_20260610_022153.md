# Benchmark 未命中 API 审查报告

- 生成时间: 2026-06-10T02:21:53
- 分析结果数: 1

## Run: 20260610_021647
- 结果文件: `D:\Desktop\Genesis\Genesis-main\rag_demo\benchmark\results\batch\20260610_021113\run_03\benchmark_20260610_021647.json`
- 任务数: 100
- miss 总数: 254
- KB 不存在: 0 (0.0%)
- KB 存在但未召回: 254 (100.0%)
- 检索参数: `{"rewrite_mode": "hyde", "hyde_route": "fourway", "n_api": 6, "n_code": 1, "n_snippet": 3, "n_error": 0, "n_units": 5, "tag_filter": null, "include_core_api": true, "core_api_limit": 40, "rerank": false, "rerank_top_n": null, "rerank_oversample": 2.0}`

### Top KB 存在但未召回 API
- `genesis.surfaces.Default`: 45
- `genesis.morphs.Plane`: 38
- `genesis.morphs.Box`: 30
- `genesis.options.renderers.Rasterizer`: 28
- `genesis.morphs.Sphere`: 17
- `genesis.surfaces.Rough`: 17
- `genesis.Scene.add_camera`: 13
- `genesis.options.morphs.Box`: 9
- `genesis.surfaces.Iron`: 9
- `genesis.morphs.Cylinder`: 8
- `genesis.morphs.Mesh`: 4
- `genesis.options.morphs.Sphere`: 4
- `genesis.surfaces.Gold`: 4
- `genesis.options.morphs.Plane`: 3
- `genesis.Scene.add_sensor`: 3
