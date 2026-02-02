from typing import List, Dict, Any
import json
import re
from agent.utils.llmExpends.MyLLMCaller import GLM4Caller
from agent.utils.llmExpends.DeepSeekCaller import DeepSeekCaller
from agent.utils.llmExpends.BasicCaller import BasicCaller
from agent.utils.llmExpends.gpt4 import GPT4Caller
from agent.utils.llmExpends.gpt35 import GPT35Caller

# TODO: make the LLMCaller more general
choices = {
    'glm-4-flash': GLM4Caller,
    'gpt-4': GPT4Caller,
    'gpt-3.5': GPT35Caller,
    'deepseek-ai/DeepSeek-R1-Distill-Qwen-7B': DeepSeekCaller
}


def get_caller(model: str) -> BasicCaller:
    return choices[model]


class LLMCaller:
    def __init__(self, model: str) -> None:
        self.model = model
        self.caller = get_caller(model)()

    async def ask(self, prompt: str) -> Dict[str, Any]:
        result = await self.caller.ask(prompt)
        try:
            result = json.loads(result)
        except Exception:
            try:
                info = re.findall(r"\{.*\}", result, re.DOTALL)
                if info:
                    info = info[-1]
                    result = json.loads(info)
                else:
                    result = {"response": result}
            except Exception:
                result = {"response": result}
        return result
