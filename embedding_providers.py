"""
embedding_providers.py
实现对各个embedding服务商的支持
"""
import httpx
import json
from datetime import datetime as dt
from typing import Optional
from astrbot.api import logger

TEXT="test"

class Provider:
    def __init__(self,config:dict) -> None:
        self.config = config
        self.url = config['api_url']
        self.model = config['embed_model']



    async def _get_embedding(self, text: str) -> Optional[list]:
        return NotImplementedError()

    async def get_embedding(self, text: str) -> Optional[list]:
        """获取embedding（异步版本）"""
        try:
            response = await self._get_embedding(text)
        except httpx.HTTPStatusError as e:
            logger.error(f"API错误: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"网络请求失败: {str(e)}")
        except json.JSONDecodeError:
            logger.error("响应数据解析失败")
        except Exception as e:
            logger.error(f"未知错误: {str(e)}")

    async def is_available(self) -> bool:
        """通过实际嵌入请求验证服务可用性"""
        try:
            # 直接调用内部方法，绕过公开方法的异常处理
            emb = await self._get_embedding(TEXT)
            # 验证返回格式：非空列表且包含浮点数
            return bool(emb) and isinstance(emb, list) and all(isinstance(x, float) for x in emb)
        except httpx.HTTPStatusError as e:
            logger.debug(f"服务不可用 HTTP {e.response.status_code}")
            return False
        except (httpx.RequestError, KeyError, ValueError, TypeError) as e:
            logger.debug(f"服务检查失败: {type(e).__name__}")
            return False
        except Exception as e:
            logger.error(f"未知错误: {str(e)}")
            return False



class BaiduProvider(Provider):
    # 百度
    token_timestamp: dt
    access_token: str

    def __init__(self,config:dict) -> None:
        super().__init__(config)
        self.api_key = self.config["api_key"]
        self.secret_key = self.config["secret_key"]

    async def _get_embedding(self,text:str) -> Optional[list]:
        """获取embedding（异步版本）"""
        async with httpx.AsyncClient(timeout=30) as client:
            if abs((dt.now() - self.token_timestamp).days) < 30 or not self.access_token:
                self.access_token = await self.get_access_token()
            params = {"access_token": self.access_token}
            payload = {"input": [text]}
            headers = {"Content-Type": "application/json"}
            response = await client.post(
                self.url + "/" + self.model,
                headers=headers, params=params, json=payload)
            response.raise_for_status()  # 自动处理4xx/5xx状态码
            return response.json()["data"][0]["embedding"]


    async def get_access_token(self) -> Optional[str]:
        """异步获取Access Token（有效期30天）"""
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
                return response.json()["access_token"]
        except httpx.HTTPStatusError as e:
            logger.error(f"百度千帆鉴权失败 HTTP错误: {e.response.status_code}")
        except httpx.ConnectError as e:
            logger.error(f"错误详情: {e.__cause__}")
        except KeyError:
            logger.error("响应缺少access_token字段")
        return None

    async def is_available(self) -> bool:
        """百度定制检查：强制刷新token"""
        try:
            # 主动刷新token保证有效性检查
            if not hasattr(self, "access_token") or (dt.now() - self.token_timestamp).days >= 30:
                await self.get_access_token()
            return await super().is_available()
        except Exception as e:
            logger.debug(f"百度服务检查异常: {str(e)}")
            return False


class OpenaiProvider(Provider):
    def __init__(self,config:dict) -> None:
        super().__init__(config)
        self.api_key = self.config["api_key"]


    async def _get_embedding(self,text:str) -> Optional[list]:
        async with httpx.AsyncClient(timeout=30) as client:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            payload = {
                "model": self.model,
                "input": text.replace("\n", " ")
            }
            response = await client.post(self.url, headers=headers,
                                         json=payload)
            response.raise_for_status()  # 自动处理4xx/5xx状态码
            return response.json()["data"][0]["embedding"]




class OllamaProvider(Provider):
    def __init__(self,config:dict) -> None:
        super().__init__(config)


    async def _get_embedding(self, text: str) -> Optional[list]:
        """获取embedding（异步版本）"""
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

    async def is_available(self) -> bool:
        """Ollama双重验证：服务在线+模型有效"""
        try:
            # 先验证服务端点可达性
            async with httpx.AsyncClient(timeout=5) as client:
                await client.get(f"{self.url}/api/tags")
            # 再验证模型响应能力
            return await super().is_available()
        except httpx.RequestError:
            return False

