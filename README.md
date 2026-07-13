Agent 必看：代码运行环境为conda环境，执行代码前先 conda activate env_genesis。

## 项目背景

本项目是我们正在研发的**物理仿真 Agent** 的知识库构建与检索生成（RAG）模块。当前自研物理引擎尚未接入 / 尚未实现，故暂时以 [Genesis](https://github.com/Genesis-Embodied-AI/Genesis) 物理引擎作为仿真后端替代（API 形态与仿真效果大差不差），待自研引擎就绪后再行切换。

## 仓库架构

rag_demo/
├── rag_engine.py        ← 灌库主引擎
├── llm_utils.py         ← LLM 工具类
├── indexers/            ← 各类知识库构建脚本（单步独立）
├── feedback_loop/       ← 执行闭环反馈系统（成功代码→知识单元 / 失败→错误记忆&API约束，完整子系统）
├── knowledge_base/      ← 生产 JSON 数据
├── tools/               ← 辅助工具（健康检查、测试查询）
├── tests/               ← 测试文件 + synthetic_tests/
├── archive/             ← 旧版本 / 中间产物 / 备份
├── examples/            ← Genesis 范例源码（不动）
└── genesis_chroma_db/   ← 向量库（不动）