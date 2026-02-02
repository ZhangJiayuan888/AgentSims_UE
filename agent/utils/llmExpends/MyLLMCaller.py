import os
import json
import aiohttp
from agent.utils.llmExpends.BasicCaller import BasicCaller

# 获取当前文件的绝对路径
abs_path = os.path.dirname(os.path.realpath(__file__))


class GLM4Caller(BasicCaller):
    def __init__(self) -> None:
        self.model = "glm-4-flash"
        self.api_key = "540e8011693c421abd67c10d7652e660.2VfAXrNULAfFc4Bv"
        # 从配置文件中读取智谱AI GLM-4的API密钥，确保config/api_key.json中包含"glm-4-flash"字段
        with open(os.path.join(abs_path, "..", "..", "..", "config", "api_key.json"), "r",
                  encoding="utf-8") as api_file:
            api_keys = json.loads(api_file.read())
            self.api_key = api_keys.get("glm-4-flash", "")
        if not self.api_key:
            raise ValueError("智谱AI GLM-4的API密钥未找到")

    async def ask(self, prompt: str) -> str:
        url = "https://www.bigmodel.cn/dev/api/normal-model/glm-4"
        headers = {
            "Content-Type": "application/json",
            # 根据智谱AI的要求，将API密钥添加到请求头中
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "prompt": prompt,
            "temperature": 0,  # 根据需求设置温度
            "max_tokens": 1000  # 根据实际情况设置生成长度限制
            # 可根据智谱AI文档添加其他参数，如 top_p、stop 等
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"请求失败: {response.status} {error_text}")
                data = await response.json()
                # 根据智谱AI返回的数据结构解析结果，假设返回格式为：{"result": "生成的内容"}
                result = data.get("result", "")
                return result

# from typing import List, Dict, Any
# import os
# import json
# import jwt
# import time
# import aiohttp
# from zhipuai import AsyncZhipuAI
# from agent.utils.llmExpends.BasicCaller import BasicCaller
#
# abs_path = os.path.dirname(os.path.realpath(__file__))
#
#
# class GLM4Caller(BasicCaller):
#     def __init__(self) -> None:
#         self.model = "glm-4-flash"  # 官方模型名称
#         self.api_key = "540e8011693c421abd67c10d7652e660.2VfAXrNULAfFc4Bv"
#         self.base_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
#
#         # 从配置文件读取API密钥
#         with open(os.path.join(abs_path, "..", "..", "..", "config", "api_key.json"), "r",
#                   encoding="utf-8") as api_file:
#             api_keys = json.loads(api_file.read())
#             self.api_key = api_keys["zhipuai"]  # 配置项需改为zhipuai
#
#         if not self.api_key:
#             raise ValueError("ZhipuAI API key not found")
#
#         # 初始化异步客户端
#         self.client = AsyncZhipuAI(api_key=self.api_key)
#
#     def _generate_jwt_token(self) -> str:
#         """生成符合智谱AI要求的JWT鉴权令牌"""
#         try:
#             id_part, secret_part = self.api_key.split(".")
#             payload = {
#                 "api_key": id_part,
#                 "exp": int(time.time() * 1000) + 3600 * 1000,  # 1小时有效期
#                 "timestamp": int(time.time() * 1000)
#             }
#             return jwt.encode(
#                 payload,
#                 secret_part,
#                 algorithm="HS256",
#                 headers={"alg": "HS256", "sign_type": "SIGN"}
#             )
#         except Exception as e:
#             raise ValueError(f"API Key格式错误: {str(e)}") from e
#
#     async def ask(self, prompt: str) -> str:
#         """异步调用GLM-4-Flash接口"""
#         counter = 0
#         max_retries = 3
#         result = ""
#
#         while counter < max_retries:
#             try:
#                 # 构造符合智谱规范的请求头
#                 headers = {
#                     "Authorization": f"Bearer {self._generate_jwt_token()}",
#                     "Content-Type": "application/json"
#                 }
#
#                 # 请求参数优化
#                 data = {
#                     "model": self.model,
#                     "messages": [{"role": "user", "content": prompt}],
#                     "temperature": 0.95,  # 提高创造性
#                     "top_p": 0.7,
#                     "max_tokens": 4096  # 支持最大输出长度
#                 }
#
#                 # 异步HTTP请求
#                 async with aiohttp.ClientSession() as session:
#                     async with session.post(
#                             self.base_url,
#                             headers=headers,
#                             json=data,
#                             timeout=30  # 超时时间优化
#                     ) as response:
#                         response.raise_for_status()
#                         result_data = await response.json()
#                         result = result_data['choices'][0]['message']['content']
#                         break
#
#             except aiohttp.ClientResponseError as e:
#                 print(f"API错误: HTTP {e.status} - {e.message}")
#                 if e.status == 429:  # 速率限制
#                     await asyncio.sleep(2 ** counter)  # 指数退避
#                 counter += 1
#             except (aiohttp.ClientError, KeyError) as e:
#                 print(f"请求异常: {str(e)}")
#                 counter += 1
#
#         return result


                #     self.headers = {
                #         "Content-Type": "application/json"
                #     }
                #     data = {
                #         "question": request
                #     }
                #     response = requests.post(self.api_url, headers=self.headers, json=data)
                #     print(response)
                #     return response.json()
                # except Exception as e:
                #     print("err: ", e)
                #     counter += 1
                # return result
                #     # 调用智谱API（同步调用示例，异步需用aiohttp改造）
                #     response = self.client.chat.completions.create(
                #         model=self.model,
                #         messages=[{"role": "user", "content": prompt}],
                #         temperature=0.7
                #     )
                #     return response.choices[0].message.content
                #
                # except Exception as e:
                #     print(f"Zhipu API Error (attempt {counter + 1}): {str(e)}")
                #     counter += 1
                #     # 可针对特定错误码处理，如429限频
                #     if hasattr(e, 'status_code'):
                #         if e.status_code == 429:
                #             await asyncio.sleep(2 ** counter)  # 指数退避
                # return json.dumps(result)
                #












