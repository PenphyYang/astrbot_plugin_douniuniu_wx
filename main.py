import asyncio
import time

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import AstrBotConfig
from astrbot.core.message.components import At
import astrbot.api.message_components as Comp
from astrbot.core.message.message_event_result import MessageChain
from astrbot.core.star.filter.event_message_type import EventMessageType
from astrbot.core.star.filter.permission import PermissionType
from data.plugins.astrbot_plugin_douniuniu_wx.core.data_manager import DataManager
from .core.battle import Battle
from .core.do_other import DoOther
from .core.do_self import DoSelf
from .core.shop import Shop
from .core.utils import format_length, is_timestamp_today, random_normal_distribution_int, check_cooldown


@register("douniuniu_wx", "pf", "培养你的牛牛，然后塔塔开！", "1.0.2")
class DouNiuniuPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.data_manager = DataManager()
        self.battle = Battle()
        self.shop = Shop()
        self.do_self = DoSelf()
        self.do_other = DoOther()
        self.task = {}

    def check_group_enable(self, group_id):
        return self.data_manager.get_group_data(group_id)['plugin_enabled']

    @filter.command("创建牛牛", alias={'创建'})
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def register_bull(self, event: AstrMessageEvent):
        """用于创建并初始化一个属于你的牛牛"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return

        user_id = event.get_sender_id()
        user_name = event.get_sender_name()

        user_data = self.data_manager.get_user_data(user_id)
        if user_data != {}:
            text = f"⚠️ 你已经创建过牛牛啦！"
            yield event.plain_result(text)
            return

        message, init_length, init_hardness = self.data_manager.create_user(group_id, user_id, user_name)
        text = f"✌️ 你的牛牛长出来啦！\n📏 初始长度：{init_length}cm\n💪 硬度等级：{init_hardness}\n{message}"
        yield event.plain_result(text)

    @filter.permission_type(PermissionType.ADMIN)
    @filter.command("强制创建牛牛", alias={'强制创建', '强制注册'})
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def force_register_bull(self, event: AstrMessageEvent):
        """强制为对方创建牛牛，仅管理员，需要@"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        for comp in event.message_obj.message:
            if isinstance(comp, At):
                user_id = str(comp.qq)
                # 获取对方用户名
                user_name = comp.name
                print(user_name)
                # 没找到用户数据，直接新建
                if not self.data_manager.get_user_data(user_id):
                    message, init_length, init_hardness = self.data_manager.create_user(group_id, user_id, user_name)
                    text = f"✌️ {user_name}的牛牛长出来啦！\n📏 初始长度：{init_length}cm\n💪 硬度等级：{init_hardness}\n{message}"
                    yield event.plain_result(text)
                    return
                else:
                    if user_id not in self.data_manager.get_group_rank_all(group_id):
                        yield event.plain_result(f'❌ 他的牛牛未加入本群，执行强制入群')
                        user_data = self.data_manager.get_user_data(user_id)
                        user_trans = user_data['items']['transfer']
                        name = '猫猫' if user_trans else '牛牛'
                        icon = '🐈️' if user_trans else '🐂'
                        self.data_manager.update_rank(user_id)
                        if not user_trans:
                            yield event.plain_result(
                                f"{icon} 你拉着长度为{user_data['length']}cm，硬度为{user_data['hardness']}的{name}强制加入了本群")
                        else:
                            yield event.plain_result(
                                f"{icon} 你拉着深度为{user_data['hole']}cm，敏感度为{user_data['sensitivity']}的{name}强制加入了本群")
                        return
                    else:
                        yield event.plain_result(f"❌ 对方的牛牛已在本群")
                        return
        yield event.plain_result(f'❌ 需要@强制创建对象')

    @filter.command("牛牛进群", alias={'进群', '加入牛牛', '牛牛加入', '猫猫进群'})
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def enter_group(self, event: AstrMessageEvent):
        """将牛牛数据加入本群"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return

        user_id = event.get_sender_id()
        user_name = event.get_sender_name()

        user_data = self.data_manager.get_user_data(user_id)
        if user_data == {}:
            text = f"❌ 你的牛牛还没出生，输入“/创建牛牛”生成你的牛牛吧！"
            yield event.plain_result(text)
            return
        else:
            local_rank = self.data_manager.get_group_rank_all(group_id)
            if user_id in local_rank:
                yield event.plain_result('👀 你的牛牛已在本群')
            else:
                user_trans = user_data['items']['transfer']
                name = '猫猫' if user_trans else '牛牛'
                icon = '🐈️' if user_trans else '🐂'
                self.data_manager.add_in_group(user_id, group_id)
                self.data_manager.update_rank(user_id)
                if not user_trans:
                    yield event.plain_result(
                        f"{icon} 你带着长度为{user_data['length']}cm，硬度为{user_data['hardness']}的{name}加入了本群")
                else:
                    yield event.plain_result(
                        f"{icon} 你带着深度为{user_data['hole']}cm，敏感度为{user_data['sensitivity']}的{name}加入了本群")

    @filter.command("牛牛排行", alias={'排行榜', '排行'})
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def show_rank(self, event: AstrMessageEvent, n: int = 10):
        """展示本群前n名的牛牛"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return

        rank = self.data_manager.get_group_rank_n(group_id, n)
        if rank == {}:
            yield event.plain_result('🤔 本群还没有人有牛牛')
        else:
            text = f"🏆 牛牛排行榜 TOP{n}：\n\n"
            for index, (key, value) in enumerate(rank.items()):
                user_data = self.data_manager.get_user_data(key)
                length_text = format_length(user_data['length'])
                if index == 0:
                    text += f"🥇 {value[0]}➜{length_text} 硬度{user_data['hardness']}级\n"
                elif index == 1:
                    text += f"🥈 {value[0]}➜{length_text} 硬度{user_data['hardness']}级\n"
                elif index == 2:
                    text += f"🥉 {value[0]}➜{length_text} 硬度{user_data['hardness']}级\n"
                else:
                    text += f"🏅 {value[0]}➜{length_text} 硬度{user_data['hardness']}级\n"
            yield event.plain_result(text)

