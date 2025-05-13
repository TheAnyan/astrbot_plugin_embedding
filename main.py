from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import LogManager
from .provider_mapping import get_provider,PROVIDER_CLASS_MAP # 假设provider_mapping在同一目录

EMlogger= LogManager.GetLogger(log_name="EmbeddingAdapter")

@register("EmbeddingAdapter", "AnYan", "提供对各种服务商的embedding模型支持", "1.0.0")
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
                    EMlogger.info(f"成功初始化服务商: {provider_name}")
                except ValueError as e:
                    EMlogger.error(f"服务商 {provider_name} 初始化失败: {str(e)}")

        # 设置目前服务商
        self.current_provider = self.providers[config["whichprovider"]]


    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        pass

    @filter.command_group("Embedding_Manager", alias={'em'})
    def embedding_manager(self):
        pass

    @filter.permission_type(filter.PermissionType.ADMIN)
    @embedding_manager.command("list", alias={'ls'})
    async def list_providers(self, event: AstrMessageEvent):
        """列出所有可用服务商 /em ls"""
        if not self.providers:
            yield event.plain_result("未配置任何有效的embedding服务商")

        for name, provider in self.providers.items():
            status = "✅" if provider == self.current_provider else "  "
            available= "(available)" if provider.is_available() else ""
            yield event.plain_result(f"{status} {name} {available}")


    @filter.permission_type(filter.PermissionType.ADMIN)
    @embedding_manager.command("select")
    async def select_provider(self, event: AstrMessageEvent, name: str ):
        """切换当前服务商 /em select ollama"""


        self.current_provider = self.providers[name]
        return MessageEventResult(f"已切换到服务商：{name}")

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        pass