# from astrbot.api.event import filter, AstrMessageEvent
# from astrbot.api import AstrBotConfig
# from astrbot.core.star import Star, register, Context
#
#
# @register("config", "Soulter", "一个配置示例", "1.0.0")
# class ConfigManager(Star):
#     def __init__(self, context: Context, config: AstrBotConfig): # AstrBotConfig 继承自 Dict，拥有字典的所有方法
#         super().__init__(context)
#         self.config = config
#         print(self.config)