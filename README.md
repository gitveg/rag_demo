

## 仓库架构

rag_demo/
├── rag_engine.py        ← 灌库主引擎
├── llm_utils.py         ← LLM 工具类
├── indexers/            ← 各类知识库构建脚本（单步独立）
├── mem_builder/         ← 错误记忆构建自动机（完整子系统）
├── knowledge_base/      ← 生产 JSON 数据
├── tools/               ← 辅助工具（健康检查、测试查询）
├── tests/               ← 测试文件 + synthetic_tests/
├── archive/             ← 旧版本 / 中间产物 / 备份
├── examples/            ← Genesis 范例源码（不动）
└── genesis_chroma_db/   ← 向量库（不动）