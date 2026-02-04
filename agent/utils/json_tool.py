import json
import re


def extract_json_from_text(text: str):
    """
    从 LLM 的回复中提取 JSON 对象。
    兼容 DeepSeek/Llama 等模型可能输出的 Markdown 格式或思维链文本。
    """
    try:
        # 尝试直接解析
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 1. 尝试提取 ```json ... ``` 代码块
    pattern = r"```json\s*(\{.*?\})\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass

    # 2. 尝试提取最外层的大括号 {}
    # 贪婪匹配第一个 { 和最后一个 }
    pattern = r"(\{.*\})"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass

    # 3. 最后的手段：尝试修复常见的单引号问题（某些模型喜欢用单引号）
    try:
        fixed_text = text.replace("'", '"')
        match = re.search(r"(\{.*\})", fixed_text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
    except:
        pass

    # 如果都失败了，返回 None 或空字典，并打印错误以便调试
    print(f"ERROR: Failed to extract JSON from LLM response:\n{text}")
    return {}
