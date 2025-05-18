"""
main.py
插件主程序
"""
import asyncio
from typing import Optional, List

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

from .provider_mapping import get_provider,PROVIDER_CLASS_MAP


@register("astrbot_plugin_embedding_adapter", "AnYan", "提供对各种服务商的embedding模型支持", "1.0.0")
class EmbeddingAdapter(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.providers = {}
        self.current_provider = None

        # 严格匹配服务商名称
        for provider_name in PROVIDER_CLASS_MAP:  # 预定义允许的服务商
            if provider_name in config:
                provider_config = config[provider_name]
                # 针对openai支持多组参数
                if provider_name == "openai":
                    # 检查是否有多个api_url/api_key/embed_model
                    api_urls = provider_config.get("api_url", "").split(",")
                    api_keys = provider_config.get("api_key", "").split(",")
                    embed_models = provider_config.get("embed_model", "").split(",")
                    # 去除空格
                    api_urls = [u.strip() for u in api_urls if u.strip()]
                    api_keys = [k.strip() for k in api_keys if k.strip()]
                    embed_models = [m.strip() for m in embed_models if m.strip()]
                    # 以最短长度为准，初始化多个openai provider
                    for idx in range(min(len(api_urls), len(api_keys), len(embed_models))):
                        multi_provider_config = {
                            "api_url": api_urls[idx],
                            "api_key": api_keys[idx],
                            "embed_model": embed_models[idx]
                        }
                        multi_provider_name = f"openai_{idx+1}" if len(api_urls) > 1 else "openai"
                        self._provider_init(provider_name,multi_provider_name, multi_provider_config)
                else:
                    self._provider_init(provider_name,provider_name, provider_config)

        # 设置目前服务商
        if config.get("whichprovider"):
            if config["whichprovider"] in self.providers:
                self.current_provider = self.providers[config["whichprovider"]]
            else:
                logger.warning(f"配置的whichprovider {config['whichprovider']} 未在已初始化的providers中")


    def _provider_init(self, provider_name: str, name:str, provider_config: dict):
        try:
            provider = get_provider(provider_name, provider_config)
            self.providers[name] = provider
            logger.info(f"成功初始化服务商: {name}")
        except ValueError as e:
            logger.error(f"服务商 {name} 初始化失败: {str(e)}，参数为{provider_config}")


    

    def get_embedding(self, text: str):
        """获取embedding向量"""
        if self.current_provider is None:
            raise ValueError("当前没有可用的embedding服务商，请使用 /em select 命令选择一个服务商")
        return self.current_provider.get_embedding(text)
    
    def get_embeddings(self, texts: List[str]):
        """获取embedding向量"""
        if self.current_provider is None:
            raise ValueError("当前没有可用的embedding服务商，请使用 /em select 命令选择一个服务商")
        return self.current_provider.get_embeddings(texts)

    def get_dim(self):
        """获取embedding维数"""
        if self.current_provider is None:
            raise ValueError("当前没有可用的embedding服务商，请使用 /em select 命令选择一个服务商")
        return self.current_provider.get_dim()

    def get_model_name(self):
        """获取模型名字"""
        if self.current_provider is None:
            raise ValueError("当前没有可用的embedding服务商，请使用 /em select 命令选择一个服务商")
        return self.current_provider.get_model_name()

    def get_provider_name(self):
        """获取provider名"""
        if self.current_provider is None:
            raise ValueError("当前没有可用的embedding服务商，请使用 /em select 命令选择一个服务商")
        return self.current_provider.get_provider_name()
    
    def is_available(self):
        """检查服务商是否可用"""
        if self.current_provider is None:
            raise ValueError("当前没有可用的embedding服务商，请使用 /em select 命令选择一个服务商")
        return self.current_provider.is_available()
    


    async def get_embedding_async(self, text:str):
        """获取embedding向量"""
        if self.current_provider is None:
            raise ValueError("当前没有可用的embedding服务商，请使用 /em select 命令选择一个服务商")
        return await self.current_provider.get_embedding_async(text)
    
    async def get_embeddings_async(self, texts: List[str]):
        """获取embedding向量"""
        if self.current_provider is None:
            raise ValueError("当前没有可用的embedding服务商，请使用 /em select 命令选择一个服务商")
        return await self.current_provider.get_embeddings_async(texts)

    async def get_dim_async(self):
        """获取embedding维数"""
        if self.current_provider is None:
            raise ValueError("当前没有可用的embedding服务商，请使用 /em select 命令选择一个服务商")
        return await self.current_provider.get_dim_async()
    
    async def is_available_async(self):
        """检查服务商是否可用"""
        if self.current_provider is None:
            raise ValueError("当前没有可用的embedding服务商，请使用 /em select 命令选择一个服务商")
        return await self.current_provider.is_available_async()
    



    @filter.command_group("Embedding_Manager", alias={'em'})
    def embedding_manager(self):
        pass

    @filter.permission_type(filter.PermissionType.ADMIN)
    @embedding_manager.command("list", alias={'ls'})
    async def list_providers(self, event: AstrMessageEvent):
        """列出所有可用服务商 /em ls"""
        if not self.providers:
            yield event.plain_result("未配置任何有效的embedding服务商")

        availability_tasks = {
            name: provider.is_available_async()
            for name, provider in self.providers.items()
        }
        results = await asyncio.gather(*availability_tasks.values(), return_exceptions=True)
        # 构建状态信息
        reply_list=[]
        for (name, provider), available in zip(self.providers.items(), results):
            try:
                is_available = "(可用)" if available else "(不可用)"
            except Exception as e:
                logger.error(f"检查服务商 {name} 状态失败: {str(e)}")
                is_available = "(状态未知)"
            model=provider.get_model_name()
            current_flag = "[√]" if provider == self.current_provider else "[  ]"
            reply_list.append(f"{current_flag} {name} {model} {is_available}")

        # 格式化输出
        yield event.plain_result("\n".join(reply_list))


    @filter.permission_type(filter.PermissionType.ADMIN)
    @embedding_manager.command("select")
    async def select_provider(self, event: AstrMessageEvent, name: str ):
        """切换当前服务商 /em select ollama"""
        if name in self.providers:
            self.current_provider = self.providers[name]
            self.config["whichprovider"]=name
            # self.config.save_config()
            yield event.plain_result(f"已切换到服务商：{name}")
        else:
            yield event.plain_result(f"切换失败，不存在服务商：{name}")

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        pass