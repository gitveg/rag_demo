import sys
import subprocess
import os
from datetime import datetime
from llm_utils import LLMClient
from rag_engine import SmartRAG

log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
code_dir = "aigc_code"
os.makedirs(code_dir, exist_ok=True)

class GenesisAgent:
    def __init__(self, max_retries=3):
        # 初始化 LLM (DeepSeek)
        self.llm = LLMClient(
            provider="openai",
            api_key="sk-061e03c70f63402bb363bcd2960622d2",
            base_url="https://api.deepseek.com",
            model="deepseek-reasoner"  # R1 模型逻辑能力强，适合改错
        )
        self.rag = SmartRAG(llm_client=self.llm)
        self.max_retries = max_retries # 最大重试次数

    def _save_code(self, code):
        """生成带时间戳的文件名并保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filename = f"genesis_sim_{timestamp}.py"
        save_path = os.path.join(code_dir, filename)
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(code)
        return save_path

    def _execute_code(self, save_path):
        """
        [终极修复版] 运行代码文件
        1. 合并 stdout 和 stderr，防止报错信息漏掉
        2. 使用 -u 参数禁用 Python 缓冲
        3. 强制 UTF-8 编码
        """
        print(f"   >> 正在尝试运行: {save_path} ...")
        print("   (注意: 如果弹出了 Genesis 可视化窗口，请在确认无误后手动关闭窗口，Agent 才能获取执行结果)")
        
        # 环境变量设置
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1" # 强制禁用缓冲

        try:
            # 关键修改 1: 加上 "-u" 参数
            cmd = [sys.executable, "-u", save_path]
            
            result = subprocess.run(
                cmd,
                # 关键修改 2: 不要用 capture_output=True
                # 而是显式把 stderr 重定向到 stdout，这样所有信息都在 stdout 里
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, 
                
                encoding='utf-8',
                errors='replace',
                env=env, 
                timeout=300 # 保持 5 分钟超时
            )
            
            # 无论成功失败，输出都在 stdout 里
            output = result.stdout
            # 在 _execute_code 内部，return 之前加上：
            print(f"   [Debug] Return Code: {result.returncode}")
            print(f"   [Debug] Output Len: {len(output)}")
            
            if result.returncode == 0:
                return True, output
            else:
                # 此时 output 包含了之前的 stdout 和 stderr 内容
                return False, output
                
        except subprocess.TimeoutExpired:
            return False, "Execution timed out (程序运行超时，可能是陷入死循环或窗口未关闭)"
        except Exception as e:
            return False, f"Agent Execution Error: {str(e)}"

    def run(self, user_query):
        print(f"=== 接到任务: {user_query} ===")
        
        # Step 1: 检索
        print("1. [RAG] 正在分析意图并检索 API 文档...")
        api_context = self.rag.retrieve(user_query)
        
        # Step 2: 初始 Prompt
        system_prompt = f"""
        你是一个精通 Genesis (Genesis-Embodied-AI) 物理仿真引擎的 Python 专家。
        你的任务：编写一个可运行的 Python 脚本。
        1. 仔细阅读提供的 "Reference Code" (参考代码)。如果参考代码的功能与用户需求相似，请**优先模仿**参考代码的写法（参数命名、类初始化方式）。
        2. 即使参考代码不完全匹配，也请参考其 `add_entity` 和 `Material` 的参数写法。
        3. 对于 API 文档中显示为 `(**data)` 的参数，**绝对不要**臆造 `scale`、`rotation` 等通用 3D 属性，除非你在参考代码中看到了它们。通常请使用 `pos` (位置), `quat` (四元数), `radius` (半径), `size` (尺寸)。
        
        参考 API:
        ----------------------------------------
        {api_context}
        ----------------------------------------
        
        要求：
        1. 必须包含 `import genesis as gs` 和 `gs.init(backend=gs.gpu)`。
        2. 必须有 `scene.build()` 和可视化循环。
        3. 输出纯 Python 代码，不要用 Markdown 格式。
        """
        
        # 维护一个对话历史，用于由错改对
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]

        current_code = ""
        
        # Step 3: 生成与修正循环
        for attempt in range(self.max_retries + 1):
            print(f"\n2. [LLM] 正在生成代码 (尝试 {attempt+1}/{self.max_retries + 1})...")
            
            # 调用 LLM
            response = self.llm.chat(messages, temperature=0.2)
            
            # 清理代码 (DeepSeek Reasoner 可能会输出 <think> 标签，这里做简单处理，通常 API 会返回正文)
            # 如果包含 Markdown，去掉它
            current_code = response.replace("```python", "").replace("```", "").strip()
            
            # Step 4: 保存文件
            filename = self._save_code(current_code)
            print(f"   >> 代码已保存至: {filename}")
            
            # Step 5: 执行代码
            print("3. [Exec] 正在执行代码检测...")
            success, output = self._execute_code(filename)
            print(f"Len(output) = {len(output)}")
            
            if success:
                print(f"\n✅ [Success] 代码执行成功！文件名: {filename}")
                return filename
            else:
                print(f"❌ [Error] 代码执行失败。")
                
                # 1. 安全起见，先把完整报错存下来，方便你去文件里查
                log_file = f"demo.log"
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(output)
                print(f"   >> 完整报错日志已保存至: {log_file} (如果控制台看不清，请直接打开此文件)")

                # 2. 智能显示：只提取 Traceback 及其之后的内容
                if "Traceback (most recent call last)" in output:
                    # 找到 Traceback 的起始位置
                    start_idx = output.find("Traceback (most recent call last)")
                    # 打印从 Traceback 开始的所有内容
                    print("\n--- 关键报错信息 ---")
                    print(output[start_idx:]) 
                else:
                    # 如果不是 Python 报错（可能是 C++ 直接崩了），显示最后 2000 字符
                    print("\n--- 关键报错信息 (Tail) ---")
                    print(output[-2000:] if len(output) > 2000 else output)
                # ================= 新代码结束 =================
                
                # 如果还没到最后一次尝试，就把错误喂回给 LLM
                if attempt < self.max_retries:
                    print("   >> 正在请求 LLM 修正代码...")
                    
                    # 构建修复 Prompt
                    error_feedback = f"""
                    上一次生成的代码运行报错了。
                    代码文件: {filename}
                    报错信息:
                    {output}
                    
                    请分析报错原因，并根据之前的 API 文档修正代码。直接输出完整的修正后代码。
                    """
                    
                    # 将错误信息追加到对话历史中
                    messages.append({"role": "assistant", "content": current_code})
                    messages.append({"role": "user", "content": error_feedback})
                else:
                    print("\n🚫 [Failed] 达到最大重试次数，修复失败。")
        
        return None

if __name__ == "__main__":
    # 实例化 Agent，设置最多自动修错 2 次
    agent = GenesisAgent(max_retries=2)
    
    # 测试案例
    # task = "创建一个场景，里面有一个红色的球体从 5米高空掉落到地面上。"
    task = "创建一个场景，一个黄色的方块从3米高空砸向正下方地面上的紫色方块"
    # task = "生成一个错误的场景代码故意测试报错" # 你可以解开这个注释测试 Agent 怎么修 Bug
    
    final_script = agent.run(task)