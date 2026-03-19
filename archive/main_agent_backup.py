from llm_utils import LLMClient
from rag_engine import SmartRAG
import time

class GenesisAgent:
    def __init__(self):
        # self.llm = LLMClient(
        #     provider="gemini",
        #     api_key="AIzaSyD_78l6Rz_5TGvtP-JMgKvofNDXmp102xg",     # 你的 Google API Key
        #     model="gemini-2.5-flash"  # 你想用的模型
        # )
        self.llm = LLMClient(
            provider="openai",
            api_key="sk-061e03c70f63402bb363bcd2960622d2",
            base_url="https://api.deepseek.com",
            model="deepseek-reasoner"  # 你想用的模型
        )
        # RAG 引擎会复用这个 llm 实例
        self.rag = SmartRAG(llm_client=self.llm)

    def run(self, user_query):
        print(f"=== 接到任务: {user_query} ===")
        
        # Step 1: 检索 (这里包含了 Agent 的意图分析过程)
        print("1. 正在分析意图并检索 API 文档...")
        api_context = self.rag.retrieve(user_query)
        
        # Step 2: 组装 Prompt
        print("2. 正在生成代码...")
        system_prompt = f"""
        你是一个精通 Genesis (Genesis-Embodied-AI) 物理仿真引擎的 Python 专家。
        
        你的任务：根据用户的描述和提供的 API 参考文档，编写一个完整的、可运行的 Python 脚本。
        
        参考的 API 文档如下 (请严格基于此文档使用参数，不要臆造不存在的参数):
        ----------------------------------------
        {api_context}
        ----------------------------------------
        
        代码要求：
        1. 必须包含 `import genesis as gs`。
        2. 必须初始化环境 `gs.init(backend=gs.gpu)`。
        3. 必须创建一个 `scene` 并添加物体。
        4. 必须包含 `scene.build()`。
        5. 最后必须有一个可视化循环 (while loop 或 for loop) 让场景动起来。
        6. 输出纯文本代码，不要包含 Markdown 格式 (```python)。
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
        
        # Step 3: 生成代码
        code = self.llm.chat(messages, temperature=0.2)
        
        # 清理可能存在的 Markdown 标记
        if code:
            code = code.replace("```python", "").replace("```", "").strip()
        
        return code

if __name__ == "__main__":
    agent = GenesisAgent()
    
    # 测试案例
    task = "创建一个场景，里面有一个红色的球体从 5米高空掉落到地面上。"
    
    generated_code = agent.run(task)
    
    if generated_code:
        print("\n" + "="*40)
        print(" GENESIS 仿真脚本生成完毕 ")
        print("="*40 + "\n")
        print(generated_code)
        
        # 可选：保存到文件
        with open("run_genesis_sim.py", "w", encoding="utf-8") as f:
            f.write(generated_code)
        print("\n>> 代码已保存至 'run_genesis_sim.py'，请在终端运行它。")