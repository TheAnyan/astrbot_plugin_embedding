"""
embedding_providers.py
实现对各个embedding服务商的支持
"""
import httpx
import json
from datetime import datetime as dt
from typing import Optional
from astrbot.api import logger



class Provider:
    def __init__(self,config:dict) -> None:
        self.config = config
        self.url = config['api_url']
        self.model = config['embed_model']

    async def get_embedding(self,text:str) -> Optional[list]:
        raise NotImplementedError()

class BaiduProvider(Provider):
    # 百度
    token_timestamp: dt
    access_token: str

    def __init__(self,config:dict) -> None:
        super().__init__(config)
        self.api_key = self.config["api_key"]
        self.secret_key = self.config["secret_key"]

    async def get_embedding(self,text:str) -> Optional[list]:
        """获取embedding（异步版本）"""
        try:
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

        except httpx.HTTPStatusError as e:
            logger.error(f"API错误: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"网络请求失败: {str(e)}")
        except json.JSONDecodeError:
            logger.error("响应数据解析失败")
        except Exception as e:
            logger.error(f"未知错误: {str(e)}")

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


class OpenaiProvider(Provider):
    def __init__(self,config:dict) -> None:
        super().__init__(config)
        self.api_key = self.config["api_key"]



    async def get_embedding(self, text: str) -> Optional[list]:
        """获取embedding（异步版本）"""
        try:
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


        except httpx.HTTPStatusError as e:
            logger.error(f"API错误: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"网络请求失败: {str(e)}")
        except json.JSONDecodeError:
            logger.error("响应数据解析失败")
        except Exception as e:
            logger.error(f"未知错误: {str(e)}")






class OllamaProvider(Provider):
    def __init__(self,config:dict) -> None:
        super().__init__(config)
        self.url=self.config['ollama_api_url']


    async def get_embedding(self, text: str) -> Optional[list]:
        """获取embedding（异步版本）"""
        try:
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

        except httpx.HTTPStatusError as e:
            logger.error(f"错误状态码: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"网络请求失败: {str(e)}")
        except json.JSONDecodeError:
            logger.error("响应数据解析失败")
        except Exception as e:
            logger.error(f"未知错误: {str(e)}")
