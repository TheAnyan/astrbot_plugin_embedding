"""
embedding_providers.py
实现对各个embedding服务商的支持
"""
import httpx
import requests
import json
import asyncio
import openai
from google import genai

from datetime import datetime as dt
from typing import Optional, List
from astrbot.api import logger

TEXT = "test"

class Provider:
    def __init__(self, config: dict) -> None:
        self.config = config
        self.model = config['embed_model']
        self.dim:Optional[int] = None 


    def _get_embedding(self, text: str) -> Optional[list]:
        """获取embedding(同步版本)"""
        embeddings=self._get_embeddings([text])
        return embeddings[0] if embeddings else None

    def _get_embeddings(self, texts: List[str]) -> Optional[List[list]]:
        """获取embedding(同步版本)"""
        return NotImplementedError()
    
    async def _get_embedding_async(self, text: str) -> Optional[list]:
        embeddings = await self._get_embeddings_async([text])
        return embeddings[0] if embeddings else None
    
    async def _get_embeddings_async(self, texts: List[str]) -> Optional[List[list]]:
        return self._get_embeddings(texts)
    

    def get_model_name(self) -> int:
        """获取embeddingmodel"""
        return self.config['embed_model']

    def get_provider_name(self) -> int:
        """获取embeddingmodel"""
        return self.__class__.__name__


    def get_embedding(self, text: str) -> Optional[list]:
        """获取embedding(同步版本)"""
        try:
            response = self._get_embedding(text)
            return response
        except requests.exceptions.Timeout:
            logger.error(f"[{self.get_provider_name()}] 请求超时")
        except requests.exceptions.ConnectionError:
            logger.error(f"[{self.get_provider_name()}] 连接错误")
        except requests.exceptions.SSLError:
            logger.error(f"[{self.get_provider_name()}] SSL证书验证失败")
        except requests.exceptions.RequestException as e:
            logger.error(f"[{self.get_provider_name()}] 请求发生异常:{str(e)}")
        except json.JSONDecodeError:
            logger.error(f"[{self.get_provider_name()}] 响应数据解析失败")
        except Exception as e:
            logger.error(f"[{self.get_provider_name()}] 未知错误: {str(e)}")

    def get_embeddings(self, texts: List[str]) -> Optional[List[list]]:
        """获取embedding(同步版本)"""
        batch_size = 16
        all_embeddings = []
        try:
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = self._get_embeddings(batch)
                if response:
                    all_embeddings.extend(response)
            return all_embeddings
        except requests.exceptions.Timeout:
            logger.error(f"[{self.get_provider_name()}] 请求超时")
        except requests.exceptions.ConnectionError:
            logger.error(f"[{self.get_provider_name()}] 连接错误")
        except requests.exceptions.SSLError:
            logger.error(f"[{self.get_provider_name()}] SSL证书验证失败")
        except requests.exceptions.RequestException as e:
            logger.error(f"[{self.get_provider_name()}] 请求发生异常:{str(e)}")
        except json.JSONDecodeError:
            logger.error(f"[{self.get_provider_name()}] 响应数据解析失败")
        except Exception as e:
            logger.error(f"[{self.get_provider_name()}] 未知错误: {str(e)}")

    def get_dim(self) -> int:
        """获取embedding维数"""
        self.is_available()
        return self.dim


    def is_available(self) -> bool:
        """通过实际嵌入请求验证服务可用性"""
        emb = self.get_embedding(TEXT)
        if bool(emb) and isinstance(emb, list):
            self.dim = len(emb)
            return True
        else:
            return False



    async def get_embedding_async(self, text: str) -> Optional[list]:
        """获取embedding(异步版本)"""
        try:
            response = await self._get_embedding_async(text)
            return response
        except httpx.HTTPStatusError as e:
            logger.error(f"[{self.get_provider_name()}] API错误: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"[{self.get_provider_name()}] 网络请求失败: {str(e)}")
        except requests.exceptions.Timeout:
            logger.error(f"[{self.get_provider_name()}] 请求超时")
        except requests.exceptions.ConnectionError:
            logger.error(f"[{self.get_provider_name()}] 连接错误")
        except requests.exceptions.SSLError:
            logger.error(f"[{self.get_provider_name()}] SSL证书验证失败")
        except requests.exceptions.RequestException as e:
            logger.error(f"[{self.get_provider_name()}] 请求发生异常:{str(e)}")
        except json.JSONDecodeError:
            logger.error(f"[{self.get_provider_name()}] 响应数据解析失败")
        except Exception as e:
            logger.error(f"[{self.get_provider_name()}] 未知错误: {str(e)}")

    async def get_embeddings_async(self, texts: List[str]) -> Optional[List[list]]:
        """获取embedding(异步版本)"""
        batch_size = 16
        all_embeddings = []
        try:
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = await self._get_embeddings_async(batch)
                if response:
                    all_embeddings.extend(response)
            return all_embeddings
        except httpx.HTTPStatusError as e:
            logger.error(f"[{self.get_provider_name()}] API错误: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"[{self.get_provider_name()}] 网络请求失败: {str(e)}")
        except requests.exceptions.Timeout:
            logger.error(f"[{self.get_provider_name()}] 请求超时")
        except requests.exceptions.ConnectionError:
            logger.error(f"[{self.get_provider_name()}] 连接错误")
        except requests.exceptions.SSLError:
            logger.error(f"[{self.get_provider_name()}] SSL证书验证失败")
        except requests.exceptions.RequestException as e:
            logger.error(f"[{self.get_provider_name()}] 请求发生异常:{str(e)}")
        except json.JSONDecodeError:
            logger.error(f"[{self.get_provider_name()}] 响应数据解析失败")
        except Exception as e:
            logger.error(f"[{self.get_provider_name()}] 未知错误: {str(e)}")

    async def get_dim_async(self) -> int:
        """获取embedding维数(异步版本)"""
        await self.is_available_async()
        # 验证返回格式：非空列表且包含浮点数
        return self.dim

    async def is_available_async(self) -> bool:
        """通过实际嵌入请求验证服务可用性"""

        emb = await self.get_embedding_async(TEXT)
        # 验证返回格式：非空列表且包含浮点数
        if bool(emb) and isinstance(emb, list):
            self.dim = len(emb)
            return True
        else:
            return False





class BaiduProvider(Provider):
    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.url = config['api_url']
        self.api_key = self.config["api_key"]
        self.secret_key = self.config["secret_key"]
        self.token_timestamp = None
        self.access_token = ""


    def _get_embeddings(self, texts: List[str]) -> Optional[List[list]]:
        """获取embedding(同步版本)"""
        if not self.access_token or not self.token_timestamp or abs((dt.now() - self.token_timestamp).days) >= 30:
            self.access_token = self.get_access_token()
        params = {"access_token": self.access_token}
        payload = {"input": texts}
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            self.url + "/" + self.model,
            headers=headers, params=params, json=payload, timeout=30)
        response.raise_for_status()
        resp_json = response.json()
        if "error_code" in resp_json:
            logger.error(f"[{self.get_provider_name()}] 百度千帆接口错误: {resp_json}")
            raise RuntimeError(f"Baidu Qianfan error: {resp_json.get('error_msg', 'Unknown error')}")
        return [itm["embedding"] for itm in resp_json["data"]]

    def get_access_token(self) -> Optional[str]:
        """同步获取Access Token"""
        auth_url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key,
        }
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        try:
            response = requests.get(auth_url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            self.token_timestamp = dt.now()
            return response.json()["access_token"]
        except requests.HTTPError as e:
            logger.error(f"[{self.get_provider_name()}] 鉴权失败 HTTP错误: {e.response.status_code}")
        except requests.RequestException as e:
            logger.error(f"[{self.get_provider_name()}] 错误详情: {str(e)}")
        except KeyError:
            logger.error(f"[{self.get_provider_name()}] 响应缺少access_token字段")
        return None


    async def _get_embeddings_async(self, texts: List[str]) -> Optional[List[list]]:
        """获取embedding(异步版本)"""
        if not self.access_token or abs((dt.now() - self.token_timestamp).days) >= 30:
            self.access_token = await self.get_access_token_async()
        async with httpx.AsyncClient(timeout=30) as client:
            params = {"access_token": self.access_token}
            payload = {"input": texts}
            headers = {"Content-Type": "application/json"}
            response = await client.post(
                self.url + "/" + self.model,
                headers=headers, params=params, json=payload)
            response.raise_for_status()  # 自动处理4xx/5xx状态码
            resp_json = response.json()
            if "error_code" in resp_json:
                logger.error(f"[{self.get_provider_name()}] 接口错误: {resp_json}")
                raise RuntimeError(f"Baidu Qianfan error: {resp_json.get('error_msg', 'Unknown error')}")
        
            return [itm["embedding"] for itm in resp_json["data"]]


    async def get_access_token_async(self) -> Optional[str]:
        """异步获取Access Token(有效期30天)"""
        auth_url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key,
        }
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(auth_url, params=params, headers=headers)
                response.raise_for_status()
                self.token_timestamp = dt.now()
                return response.json()["access_token"]
        except httpx.HTTPStatusError as e:
            logger.error(f"[{self.get_provider_name()}] 鉴权失败 HTTP错误: {e.response.status_code}")
        except httpx.ConnectError as e:
            logger.error(f"[{self.get_provider_name()}] 错误详情: {e.__cause__}")
        except KeyError:
            logger.error(f"[{self.get_provider_name()}] 响应缺少access_token字段")
        return None