# # MyLLMCaller.py
# import json
# import time
# from typing import Optional
#
# import requests
#
# from agent.utils.llmExpends.BasicCaller import BasicCaller
#
#
# class GLM4Caller(BasicCaller):
#     def __init__(self, model_name: str = "glm-4", api_key: Optional[str] = None):
#         super().__init__(model_name)
#         self.base_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
#         self.api_key = api_key or self._load_default_key()
#         self.max_retries = 3  # 最大重试次数
#         self.timeout = 30  # 单次请求超时时间(秒)
#
#         # 流式响应处理参数
#         self.stream = False
#         self.stream_delay = 0.1  # 流式响应间隔
#
#     def _load_default_key(self) -> str:
#         """从配置文件加载API密钥"""
#         try:
#             with open("config/api_key.json") as f:
#                 return json.load(f).get("glm-4", "")
#         except Exception as e:
#             raise ValueError("未找到GLM-4 API密钥，请在config/api_key.json配置") from e
#
#     def call(self, prompt: str, **kwargs) -> str:
#         """核心调用方法，支持普通/流式响应"""
#         headers = {
#             "Authorization": f"Bearer {self.api_key}",
#             "Content-Type": "application/json"
#         }
#
#         payload = {
#             "model": self.model_name,
#             "messages": [{"role": "user", "content": prompt}],
#             "temperature": kwargs.get("temperature", 0.95),
#             "top_p": kwargs.get("top_p", 0.7),
#             "max_tokens": kwargs.get("max_tokens", 1024),
#             "stream": self.stream
#         }
#
#         # 请求重试逻辑
#         for attempt in range(self.max_retries):
#             try:
#                 response = requests.post(
#                     self.base_url,
#                     headers=headers,
#                     json=payload,
#                     timeout=self.timeout,
#                     stream=self.stream
#                 )
#
#                 if response.status_code == 200:
#                     if self.stream:
#                         return self._handle_stream_response(response)
#                     else:
#                         return response.json()["choices"][0]["message"]["content"]
#                 else:
#                     self._handle_api_error(response)
#
#             except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
#                 if attempt == self.max_retries - 1:
#                     raise RuntimeError(f"API调用失败: {str(e)}")
#                 time.sleep(2 ** attempt)  # 指数退避
#
#     def _handle_stream_response(self, response) -> str:
#         """处理流式响应"""
#         full_content = []
#         for chunk in response.iter_lines():
#             if chunk:
#                 decoded_chunk = json.loads(chunk.decode("utf-8"))
#                 if "content" in decoded_chunk["choices"][0]["delta"]:
#                     content = decoded_chunk["choices"][0]["delta"]["content"]
#                     full_content.append(content)
#                     time.sleep(self.stream_delay)  # 模拟实时输出
#         return "".join(full_content)
#
#     def _handle_api_error(self, response):
#         """错误处理"""
#         error_info = response.json().get("error", {})
#         error_code = error_info.get("code", "unknown")
#         error_msg = error_info.get("message", "未知错误")
#         raise RuntimeError(f"API错误 [{error_code}]: {error_msg}")
#
#     @property
#     def _llm_type(self) -> str:
#         return "glm-4"
