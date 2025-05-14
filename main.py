"""
main.py
插件主程序
"""
import asyncio

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

from .provider_mapping import get_provider,PROVIDER_CLASS_MAP # 假设provider_mapping在同一目录


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
                try:
                    provider = get_provider(provider_name, provider_config)
                    self.providers[provider_name] = provider
                    logger.info(f"成功初始化服务商: {provider_name}")
                except ValueError as e:
                    logger.error(f"服务商 {provider_name} 初始化失败: {str(e)}")

        # 设置目前服务商
        if config["whichprovider"]:
            self.current_provider = self.providers[config["whichprovider"]]


    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        pass

    def get_embedding(self):
        """获取embedding向量"""
        return self.current_provider.get_embedding()

    def get_model_name(self):
        """获取模型名字"""
        return self.current_provider.get_model_name()

    def get_provider_name(self):
        """获取provider名"""
        return self.current_provider.get_provider_name()

    def get_dim(self):
        """获取embedding维数"""
        return self.current_provider.get_dim()

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
            name: provider.is_available()
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

            current_flag = "[√]" if provider == self.current_provider else "[  ]"
            reply_list.append(f"{current_flag} {name} {is_available}")

        # 格式化输出
        yield event.plain_result("\n".join(reply_list))


    @filter.permission_type(filter.PermissionType.ADMIN)
    @embedding_manager.command("select")
    async def select_provider(self, event: AstrMessageEvent, name: str ):
        """切换当前服务商 /em select ollama"""
        if name in self.providers:
            self.current_provider = self.providers[name]
            self.config["whichprovider"]=name
            self.config.save_config()
            yield event.plain_result(f"已切换到服务商：{name}")
        else:
            yield event.plain_result(f"切换失败，不存在服务商：{name}")

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        pass