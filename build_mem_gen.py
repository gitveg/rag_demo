import os
import json
import time
from tqdm import tqdm
from agent import GenesisAgent # 直接复用你强大的 Agent
from llm_utils import LLMClient
import dotenv

dotenv.load_dotenv()

# ================= 配置 =================
OUTPUT_DIR = "./synthetic_tests"
NUM_SCENARIOS = 10 # 这一批次生成多少个测试用例

# 确保目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 初始化 LLM (用于生成 Prompt)
llm = LLMClient(
    provider="openai",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    model="deepseek-chat"
)

# 初始化你的 RAG Agent (被测试对象)
rag_agent = GenesisAgent()

def generate_test_prompts():
    """让 LLM 生成一些可能会触发幻觉的物理仿真指令"""
    print("😈 Instigator is brainstorming scenarios...")
    
    prompt = f"""
    Generate {NUM_SCENARIOS} distinct user instructions for Genesis Physics Engine.
    Focus on specific API usages that might be tricky or undocumented.
    
    Categories to cover:
    1. Soft body interaction (creating meshes, setting stiffness).
    2. Fluid simulation (MPM emitter, viscosity).
    3. Camera/Viewer settings (resolution, recording).
    4. Rigid body dynamics (friction, damping).
    
    Return ONLY a JSON list of strings:
    ["Create a soft bunny...", "Set up a water emitter...", ...]
    """
    
    try:
        response = llm.chat([{"role": "user", "content": prompt}], temperature=0.8)
        clean_json = response.replace("```json", "").replace("```", "").strip()
        prompts = json.loads(clean_json)
        return prompts
    except Exception as e:
        print(f"❌ Prompt generation failed: {e}")
        return [
            "Create a soft bunny falling on a rigid floor.",
            "Pour water into a cup using MPM.",
            "Create a scene with gravity set to zero."
        ]

def main():
    # 1. 生成考题
    prompts = generate_test_prompts()
    print(f"✅ Generated {len(prompts)} prompts. Starting RAG Agent...")
    
    for i, user_query in enumerate(tqdm(prompts, desc="Agent Coding")):
        print(f"\n--- Scenario {i+1}: {user_query} ---")
        
        # 2. 让 RAG Agent 答题 (生成代码)
        # solve 方法内部已经包含了 search_code -> search_api -> generate 的全流程
        try:
            code_content = rag_agent.solve(user_query)
            
            # 3. 保存代码 (覆盖掉 agent 内部的 save 逻辑，按测试集命名)
            timestamp = time.strftime("%H%M%S")
            filename = f"test_{i}_{timestamp}.py"
            file_path = os.path.join(OUTPUT_DIR, filename)
            
            # 在文件头写入 Prompt，方便 Judge 读取上下文
            full_content = f'"""\nUser Query: {user_query}\n"""\n\n' + code_content
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(full_content)
                
        except Exception as e:
            print(f"⚠️ Agent failed on this query: {e}")

    print(f"\n🎉 Generation Complete. Check folder: {OUTPUT_DIR}")
    print("Next Step: Run 'python build_mem_judge.py' to execute and analyze.")

if __name__ == "__main__":
    main()