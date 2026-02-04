import os
import json
import aiohttp
import re
from agent.utils.llmExpends.BasicCaller import BasicCaller
import sys


class DeepSeekCaller(BasicCaller):
    def __init__(self):
        # 保持与你配置一致的模型名称
        self.model = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
        self.api_key = self._load_api_key()
        # 保持 SiliconFlow 的 API 地址
        self.base_url = "https://api.siliconflow.cn/v1/chat/completions"

    def _load_api_key(self):
        # 动态获取项目根目录路径，防止路径错误
        try:
            # 向上回溯4层找到 config 目录
            abs_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            config_path = os.path.join(abs_path, "config", "api_key.json")
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f).get("siliconflow")
        except Exception as e:
            print(f"Warning: Failed to load api_key.json: {e}")
            return os.getenv("SILICONFLOW_API_KEY", "")

    async def ask(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # [关键修复] 增加 System Prompt 强制约束 JSON 格式
        # R1 模型有时会忽略 prompt 中的格式要求，system prompt 权重更高
        messages = [
            {"role": "system",
             "content": "You are a helpful assistant. You must response with PURE JSON format directly. Do not output markdown code blocks. Do not output thinking process in the final response."},
            {"role": "user", "content": prompt}
        ]

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.6,  # 稍微降低温度以提高格式稳定性
            "max_tokens": 4096
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=data) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        print(f"DeepSeek API Error: {resp.status} - {error_text}")
                        return "{}"

                    response = await resp.json()
                    content = response['choices'][0]['message']['content']

                    # --- Cleaning Logic (核心清洗逻辑) ---
                    # 解决日志中出现的 "response": "Okay, I need to help..." 问题
                    if content:
                        # 1. 移除 <think>...</think> 标签及其包裹的思维过程 (DOTALL模式匹配换行)
                        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)

                        # 2. 移除 Markdown 代码块标记 (```json 和 ```)
                        content = re.sub(r'```json', '', content, flags=re.IGNORECASE)
                        content = re.sub(r'```', '', content)

                        # 3. 去除首尾空白字符
                        content = content.strip()

                        # 4. 简单的兜底：如果清洗后还是不是 { 开头，尝试找第一个 {
                        # 这能解决前面还有闲聊文本的情况
                        if not content.startswith('{'):
                            match = re.search(r'\{.*\}', content, re.DOTALL)
                            if match:
                                content = match.group(0)
                            else:
                                # [新增] 如果清洗后仍不是 JSON 对象（例如模型返回 "Idle" 或其他乱码）
                                # 强制返回空 JSON，防止 downstream 接收到字符串导致崩溃
                                print(
                                    f"[DeepSeekCaller] Warning: Malformed/Non-JSON output detected: '{content[:50]}...' -> Fallback to {{}}")
                                content = "{}"
                    # -------------------------------

                    return content
        except Exception as e:
            print(f"DeepSeekCaller Request Error: {e}")
            return "{}"
# import os
# import json
# import aiohttp
# from agent.utils.llmExpends.BasicCaller import BasicCaller
# import sys
#
# class DeepSeekCaller(BasicCaller):
#     def __init__(self):
#         self.model = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
#         self.api_key = self._load_api_key()
#         self.base_url = "https://api.siliconflow.cn/v1/chat/completions"
#
#
#     def _load_api_key(self):
#         abs_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
#         with open(os.path.join(abs_path, "config", "api_key.json")) as f:
#             return json.load(f).get("siliconflow")
#
#     async def ask(self, prompt: str) -> str:
#         headers = {
#             "Authorization": f"Bearer {self.api_key}",
#             "Content-Type": "application/json"
#         }
#         data = {
#             "model": self.model,
#             "messages": [{"role": "user", "content": prompt}],
#             "temperature": 0.7,
#             "max_tokens": 1024
#         }
#         async with aiohttp.ClientSession() as session:
#             async with session.post(self.base_url, headers=headers, json=data) as resp:
#                 response = await resp.json()
#                 return response['choices'][0]['message']['content']