#    @filter.permission_type(PermissionType.ADMIN)
    @filter.command("添加牛牛管理员", alias={'添加'})
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def add_manager(self, event: AstrMessageEvent, user_id: str, group_id: str):
        """向指定群里添加指定管理员"""
        self.data_manager.add_group_manager(group_id, user_id)
#        group_data = self.data_manager.get_group_data(group_id)

#        if user_id in group_data['manager']:
#            yield event.plain_result(f"❌ {user_id}已是目标群的牛牛管理员")
#        else:
#            self.data_manager.add_group_manager(group_id, user_id)
#            yield event.plain_result(f"✅ {user_id}已被设为{group_id}的牛牛管理员")

#    @filter.permission_type(PermissionType.ADMIN)
    @filter.command("删除牛牛管理员", alias={'删除'})
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def del_manager(self, event: AstrMessageEvent, user_id: str, group_id: str):
        """向指定群里删除指定管理员"""
        self.data_manager.del_group_manager(group_id, user_id)
 #       group_data = self.data_manager.get_group_data(group_id)

 #       if user_id not in group_data['manager']:
 #           yield event.plain_result(f"❌ {user_id}并不是目标群的牛牛管理员")
 #       else:
 #           self.data_manager.del_group_manager(group_id, user_id)
 #           yield event.plain_result(f"✅ 已清除{user_id}在{group_id}的牛牛管理员权限")

    @filter.command("牛牛帮助", alias={'帮助', '文档', '牛牛文档', '菜单', '牛牛菜单'})
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def show_help(self, event: AstrMessageEvent):
        """显示帮助文档"""
        yield event.image_result('data/plugins/astrbot_plugin_douniuniu_wx/help.jpg')

    @filter.command("开启牛牛", alias={'开启', '启用', '牛牛开启', '启用牛牛', '牛牛启用', '启动'})
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def enable_niuniu(self, event: AstrMessageEvent):
        """开启本群牛牛功能"""
        user_id = event.get_sender_id()
        # 判断是否为管理员
        group_id = event.get_group_id()
        manager_list = self.data_manager.get_group_data(group_id)['manager']
        if user_id not in manager_list:
            yield event.plain_result(f"❌ 你不是本群的牛牛管理员，无法开启牛牛插件")
        else:
            self.data_manager.set_group_enabled(group_id, True)
            yield event.plain_result(
                f"🔓️ 牛牛插件已开启\n\n🔗 本插件github链接：https://github.com/LaoZhuJackson/astrbot_plugin_douniuniu_wx#\n🌟 欢迎来点星星，提需求和提交bug━(*｀∀´*)ノ亻!")

    @filter.command("关闭牛牛", alias={'关闭', '牛牛关闭'})
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def disable_niuniu(self, event: AstrMessageEvent):
        """关闭本群牛牛功能"""
        user_id = event.get_sender_id()
        # 判断是否为管理员
        group_id = event.get_group_id()
        manager_list = self.data_manager.get_group_data(group_id)['manager']
        if user_id not in manager_list:
            yield event.plain_result(f"❌ 你不是本群的牛牛管理员，无法关闭牛牛插件")
        else:
            self.data_manager.set_group_enabled(group_id, False)
            yield event.plain_result(f"🔒 牛牛插件已关闭")

    @filter.command("注销牛牛", alias={'注销'})
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def delete_niuniu(self, event: AstrMessageEvent, who: str = None):
        """注销自己或其他用户的牛牛并清空对应排行榜"""
        user_id = event.get_sender_id()
        # 判断是否为管理员
        group_id = event.get_group_id()
        manager_list = self.data_manager.get_group_data(group_id)['manager']
        if not who:
            for comp in event.message_obj.message:
                if isinstance(comp, At):
                    user2_id = str(comp.qq)
                    if user2_id not in manager_list:
                        yield event.plain_result(f"❌ 你不是本群的牛牛管理员，无法注销其他用户")
                        return
                    other_data = self.data_manager.get_user_data(user2_id)
                    if not other_data:
                        yield event.plain_result(f'❌ 他的牛牛还没出生，需要对方输入“/创建牛牛”创建牛牛')
                        return
                    # 注销别人的需要别人在他那个群，注销自己的则不需要
                    if user2_id not in self.data_manager.get_group_rank_all(group_id):
                        yield event.plain_result(f'❌ 他的牛牛还没加入本群，需要对方输入“/牛牛进群”将牛牛加入本群')
                        return
                    self.data_manager.delete_user(user2_id)
                    yield event.plain_result(f"✅ 注销用户 {other_data['user_name']} 成功\n")
                    return
            yield event.plain_result(f"❌ 注销他人牛牛需要管理员权限且@需要注销的人\n如果需要注销自己，输入“/注销 自己”")
        else:
            if who == "自己":
                sender_data = self.data_manager.get_user_data(user_id)
                if not sender_data:
                    yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
                    return
                self.data_manager.delete_user(user_id)
                yield event.plain_result(f"✅ 注销用户 {sender_data['user_name']} 成功\n")
            else:
                yield event.plain_result(
                    f"❌ 注销他人牛牛需要管理员权限且@需要注销的人\n如果需要注销自己，输入“/注销 自己”")

    @filter.command("牛牛决斗", alias={'比划比划', '🤺', '比划', '决斗', '击剑'})
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def battle(self, event: AstrMessageEvent):
        """与另外一个牛牛决斗"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return

        # 判断双方牛牛是否存在
        sender_id = event.get_sender_id()
        sender_data = self.data_manager.get_user_data(sender_id)
        if not sender_data:
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return
        if sender_id not in self.data_manager.get_group_rank_all(group_id):
            yield event.plain_result(f'❌ 你的牛牛还没加入本群，输入“/牛牛进群”将牛牛加入本群')
            return
        name = "猫猫" if self.data_manager.get_user_data(sender_id)['items']['transfer'] else "牛牛"
        if self.is_work(sender_id):
            yield event.plain_result(f'❌ 你的{name}还在卖力工作中')
            return
        if self.is_exercise(sender_id):
            yield event.plain_result(f'❌ 你的{name}还在努力锻炼中')
            return
        other_data = {}
        user_id = ''
        for comp in event.message_obj.message:
            if isinstance(comp, At):
                user_id = str(comp.qq)
                other_data = self.data_manager.get_user_data(user_id)
                if not other_data:
                    yield event.plain_result(f'❌ 他的牛牛还没出生，需要对方输入“/创建牛牛”创建牛牛')
                    return
                if user_id not in self.data_manager.get_group_rank_all(group_id):
                    yield event.plain_result(f'❌ 他的牛牛还没加入本群，需要对方输入“/牛牛进群”将牛牛加入本群')
                    return
                name = "猫猫" if self.data_manager.get_user_data(user_id)['items']['transfer'] else "牛牛"
                if self.is_work(user_id):
                    yield event.plain_result(f'❌ 他的{name}还在卖力工作中')
                    return
                if self.is_exercise(user_id):
                    yield event.plain_result(f'❌ 他的{name}还在努力锻炼中')
                    return
        if not user_id:
            yield event.plain_result(f'❌ 需要@一个与你决斗的人')
            return
        # 判断性转
        sender_trans = sender_data['items']['transfer']
        other_trans = other_data['items']['transfer']
        if sender_id not in self.data_manager.get_group_rank_all(group_id):
            name = '猫猫' if sender_trans else '牛牛'
            icon = '🐈️' if sender_trans else '🐂'
            yield event.plain_result(f'{icon} 你的{name}不在本群，输入“/{name}进群”让{name}加入本群')
            return
        if user_id not in self.data_manager.get_group_rank_all(group_id):
            name = '猫猫' if other_trans else '牛牛'
            icon = '🐈️' if other_trans else '🐂'
            yield event.plain_result(f'{icon} 他的{name}不在本群，需要对方输入“/{name}进群”让他的{name}加入本群')
            return

        # 进入不同情况下的决斗
        yield event.plain_result(self.battle.user1_vs_user2(group_id, sender_id, user_id))

    @filter.command("牛牛取名", alias={'取名', '改名', '名称', '牛牛改名'})
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def set_niuniu_name(self, event: AstrMessageEvent, name: str):
        """为牛牛取名"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user_id = event.get_sender_id()
        user_data = self.data_manager.get_user_data(user_id)
        if not user_data:
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return
        yield event.plain_result(self.shop.use_rename_card(user_id, name, self.config))

    def get_info(self, user_id, user_name):
        """获取用户信息"""
        text = f'✨✨✨{user_name}的信息✨✨✨\n'

        user_data = self.data_manager.get_user_data(user_id)
        text += f"🐮 牛牛名称：{user_data['niuniu_name']}\n"
        niuniu_length_text = format_length(user_data['length'])
        text += f"📏 牛牛长度：{niuniu_length_text}\n"
        text += f"💪 牛牛硬度：{user_data['hardness']}级\n"
        drone = user_data['items']['drone']
        drone_text = str(drone) if len(drone) > 0 else '没有寄生虫，牛牛很健康'
        text += f"🐛 寄生虫：{drone_text}\n"
        text += f"💯 牛牛评分：{round(user_data['length'] * 0.3 + user_data['hardness'] * 0.7, 2)}\n"
        maomao_length_text = format_length(user_data['hole'])
        text += f"📏 猫猫深度：{maomao_length_text}\n"
        text += f"💦 猫猫敏感度：{user_data['sensitivity']}级\n"
        text += f"💯 猫猫评分：{user_data['hole'] * 0.3 + user_data['sensitivity'] * 0.7}\n"
        text += f"👛 持有金币：{user_data['coins']}\n"
        text += f"🥊 当前连胜：{user_data['current_win_count']}次\n"
        text += f"🗡️ 最高连胜：{user_data['win_count']}次\n"
        _,remain_work = check_cooldown(user_data['time_recording']['start_work'][0], user_data['time_recording']['start_work'][1])
        _,remain_exercise = check_cooldown(user_data['time_recording']['start_exercise'][0], user_data['time_recording']['start_exercise'][1])
        remain_work = "未工作" if remain_work=='0秒' else remain_work
        remain_exercise = "未锻炼" if remain_exercise=='0秒' else remain_exercise
        text += f"🥵 打工时长剩余：{remain_work}\n"
        text += f"🦶 锻炼时长剩余：{remain_exercise}\n"

        transfer_text = '是' if user_data['items']['transfer'] else '否'
        text += f"🔄 性转：{transfer_text}\n"
        sign_text = "是" if is_timestamp_today(user_data['time_recording']['sign']) else '否'
        text += f"📅 今日签到：{sign_text}\n"

        return text

    @filter.command("我的信息", alias={'信息', '我的牛牛', '牛牛信息'})
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def show_self_info(self, event: AstrMessageEvent):
        """展示自己的个人信息"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return

        user_id = event.get_sender_id()
        user_name = event.get_sender_name()
        if not self.data_manager.get_user_data(user_id):
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return

        yield event.plain_result(self.get_info(user_id, user_name))

    @filter.command("查看信息", alias={'查看'})
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def show_other_info(self, event: AstrMessageEvent):
        """查看他人的个人信息"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        for comp in event.message_obj.message:
            if isinstance(comp, At):
                user_id = str(comp.qq)
                if not self.data_manager.get_user_data(user_id):
                    yield event.plain_result(f'❌ 他的牛牛还没出生，需要对方输入“/创建牛牛”创建牛牛')
                    return
                if user_id not in self.data_manager.get_group_rank_all(group_id):
                    yield event.plain_result(f'❌ 他的牛牛未加入本群，无法查看')
                    return
                user_name = self.data_manager.get_group_rank_all(group_id)[user_id][0]
                yield event.plain_result(self.get_info(user_id, user_name))
                return
        yield event.plain_result("❌ 查看信息需要@想要查看的人")

    @filter.command("牛牛签到", alias={'签到', '每日签到'})
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def daily_sign(self, event: AstrMessageEvent):
        """每日签到"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return

        user_id = event.get_sender_id()
        user_data = self.data_manager.get_user_data(user_id)
        if not user_data:
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return
        if is_timestamp_today(user_data['time_recording']['sign']):
            yield event.plain_result(f'🥰 你今天以及签过到啦！')
            return
        timestamp = time.time()
        user_data['time_recording']['sign'] = timestamp
        get_coins = random_normal_distribution_int(10, 20, 3)
        user_data['coins'] += get_coins
        self.data_manager.save_user_data(user_id, user_data)
        text = '✨ 签到成功 ✨\n'
        text += f'💰️ 获得金币：{get_coins}\n'
        coins = user_data['coins']
        text += f'👛 当前金币：{coins}'
        yield event.plain_result(text)

    @filter.command("牛牛商城", alias={'商城', '商店', '牛牛商店'})
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def show_store(self, event: AstrMessageEvent, output_type: str = 'image'):
        """展示商城的所有商品"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user_id = event.get_sender_id()
        if not self.data_manager.get_user_data(user_id):
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return

        if output_type == 'image':
            money = self.data_manager.get_user_data(user_id)['coins']
            text = f'👛 当前持有金币：{money}'

            chain = [
                Comp.Reply(id=user_id),  # 回复 消息发送者
                Comp.Image.fromFileSystem("data/plugins/astrbot_plugin_douniuniu_wx/store_items.jpg"),  # 从本地文件目录发送图片
                Comp.Plain(text)
            ]
            yield event.chain_result(chain)
        else:
            yield event.plain_result(self.shop.get_items(user_id))

    @filter.command("购买")
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def buy_item(self, event: AstrMessageEvent, items_id: int, num: int = 1):
        """购买商品，必须指定商品编号，可选购买数量，默认买1个"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user_id = event.get_sender_id()
        if not self.data_manager.get_user_data(user_id):
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return

        user_id = event.get_sender_id()
        yield event.plain_result(self.shop.purchase(user_id, items_id, num))

    @filter.command("牛牛背包", alias={'背包', '我的背包'})
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def show_bag(self, event: AstrMessageEvent):
        """展示用户背包物品"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user_id = event.get_sender_id()
        if not self.data_manager.get_user_data(user_id):
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return

        user_id = event.get_sender_id()
        user_data = self.data_manager.get_user_data(user_id)
        text = '🎒 你的背包 🎒\n'
        for key, value in user_data['items_num'].items():
            if value < 1:
                continue
            text += f'{key}: {value}\n'
        if text == '🎒 你的背包 🎒\n':
            text += '\n空空如也'
        yield event.plain_result(text)

    @filter.command("钞能力", alias={'超能力'})
    @filter.permission_type(PermissionType.ADMIN)
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def admin_get_money(self, event: AstrMessageEvent, money: int):
        """bot持有者专用，向账户添加金币"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user_id = event.get_sender_id()
        if not self.data_manager.get_user_data(user_id):
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return

        user_id = event.get_sender_id()
        self.data_manager.add_coins(user_id, money)
        current_money = self.data_manager.get_user_data(user_id)['coins']
        yield event.plain_result(f'💫 超能力使用成功，当前持有金币：{current_money}\n')

    @filter.command("打胶", alias={'导管','自摸'})
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def do_self_niu(self, event: AstrMessageEvent):
        """为自己导一发"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user_id = event.get_sender_id()
        if not self.data_manager.get_user_data(user_id):
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return
        if user_id not in self.data_manager.get_group_rank_all(group_id):
            yield event.plain_result(f'❌ 你的牛牛还没加入本群，输入“/牛牛进群”将牛牛加入本群')
            return
        user_data = self.data_manager.get_user_data(user_id)
        name = "猫猫" if user_data['items']['transfer'] else "牛牛"
        if self.is_work(user_id):
            yield event.plain_result(f'❌ 你的{name}还在卖力工作中')
            return
        if self.is_exercise(user_id):
            yield event.plain_result(f'❌ 你的{name}还在努力锻炼中')
            return
        do_self_cd = self.config['do_self_cooldown']

        can_do, remaining_text = check_cooldown(user_data['time_recording']['do_self'], do_self_cd)
        # 判断伟哥次数
        if can_do or user_data['items']['viagra']>0:
            if user_data['items']['transfer']:
                yield event.plain_result(self.do_self.do_self_mao(group_id, user_id))
            else:
                yield event.plain_result(self.do_self.do_self_niu(group_id, user_id))
        else:
            yield event.plain_result(f'❌ 你的{name}还在贤者模式，cd剩余：{remaining_text}')

    @filter.command("锁牛牛", alias={'嗦牛牛'})
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def do_other_niu(self, event: AstrMessageEvent):
        """锁群友牛牛"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user1_id = event.get_sender_id()
        for comp in event.message_obj.message:
            if isinstance(comp, At):
                user2_id = str(comp.qq)
                if not self.data_manager.get_user_data(user2_id):
                    yield event.plain_result(f'❌ 他的牛牛还没出生，需要对方输入“/创建牛牛”创建牛牛')
                    return
                if user2_id not in self.data_manager.get_group_rank_all(group_id):
                    yield event.plain_result(f'❌ 他的牛牛未加入本群，无法锁他牛牛')
                    return
                name = "猫猫" if self.data_manager.get_user_data(user2_id)['items']['transfer'] else "牛牛"
                if self.is_work(user2_id):
                    yield event.plain_result(f'❌ 他的{name}还在卖力工作中')
                    return
                if self.is_exercise(user2_id):
                    yield event.plain_result(f'❌ 他的{name}还在努力锻炼中')
                    return
                yield event.plain_result(self.do_other.do_other_niu(group_id,user1_id, user2_id,self.config['do_other_cooldown']))
                return
        yield event.plain_result("锁牛牛需要@想要锁的人")

    @filter.command("锻炼", alias={'牛牛锻炼','猫猫锻炼'})
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def do_exercise(self, event: AstrMessageEvent, hours:int=1):
        """让牛牛/猫猫强身健体"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user_id = event.get_sender_id()
        if not self.data_manager.get_user_data(user_id):
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return
        if hours*3600 >self.config['max_exercise_hours'] or hours<1:
            yield event.plain_result(f'❌ 锻炼时长范围需要在1~{self.config["max_exercise_hours"]/3600}小时')
            return

        user_data = self.data_manager.get_user_data(user_id)
        name = "猫猫" if user_data['items']['transfer'] else "牛牛"
        text = ''
        can_exercise, remain_text = check_cooldown(user_data['time_recording']['start_exercise'][0],
                                               user_data['time_recording']['start_exercise'][1])
        if can_exercise:
            user_data['time_recording']['start_exercise'][0] = time.time()
            user_data['time_recording']['start_exercise'][1] = hours * 3600
            if user_data['items']['transfer']:
                # 结算硬度
                if user_data['items']['jump_egg']:
                    reward = 3 * 2 * hours
                    user_data['items']['jump_egg'] = False
                else:
                    reward = 3 * hours
                user_data['sensitivity'] += reward
                text += f"💦 猫猫将会在跳蛋的帮助下锻炼了{hours}小时，敏感度增加{reward}级\n"
            else:
                if user_data['items']['sandbag']:
                    reward = 3 * 2 * hours
                    user_data['items']['sandbag'] = False
                else:
                    reward = 3 * hours
                user_data['hardness'] += reward
                text += f"💦 牛牛将会在沙袋的帮助下锻炼了{str(hours)}小时，硬度增加{reward}级\n"
            self.data_manager.save_user_data(user_id, user_data)
            yield event.plain_result(text)

            async def after_exercise():
                user_data = self.data_manager.get_user_data(user_id)
                sleep_time = user_data['time_recording']['start_exercise'][1] + 5
                await asyncio.sleep(sleep_time)

                user_data = self.data_manager.get_user_data(user_id)
                if check_cooldown(user_data['time_recording']['start_exercise'][0],
                                  user_data['time_recording']['start_exercise'][1])[0]:
                    umo = event.unified_msg_origin
                    message_chain = MessageChain().at(user_data["user_name"], user_id).message(
                        f'💦 {name}的锻炼结束了\n')
                    await self.context.send_message(umo, message_chain)

            task = asyncio.create_task(after_exercise())
            self.task[f"exercise_{group_id}_{user_id}"] = task
        else:
            text += f"❌ 你的{name}正在努力锻炼中，剩余时间：{remain_text}\n"
            yield event.plain_result(text)

    def is_exercise(self,user_id):
        user_data = self.data_manager.get_user_data(user_id)
        return not check_cooldown(user_data['time_recording']['start_exercise'][0],user_data['time_recording']['start_exercise'][1])[0]

    def is_work(self,user_id):
        user_data = self.data_manager.get_user_data(user_id)
        return not check_cooldown(user_data['time_recording']['start_work'][0],user_data['time_recording']['start_work'][1])[0]

    @filter.command("打工", alias={'牛牛打工','猫猫打工','工作'})
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def do_work(self, event: AstrMessageEvent,hours:int=1):
        """让牛牛/猫猫打工赚钱"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user_id = event.get_sender_id()
        if not self.data_manager.get_user_data(user_id):
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return
        if hours*3600 >self.config['max_work_hours'] or hours<1:
            yield event.plain_result(f'❌ 打工时长范围需要在1~{self.config["max_work_hours"]/3600}小时')
            return

        user_data = self.data_manager.get_user_data(user_id)
        name = "猫猫" if user_data['items']['transfer'] else "牛牛"
        text = ''
        can_work, remain_text = check_cooldown(user_data['time_recording']['start_work'][0],
                                               user_data['time_recording']['start_work'][1])
        if can_work:
            user_data['time_recording']['start_work'][0] = time.time()
            user_data['time_recording']['start_work'][1] = hours
            if user_data['items']['transfer']:
                # 结算钱
                reward = self.config['coins_per_hour'] * 2 * hours
                user_data['coins'] += reward
                text += f"💰️ 猫猫需要陪客人{hours}小时，结算工资：{reward}金币\n"
            else:
                reward = self.config['coins_per_hour'] * hours
                user_data['coins'] += reward
                text += f"💰️ 牛牛需要陪客人{hours}小时，结算工资：{reward}金币\n"
            self.data_manager.save_user_data(user_id, user_data)
            yield event.plain_result(text)

            async def after_work():
                user_data = self.data_manager.get_user_data(user_id)
                sleep_time = user_data['time_recording']['start_work'][1] + 5
                await asyncio.sleep(sleep_time)

                user_data = self.data_manager.get_user_data(user_id)
                if check_cooldown(user_data['time_recording']['start_work'][0],
                                  user_data['time_recording']['start_work'][1])[0]:
                    umo = event.unified_msg_origin
                    message_chain = MessageChain().at(user_data["user_name"], user_id).message(
                        f'💰️ {name}的打工结束了\n')
                    await self.context.send_message(umo, message_chain)

            task = asyncio.create_task(after_work())
            self.task[f"work_{group_id}_{user_id}"] = task
        else:
            text += f"❌ 你的{name}正在卖力打工中，剩余时间：{remain_text}\n"
            yield event.plain_result(text)

    @filter.command("转账", alias={'转钱'})
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def give_money(self, event: AstrMessageEvent, money: int):
        """向指定用户转账"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user1_id = event.get_sender_id()
        if not self.data_manager.get_user_data(user1_id):
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return
        user1_data = self.data_manager.get_user_data(user1_id)
        have_money = user1_data['coins']
        if have_money < money:
            yield event.plain_result(f'当前金币不足{money}，持有金币：{have_money}')
            return
        else:
            for comp in event.message_obj.message:
                if isinstance(comp, At):
                    user2_id = str(comp.qq)
                    if not self.data_manager.get_user_data(user2_id):
                        yield event.plain_result(f'❌ 他的牛牛还没出生，需要对方输入“/创建牛牛”创建牛牛')
                        return
                    self.data_manager.del_coins(user1_id, money)
                    self.data_manager.add_coins(user2_id, money)
                    yield event.plain_result("✅ 转账成功")
                    return
            yield event.plain_result("❌ 转账需要@想要转账的人")

    @filter.command_group("使用道具", alias={'使用'})
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    def use_item(self):
        """使用道具命令组"""
        pass

    @use_item.command("牛牛寄生虫", alias={'寄生虫','15'})
    async def use_drone(self, event: AstrMessageEvent, num: int = 1):
        """使用牛牛寄生虫"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user1_id = event.get_sender_id()
        for comp in event.message_obj.message:
            if isinstance(comp, At):
                user2_id = str(comp.qq)
                if not self.data_manager.get_user_data(user2_id):
                    yield event.plain_result(f'❌ 他的牛牛还没出生，需要对方输入“/创建牛牛”创建牛牛')
                    return
                if user2_id not in self.data_manager.get_group_rank_all(group_id):
                    yield event.plain_result(f'❌ 他的牛牛未加入本群，无法寄生')
                    return
                yield event.plain_result(self.shop.use_drone(user1_id, user2_id, num))
                return
        yield event.plain_result(f'❌ 使用牛牛寄生虫需要@想要寄生的人')

    @use_item.command("六味地黄丸", alias={'必胜药','7'})
    async def use_pill(self, event: AstrMessageEvent):
        """使用六味地黄丸"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user_id = event.get_sender_id()
        if not self.data_manager.get_user_data(user_id):
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return
        yield event.plain_result(self.shop.use_sure_win(user_id))

    @use_item.command("负重沙袋", alias={'沙袋', '8'})
    async def use_sandbag(self, event: AstrMessageEvent):
        """使用负重沙袋"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user_id = event.get_sender_id()
        if not self.data_manager.get_user_data(user_id):
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return
        yield event.plain_result(self.shop.use_sandbag(user_id))

    @use_item.command("会跳的蛋", alias={'跳蛋', '9'})
    async def use_jump_egg(self, event: AstrMessageEvent):
        """使用会跳的蛋"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user_id = event.get_sender_id()
        if not self.data_manager.get_user_data(user_id):
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return
        yield event.plain_result(self.shop.use_jumping_egg(user_id))

    @use_item.command("黑店壮丁手术体验卡", alias={'黑店手术', '黑店','4'})
    async def use_big_d_1(self, event: AstrMessageEvent):
        """使用黑店壮丁手术体验卡"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user_id = event.get_sender_id()
        if not self.data_manager.get_user_data(user_id):
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return
        yield event.plain_result(self.shop.use_big_d(group_id, user_id, 0.3))

    @use_item.command("诊所壮丁手术体验卡", alias={'诊所手术', '诊所','5'})
    async def use_big_d_2(self, event: AstrMessageEvent):
        """使用诊所壮丁手术体验卡"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user_id = event.get_sender_id()
        if not self.data_manager.get_user_data(user_id):
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return
        yield event.plain_result(self.shop.use_big_d(group_id, user_id, 0.5))

    @use_item.command("医院壮丁手术体验卡", alias={'医院手术', '医院','6'})
    async def use_big_d_3(self, event: AstrMessageEvent):
        """使用医院壮丁手术体验卡"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user_id = event.get_sender_id()
        if not self.data_manager.get_user_data(user_id):
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return
        yield event.plain_result(self.shop.use_big_d(group_id, user_id, 0.7))

    @use_item.command("杀虫剂", alias={'杀虫','18'})
    async def use_insecticide(self, event: AstrMessageEvent, num: int = 1):
        """使用杀虫剂"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user1_id = event.get_sender_id()
        if not self.data_manager.get_user_data(user1_id):
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return
        yield event.plain_result(self.shop.use_insecticide(user1_id, num))

    @use_item.command("牛牛盲盒", alias={'盲盒','14'})
    async def use_cassette(self, event: AstrMessageEvent):
        """使用牛牛盲盒"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user_id = event.get_sender_id()
        if not self.data_manager.get_user_data(user_id):
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return
        yield event.plain_result(self.shop.use_cassette(user_id))

    @use_item.command("伟哥",alias={'1'})
    async def use_viagra(self, event: AstrMessageEvent,num:int=1):
        """使用牛牛盲盒"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user_id = event.get_sender_id()
        if not self.data_manager.get_user_data(user_id):
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return
        yield event.plain_result(self.shop.use_viagra(user_id,num))

    @use_item.command("猫猫转换器", alias={'猫猫转换','12'})
    async def use_exchange_mao(self, event: AstrMessageEvent):
        """使用猫猫转换器"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user1_id = event.get_sender_id()
        if not self.data_manager.get_user_data(user1_id):
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return
        for comp in event.message_obj.message:
            if isinstance(comp, At):
                user2_id = str(comp.qq)
                user2_data = self.data_manager.get_user_data(user2_id)
                if not user2_data:
                    yield event.plain_result(f'❌ 他的牛牛还没出生，需要对方输入“/创建牛牛”创建牛牛')
                    return
                if user2_id not in self.data_manager.get_group_rank_all(group_id):
                    yield event.plain_result(f'❌ 他的牛牛还没加入本群，需要对方输入“/牛牛进群”将牛牛加入本群')
                    return
                yield event.plain_result(self.shop.use_exchange_mao(user1_id, user2_id))
                return
        yield event.plain_result(f'❌ 使用猫猫转换器需要@想要转换的人')

    @use_item.command("牛牛转换器", alias={'牛牛转换','11'})
    async def use_exchange_niu(self, event: AstrMessageEvent):
        """使用牛牛转换器"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user1_id = event.get_sender_id()
        if not self.data_manager.get_user_data(user1_id):
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return
        for comp in event.message_obj.message:
            if isinstance(comp, At):
                user2_id = str(comp.qq)
                user2_data = self.data_manager.get_user_data(user2_id)
                if not user2_data:
                    yield event.plain_result(f'❌ 他的牛牛还没出生，需要对方输入“/创建牛牛”创建牛牛')
                    return
                if user2_id not in self.data_manager.get_group_rank_all(group_id):
                    yield event.plain_result(f'❌ 他的牛牛还没加入本群，需要对方输入“/牛牛进群”将牛牛加入本群')
                    return
                yield event.plain_result(self.shop.use_exchange_niu(user1_id, user2_id))
                return
        yield event.plain_result(f'❌ 使用牛牛转换器需要@想要转换的人')

    @use_item.command("迷幻菌子", alias={'菌子','2'})
    async def use_mushroom(self, event: AstrMessageEvent):
        """使用迷幻菌子"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user1_id = event.get_sender_id()
        if not self.data_manager.get_user_data(user1_id):
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return
        yield event.plain_result(self.shop.use_mushroom(group_id, user1_id, self.config['do_self_cooldown']))

    @use_item.command("春天的药", alias={'春药', '3'})
    async def use_aphrodisiac(self, event: AstrMessageEvent):
        """使用春天的药"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user1_id = event.get_sender_id()
        if not self.data_manager.get_user_data(user1_id):
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return
        yield event.plain_result(self.shop.use_aphrodisiac(group_id, user1_id, self.config['do_other_cooldown']))

    @use_item.command("性转针筒", alias={'性转', '针筒','10'})
    async def use_trans(self, event: AstrMessageEvent):
        """使用性转针筒"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user1_id = event.get_sender_id()
        if not self.data_manager.get_user_data(user1_id):
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return
        user_data = self.data_manager.get_user_data(user1_id)
        name = "猫猫" if user_data['items']['transfer'] else "牛牛"
        if self.is_work(user1_id):
            yield event.plain_result(f'❌ 你的{name}还在卖力工作中')
            return
        if self.is_exercise(user1_id):
            yield event.plain_result(f'❌ 你的{name}还在努力锻炼中')
            return
        yield event.plain_result(self.shop.use_trans(user1_id))

        async def restore_gender():
            sleep_seconds = self.config['trans_time']
            await asyncio.sleep(sleep_seconds)

            user_data = self.data_manager.get_user_data(user1_id)
            if user_data['items']['transfer']:
                self.data_manager.set_value(user1_id, ['items', 'transfer'], False)
                umo = event.unified_msg_origin
                message_chain = MessageChain().at(user_data["user_name"], user1_id).message(
                    '🔄 你的性转时间结束了，猫猫离去，牛牛回归\n')
                await self.context.send_message(umo, message_chain)

        task = asyncio.create_task(restore_gender())
        # 需要保留任务引用（如保存为实例变量），防止被GC提前回收
        self.task[f"trans_{group_id}_{user1_id}"] = task

    @use_item.command("八折优惠券", alias={'八折', '优惠券','17'})
    async def use_20off(self, event: AstrMessageEvent):
        """使用八折优惠券"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user1_id = event.get_sender_id()
        if not self.data_manager.get_user_data(user1_id):
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return
        yield event.plain_result(self.shop.use_20off(user1_id))

        async def restore_price():
            sleep_seconds = 5 * 60
            await asyncio.sleep(sleep_seconds)

            user_data = self.data_manager.get_user_data(user1_id)
            if user_data['items']['20off']:
                self.data_manager.set_value(user1_id, ['items', '20off'], False)
                umo = event.unified_msg_origin
                message_chain = MessageChain().at(user_data["user_name"], user1_id).message(
                    '🎫 8折优惠券效果结束，商店价格恢复\n')
                await self.context.send_message(umo, message_chain)

        task = asyncio.create_task(restore_price())
        # 需要保留任务引用（如保存为实例变量），防止被GC提前回收
        self.task[f"20off_{group_id}_{user1_id}"] = task

    @use_item.command("春风精灵", alias={'精灵','13'})
    async def use_elf(self, event: AstrMessageEvent):
        """使用春风精灵"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        user1_id = event.get_sender_id()
        if not self.data_manager.get_user_data(user1_id):
            yield event.plain_result(f'❌ 你的牛牛还没出生，输入“/创建牛牛”创建牛牛')
            return
        yield event.plain_result(self.shop.use_fling(user1_id))

        async def start_do_self():
            user_data = self.data_manager.get_user_data(user1_id)
            end_time = user_data['time_recording']['start_elf'] + 3600
            while time.time() < end_time:
                user_data = self.data_manager.get_user_data(user1_id)
                last_do_self = user_data['time_recording']['do_self']
                can_do, _ = check_cooldown(last_do_self, self.config['do_self_cooldown'])
                if can_do:
                    if user_data['items']['elf_reminder']:
                        is_trans = user_data['items']['transfer']
                        text = self.do_self.do_self_mao(group_id, user1_id) if is_trans else self.do_self.do_self_niu(
                            group_id, user1_id)
                        message_chain = MessageChain().at(user_data["user_name"], user1_id).message(
                            '🧚 春风精灵提醒\n' + text)
                        await self.context.send_message(event.unified_msg_origin, message_chain)
                else:
                    sleep_seconds = max(1, last_do_self + self.config['do_self_cooldown'] - time.time())
                    await asyncio.sleep(sleep_seconds)
            if user_data['items']['elf_reminder']:
                message_chain = MessageChain().at(user_data["user_name"], user1_id).message(
                    '🧚 春风精灵效果结束\n')
                await self.context.send_message(event.unified_msg_origin, message_chain)

        task = asyncio.create_task(start_do_self())
        # 需要保留任务引用（如保存为实例变量），防止被GC提前回收
        self.task[f"elf_{group_id}_{user1_id}"] = task

    @filter.command_group("配置")
    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    def config(self):
        """全局配置命令组"""
        pass

    @filter.permission_type(PermissionType.ADMIN)
    @config.command("添加名字非法词", alias={'添加非法词', '禁用词'})
    async def add_illegal(self, event: AstrMessageEvent, illegal: str):
        """为取名功能添加禁用词"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        disabled_list = self.config['disabled_name']
        if illegal in disabled_list:
            yield event.plain_result('⚠️ 该词已是非法词，无需添加')
        else:
            disabled_list.append(illegal)
            self.config['disabled_name'] = disabled_list
            self.config.save_config()
            yield event.plain_result('✅ 添加成功该词为非法词')

    @filter.permission_type(PermissionType.ADMIN)
    @config.command("删除名字非法词", alias={'删除非法词'})
    async def del_illegal(self, event: AstrMessageEvent, illegal: str):
        """删除已添加的禁用词"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        disabled_list = self.config['disabled_name']
        if illegal in disabled_list:
            disabled_list.remove(illegal)
            self.config['disabled_name'] = disabled_list
            self.config.save_config()
            yield event.plain_result('✅ 成功删除该词')
        else:
            yield event.plain_result('❌ 该词不在禁用列表')

    @filter.permission_type(PermissionType.ADMIN)
    @config.command("打胶cd", alias={'导管cd'})
    async def set_do_self_cd(self, event: AstrMessageEvent, cd: int):
        """设置打胶/自摸cd"""
        group_id = event.get_group_id()
        if not self.check_group_enable(group_id):
            yield event.plain_result("❌ 牛牛插件未启用")
            return
        if cd < 0:
            yield event.plain_result('❌ 导管cd不能小于0')
            return
        original_cd = self.config['do_self_cooldown']
        if cd == original_cd:
            yield event.plain_result(f'❌ 打胶cd已是{original_cd}分钟')
            return
        self.config['do_self_cooldown'] = cd
        self.config.save_config()
        yield event.plain_result(f'✅ 打胶cd设置成功：{cd}分钟')

    async def terminate(self):
        """可选择实现 terminate 函数，当插件被卸载/停用时会调用。"""
        pass
