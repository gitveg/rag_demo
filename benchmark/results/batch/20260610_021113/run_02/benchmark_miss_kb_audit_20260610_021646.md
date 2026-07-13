# Benchmark 未命中 API 审查报告

- 生成时间: 2026-06-10T02:16:46
- 分析结果数: 1

## Run: 20260610_021209
- 结果文件: `D:\Desktop\Genesis\Genesis-main\rag_demo\benchmark\results\batch\20260610_021113\run_02\benchmark_20260610_021209.json`
- 任务数: 100
- miss 总数: 101
- KB 不存在: 0 (0.0%)
- KB 存在但未召回: 101 (100.0%)
- 检索参数: `{"rewrite_mode": "hyde", "hyde_route": "unit", "n_api": 6, "n_code": 1, "n_snippet": 3, "n_error": 0, "n_units": 5, "tag_filter": null, "include_core_api": true, "core_api_limit": 40, "rerank": false, "rerank_top_n": null, "rerank_oversample": 2.0}`

### Top KB 存在但未召回 API
- `genesis.options.renderers.Rasterizer`: 28
- `genesis.surfaces.Rough`: 13
- `genesis.surfaces.Default`: 12
- `genesis.surfaces.Iron`: 9
- `genesis.Scene.add_camera`: 5
- `genesis.surfaces.Gold`: 4
- `genesis.surfaces.Glass`: 3
- `genesis.morphs.Cylinder`: 3
- `genesis.options.surfaces.Glass`: 2
- `genesis.surfaces.Metal`: 2
- `genesis.morphs.Box`: 2
- `genesis.surfaces.Emission`: 2
- `genesis.surfaces.Aluminium`: 2
- `genesis.options.morphs.Terrain`: 1
- `genesis.morphs.URDF`: 1
