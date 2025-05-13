from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger


from datetime import datetime as dt


@register("EmbeddingAdapter", "AnYan", "提供对各种服务商的embedding模型支持", "1.0.0")
class EmbeddingAdapter(Star):
    def __init__(self, context: Context, config:  dict):
        super().__init__(context)
        self.config = config



    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        pass

    @filter.command_group("Embedding_Manager", alias={'em'})
    def embedding_manager(self):
        pass

    @filter.permission_type(filter.PermissionType.ADMIN)
    @embedding_manager.command("list", alias={'ls'})
    async def list(self, event: AstrMessageEvent):



    @filter.permission_type(filter.PermissionType.ADMIN)
    @embedding_manager.command("list", alias={'ls'})
        async def list(self, event: AstrMessageEvent):

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
