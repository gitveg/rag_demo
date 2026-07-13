# Benchmark 未命中 API 审查报告

- 生成时间: 2026-06-09T14:12:48
- 分析结果数: 1

## Run: 20260609_134122
- 结果文件: `D:\Desktop\Genesis\phys_agent\benchmark\results\batch\20260609_134017\run_02\benchmark_20260609_134122.json`
- 任务数: 100
- miss 总数: 106
- KB 不存在: 0 (0.0%)
- KB 存在但未召回: 106 (100.0%)
- 检索参数: `{"rewrite_mode": "hyde", "hyde_route": "unit", "n_api": 6, "n_code": 1, "n_snippet": 3, "n_error": 0, "n_units": 5, "tag_filter": null, "include_core_api": true, "core_api_limit": 40, "rerank": false, "rerank_top_n": null, "rerank_oversample": 2.0}`

### Top KB 存在但未召回 API
- `genesis.surfaces.Default`: 28
- `genesis.options.renderers.Rasterizer`: 27
- `genesis.surfaces.Rough`: 8
- `genesis.surfaces.Iron`: 8
- `genesis.morphs.Cylinder`: 5
- `genesis.morphs.Box`: 5
- `genesis.Scene.add_camera`: 4
- `genesis.surfaces.Gold`: 3
- `genesis.surfaces.Glass`: 2
- `genesis.surfaces.Metal`: 2
- `genesis.surfaces.Emission`: 2
- `genesis.sensors.DepthCameraPattern`: 2
- `genesis.surfaces.Aluminium`: 2
- `genesis.surfaces.Water`: 1
- `genesis.options.surfaces.Glass`: 1
