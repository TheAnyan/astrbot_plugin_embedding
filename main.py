"""
main.py
插件主程序
"""
import asyncio
from typing import Optional, List,Union

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

from .provider_mapping import get_provider,PROVIDER_CLASS_MAP
from .model_group import ModelGroupProvider

@register("astrbot_plugin_embedding_adapter", "AnYan", "提供对各种服务商的embedding模型支持", "1.0.0")
class EmbeddingAdapter(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.providers = {}
        self.groups = {}
        self.unable_groups = []
        self.current_provider_group = None

        # 严格匹配服务商名称
        for api_name in PROVIDER_CLASS_MAP:  # 预定义允许的服务商
            if api_name in config:
                provider_name=None
                provider_config = config[api_name]
                # 针对openai支持多组参数
                if api_name == "openai":
                    # 检查是否有多个api_url/api_key/embed_model
                    api_urls = provider_config.get("api_url", "").split(",")
                    api_keys = provider_config.get("api_key", "").split(",")
                    embed_models = provider_config.get("embed_model", "").split(",")
                    batch_size = provider_config.get("batch_size", "1").split(",")

                    api_urls = [u.strip() for u in api_urls if u.strip()]
                    api_keys = [k.strip() for k in api_keys if k.strip()]
                    embed_models = [m.strip() for m in embed_models if m.strip()]
                    batch_sizes = [b.strip() for b in batch_size if b.strip()]

                    # 以最短长度为准，初始化多个openai provider
                    for idx in range(min(len(api_urls), len(api_keys), len(embed_models))):
                        multi_provider_config = {
                            "api_url": api_urls[idx],
                            "api_key": api_keys[idx],
                            "embed_model": embed_models[idx],
                            "batch_size": batch_sizes[idx] if idx < len(batch_sizes) else "1",
                        }
                        provider_name = f"openai_{idx+1}" if len(api_urls) > 1 else "openai"
                        self._provider_init(api_name,provider_name, multi_provider_config)
                else:
                    provider_name=api_name
                    self._provider_init(api_name,provider_name, provider_config)
                    
        for provider_name in self.providers:
            # 如果可用则添加到groups中
            if self.providers[provider_name].is_available():
                has_group = False
                for goup_name, group in self.groups.items():
                    if group.add_provider(self.providers[provider_name]):
                        has_group = True
                        break

                if not has_group:
                    # 如果没有找到对应的group，则创建一个新的group
                    group_name = self.providers[provider_name].get_model_name()
                    self.groups[group_name] = ModelGroupProvider(group_name,[self.providers[provider_name]])
                    logger.info(f"成功创建新的模型组: {group_name}")
            else:
                self.unable_groups.append(provider_name)
                            

        # 设置目前服务商
        if config.get("whichgroup"):
            if config["whichgroup"] in self.groups:
                self.current_provider_group = self.groups[config["whichgroup"]]
            else:
                logger.warning(f"配置的whichgroup {config['whichgroup']} 未在已初始化的groups中")


    def _provider_init(self, api_name: str, group_name:str, provider_config: dict):
        try:
            provider = get_provider(api_name, group_name, provider_config)
            self.providers[group_name] = provider
            logger.info(f"成功初始化服务商: {group_name}")
            return provider
        except ValueError as e:
            logger.error(f"服务商 {group_name} 初始化失败: {str(e)}，参数为{provider_config}")
            return None
        
    
    def _in_which_groups(self, api_name: str):
        for name,group in self.groups.items():
            if group.is_in_group(api_name):
                return name
        return None

    

    def get_embedding(self, text: str):
        """获取embedding向量"""
        if self.current_provider_group is None:
            raise ValueError("当前没有可用的embedding服务商，请使用 /em select 命令选择一个服务商")
        return self.current_provider_group.get_embedding(text)
    
    def get_embeddings(self, texts: List[str]):
        """获取embedding向量"""
        if self.current_provider_group is None:
            raise ValueError("当前没有可用的embedding服务商，请使用 /em select 命令选择一个服务商")
        return self.current_provider_group.get_embeddings(texts)

    def get_dim(self):
        """获取embedding维数"""
        if self.current_provider_group is None:
            raise ValueError("当前没有可用的embedding服务商，请使用 /em select 命令选择一个服务商")
        return self.current_provider_group.get_dim()

    def get_model_name(self):
        """获取模型名字"""
        if self.current_provider_group is None:
            raise ValueError("当前没有可用的embedding服务商，请使用 /em select 命令选择一个服务商")
        return self.current_provider_group.get_model_name()

    def get_provider_name(self):
        """获取provider名"""
        if self.current_provider_group is None:
            raise ValueError("当前没有可用的embedding服务商，请使用 /em select 命令选择一个服务商")
        return self.current_provider_group.get_provider_name()
    
    def is_available(self):
        """检查服务商是否可用"""
        if self.current_provider_group is None:
            raise ValueError("当前没有可用的embedding服务商，请使用 /em select 命令选择一个服务商")
        return self.current_provider_group.is_available()
    


    async def get_embedding_async(self, text:str):
        """获取embedding向量"""
        if self.current_provider_group is None:
            raise ValueError("当前没有可用的embedding服务商，请使用 /em select 命令选择一个服务商")
        return await self.current_provider_group.get_embedding_async(text)
    
    async def get_embeddings_async(self, texts: List[str]):
        """获取embedding向量"""
        if self.current_provider_group is None:
            raise ValueError("当前没有可用的embedding服务商，请使用 /em select 命令选择一个服务商")
        return await self.current_provider_group.get_embeddings_async(texts)

    async def get_dim_async(self):
        """获取embedding维数"""
        if self.current_provider_group is None:
            raise ValueError("当前没有可用的embedding服务商，请使用 /em select 命令选择一个服务商")
        return await self.current_provider_group.get_dim_async()
    
    async def is_available_async(self):
        """检查服务商是否可用"""
        if self.current_provider_group is None:
            raise ValueError("当前没有可用的embedding服务商，请使用 /em select 命令选择一个服务商")
        return await self.current_provider_group.is_available_async()
    



    @filter.command_group("Embedding_Manager", alias={'em'})
    def embedding_manager(self):
        pass

    @filter.permission_type(filter.PermissionType.ADMIN)
    @embedding_manager.command("list", alias={'ls'})
    async def list_groupgroups(self, event: AstrMessageEvent):
        """列出所有可用服务商 /em ls"""
        if not self.groups:
            yield event.plain_result("未配置任何有效的embedding服务商")
        reply_list=[]
        for group_name, group in self.groups.items():
            current_flag = "[√]" if group == self.current_provider_group else "[  ]"
            reply_list.append(f"{current_flag} {group_name}:")
            availability_tasks = {
                provider.get_provider_name: provider.is_available_async()
                for provider in group.providers
            }
            results = await asyncio.gather(*availability_tasks.values(), return_exceptions=True)
            # 构建状态信息
            i=0
            for provider, available in zip(group.providers, results):
                is_available = "(可用)" if available else "(不可用)"
                current_flag2 = "[√]" if i == group.default_provider_index else "[  ]"
                reply_list.append(f"\t({i}) {current_flag2} {provider.get_provider_name()} {is_available}")
                i+=1
        reply_list.append("不可用的服务商:")
        for provider_name in self.unable_groups:
            reply_list.append(f"\t{provider_name}")
        # 格式化输出
        yield event.plain_result("\n".join(reply_list))


    @filter.permission_type(filter.PermissionType.ADMIN)
    @embedding_manager.command("select")
    async def select_group(self, event: AstrMessageEvent, name: str ,default_index:int = 0):
        """切换当前模型 /em select <模型> [提供商的序号]"""
        if name in self.groups:
            self.current_provider_group = self.groups[name]
            self.config["whichgroup"]=name
            # self.config.save_config()
            try:
                self.current_provider_group.set_default_provider(default_index)
                yield event.plain_result(f"已切换到模型为{name}的服务商：{self.current_provider_group.providers[default_index].get_provider_name()}")
            except ValueError as e:
                yield event.plain_result(f"切换失败，提供商索引越界: {str(e)}")
                return
        else:
            yield event.plain_result(f"切换失败，不存在服务商：{name}")

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        pass