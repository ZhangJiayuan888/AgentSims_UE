import os
import json
import aiohttp
import re
from agent.utils.llmExpends.BasicCaller import BasicCaller
import sys


class DeepSeekCaller(BasicCaller):
    def __init__(self):
        self.model = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
        self.api_key = self._load_api_key()
        self.base_url = "https://api.siliconflow.cn/v1/chat/completions"

    def _load_api_key(self):
        # 注意：这里路径层级可能需要根据你实际的文件位置微调，保持你原本逻辑即可
        abs_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        config_path = os.path.join(abs_path, "config", "api_key.json")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f).get("siliconflow")
        except Exception:
            # 兼容不同系统的路径问题或文件不存在的情况
            return os.getenv("SILICONFLOW_API_KEY", "")

    async def ask(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 1024
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=data) as resp:
                    if resp.status != 200:
                        print(f"DeepSeek API Error: {resp.status} - {await resp.text()}")
                        return "{}"

                    response = await resp.json()
                    content = response['choices'][0]['message']['content']

                    # --- Cleaning Logic (关键修改) ---
                    if content:
                        # 1. 移除 <think>...</think> 标签及其包裹的思维过程
                        # flags=re.DOTALL 让 . 能够匹配换行符
                        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)

                        # 2. 去除首尾空白字符
                        content = content.strip()
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
