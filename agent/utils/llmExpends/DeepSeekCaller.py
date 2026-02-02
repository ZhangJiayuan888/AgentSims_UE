import os
import json
import aiohttp
from agent.utils.llmExpends.BasicCaller import BasicCaller
import sys

class DeepSeekCaller(BasicCaller):
    def __init__(self):
        self.model = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
        self.api_key = self._load_api_key()
        self.base_url = "https://api.siliconflow.cn/v1/chat/completions"


    def _load_api_key(self):
        abs_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        with open(os.path.join(abs_path, "config", "api_key.json")) as f:
            return json.load(f).get("siliconflow")

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
        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_url, headers=headers, json=data) as resp:
                response = await resp.json()
                return response['choices'][0]['message']['content']