class OpenaiProvider(Provider):
    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.url = config['api_url']
        self.api_key = self.config["api_key"]

        self.client = openai.OpenAI(api_key=self.api_key, base_url=self.url)


    def _get_embeddings(self, texts: List[str]) -> Optional[List[list]]:
        # 使用 openai 库同步获取多个 embedding
        response = self.client.embeddings.create(input=texts, model=self.model)
        return [item["embedding"] for item in response["data"]]


class OllamaProvider(Provider):
    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.url = config['api_url']

    def _get_embedding(self, text: str) -> Optional[list]:
        response = requests.post(
            f"{self.url}/api/embeddings",
            json={
                "model": self.model,
                "prompt": text
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()["embedding"]

    def _get_embeddings(self, texts: List[str]) -> Optional[List[list]]:
        # Ollama API 不支持批量，逐条处理
        results = []
        for text in texts:
            results.append(self._get_embedding(text))
        return results

    async def _get_embedding_async(self, text: str) -> Optional[list]:
        """获取embedding(异步版本)"""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text
                }
            )
            response.raise_for_status()  # 自动处理4xx/5xx状态码
            return response.json()["embedding"]
        
    async def _get_embeddings_async(self, texts: List[str]) -> Optional[List[list]]:
        # Ollama API 不支持批量，逐条处理
        async with httpx.AsyncClient(timeout=30) as client:
            tasks = []
            for text in texts:
                tasks.append(
                    client.post(
                        f"{self.url}/api/embeddings",
                        json={
                            "model": self.model,
                            "prompt": text
                        }
                    )
                )
            responses = await asyncio.gather(*tasks)
            return [response.json()["embedding"] for response in responses if response.status_code == 200]

    async def is_available_async(self) -> bool:
        """Ollama双重验证:服务在线+模型有效"""
        try:
            # 先验证服务端点可达性
            async with httpx.AsyncClient(timeout=5) as client:
                await client.get(f"{self.url}/api/tags")
            # 再验证模型响应能力
            return await super().is_available_async()
        except httpx.RequestError:
            return False

class GeminiProvider(Provider):
    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.api_key = self.config["api_key"]
        self.model = self.config["embed_model"]
        self.client = genai.Client(api_key=self.api_key)

    def _get_embeddings(self, texts: List[str]) -> Optional[List[list]]:
        response = self.client.models.embed_content(model=self.model, contents=texts)
        return [embedding.values for embedding in response.embeddings]
