import os

# 动态导入库，防止用户缺少某个库时直接报错
try:
    from google import genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

class LLMClient:
    def __init__(self, provider="openai", api_key=None, base_url=None, model=None):
        """
        统一的 LLM 客户端
        :param provider: "openai" (包括 DeepSeek) 或 "gemini"
        :param api_key: 你的 API Key
        :param base_url: OpenAI 兼容接口的地址 (Gemini 不需要)
        :param model: 模型名称 (例如 "deepseek-chat" 或 "gemini-2.0-flash")
        """
        self.provider = provider.lower()
        self.model = model
        self.api_key = api_key

        # --- 初始化 Gemini ---
        if self.provider == "gemini":
            if not HAS_GEMINI:
                raise ImportError("检测到 provider='gemini'，但未安装库。请运行: pip install google-genai")
            self.client = genai.Client(api_key=self.api_key)
            # 设置默认模型
            if not self.model: self.model = "gemini-2.0-flash"

        # --- 初始化 OpenAI/DeepSeek ---
        elif self.provider == "openai":
            if not HAS_OPENAI:
                raise ImportError("检测到 provider='openai'，但未安装库。请运行: pip install openai")
            self.client = OpenAI(api_key=self.api_key, base_url=base_url)
            # 设置默认模型
            if not self.model: self.model = "deepseek-chat"
            
        else:
            raise ValueError(f"不支持的 provider: {provider}")

    def chat(self, messages, temperature=0.1):
        """
        统一对外接口。
        不管内部是 Gemini 还是 OpenAI，外部调用者都只传入标准的 messages 列表。
        """
        if self.provider == "gemini":
            return self._chat_gemini(messages, temperature)
        elif self.provider == "openai":
            return self._chat_openai(messages, temperature)

    def _chat_openai(self, messages, temperature):
        """内部处理 OpenAI 请求"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[OpenAI Error]: {e}")
            return None

    def _chat_gemini(self, messages, temperature):
        """内部处理 Gemini 请求 (自动适配格式)"""
        try:
            # 1. 格式转换: 从 OpenAI messages 提取 System Prompt 和 User Content
            system_instruction = None
            user_content = ""
            
            for msg in messages:
                role = msg.get('role')
                content = msg.get('content', '')
                
                if role == 'system':
                    system_instruction = content
                elif role == 'user':
                    user_content += content + "\n"
                elif role == 'assistant':
                    # 如果有多轮对话，可以在这里拼接历史，或者使用 Gemini 的 chat session
                    # 这里的 Agent 主要是单轮任务，简单处理即可
                    pass

            # 2. 配置参数
            config = types.GenerateContentConfig(
                temperature=temperature,
                system_instruction=system_instruction
            )

            # 3. 发送请求
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_content,
                config=config
            )
            return response.text
            
        except Exception as e:
            print(f"[Gemini Error]: {e}")
            return None