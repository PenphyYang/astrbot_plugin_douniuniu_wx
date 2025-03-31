import math
import random

from data.plugins.astrbot_plugin_douniuniu.core.data_manager import DataManager
from data.plugins.astrbot_plugin_douniuniu.core.utils import probabilistic_decision, random_normal_distribution_int, \
    format_length, get_add_text


class Battle:
    def __init__(self):
        self.data_manager = DataManager()
        self.record_breaking_reward = 50  # 每级破纪录递增收益数

    def niu_vs_niu_win_prob(self, user1_id, user2_id):
        """
        计算进攻方获胜概率
        :param user1_id:
        :param user2_id:
        :return: 'user1'（进攻方胜）/'user2'（防守方胜）/'draw'（平局）
        """
        # 属性权重分配（硬度权重更高）
        HARDNESS_WEIGHT = 0.7  # 硬度权重
        LENGTH_WEIGHT = 0.3  # 长度权重

        user1_data = self.data_manager.get_user_data(user1_id)
        user2_data = self.data_manager.get_user_data(user2_id)

        # 计算双方综合战斗力（硬度主导）
        attack_power = user1_data['length'] * LENGTH_WEIGHT + user1_data['hardness'] * HARDNESS_WEIGHT
        defend_power = user2_data['length'] * LENGTH_WEIGHT + user2_data['hardness'] * HARDNESS_WEIGHT

        # 基础胜率计算（Sigmoid函数平滑差异）
        power_diff = attack_power - defend_power
        # 判断必赢道具,只判断进攻者，道具效果为进攻必赢
        if user1_data['items']['pills']:
            user1_data['items']['pills'] = False
            self.data_manager.save_user_data(user1_id, user1_data)
            return 'user1', power_diff
        base_prob = 1 / (1 + math.exp(-power_diff * 0.5))  # 0.5控制曲线陡峭度

        # 引入随机扰动保障弱者机会（±15%波动）
        random_factor = random.uniform(-0.15, 0.15)
        final_prob = max(0.1, min(0.9, base_prob + random_factor))  # 锁定10%~90%胜率

        # 平局概率（双方战斗力越接近，平局概率越高）
        draw_prob = max(0, 0.3 - 0.03 * abs(power_diff))  # 线性衰减模型

        # 生成随机数判断结果
        rand = random.random()
        if rand < draw_prob:
            return 'draw', power_diff
        elif rand < draw_prob + final_prob * (1 - draw_prob):
            return 'user1', power_diff
        else:
            return 'user2', power_diff

    def niu_vs_niu(self, group_id, user1_id, user2_id) -> str:
        """牛牛与牛牛对战"""
        # 先获取初始数据
        user1_data = self.data_manager.get_user_data(user1_id)
        user2_data = self.data_manager.get_user_data(user2_id)
        # 获取名称
        user1_niuniu_name = user1_data['niuniu_name']
        user2_niuniu_name = user2_data['niuniu_name']
        user1_name = self.data_manager.get_group_rank_all(group_id)[user1_id][0]
        user2_name = self.data_manager.get_group_rank_all(group_id)[user2_id][0]
        # 计算战斗结果
        winner, power_diff = self.niu_vs_niu_win_prob(user1_id, user2_id)
        text = ''
        if winner == 'draw':
            # 公布结果
            text += "⚖️ 双方的牛牛势均力敌！\n"
            # 后续
            random_num = random.random()
            if random_num < 0.2:
                text += "📢 俩牛牛不打不相识，这场战斗让双方都获得了成长\n\n"
                user1_add = random_normal_distribution_int(1, 6, 2)
                user1_true_add = self.data_manager.add_length(group_id, user1_id, user1_add)
                text += get_add_text(user1_true_add,user1_add,user1_niuniu_name,self.data_manager.get_user_data(user1_id))

                user2_add = random_normal_distribution_int(1, 6, 2)
                user2_true_add = self.data_manager.add_length(group_id, user2_id, user2_add)
                text += get_add_text(user2_true_add, user2_add, user2_niuniu_name,
                                     self.data_manager.get_user_data(user2_id))
            elif random_num < 0.4:
                text += "📢 双方的牛牛即使激战过后依然缠绕在一起，强制分开导致长度减半\n\n"
                user1_del = int(user1_data['length'] / 2)
                user2_del = int(user2_data['length'] / 2)
                self.data_manager.del_length(group_id, user1_id, user1_del)
                self.data_manager.del_length(group_id, user2_id, user2_del)
                text += f"📏 {user1_niuniu_name}的长度减少{user1_del}cm\n"
                text += f"📏 {user2_niuniu_name}的长度减少{user2_del}cm\n"
            elif random_num < 0.6:
                loser_id = random.choice([user1_id, user2_id])
                loser_name = user1_niuniu_name if loser_id == user1_id else user2_niuniu_name
                text += f"📢 {loser_name}不愿承认平局，对自己的长度产生了自我怀疑\n\n"
                loser_del = random_normal_distribution_int(1, 6, 1)
                self.data_manager.del_length(group_id, loser_id, loser_del)
                text += f"📏 {loser_name}的长度减少{loser_del}cm\n"
            else:
                text += "📢 之后无事发生，下一次再见面想必又会有一场厮杀吧\n"
            text += "💰 平局双方均无收益"
            return text
        elif winner == 'user1':
            winner_name = user1_niuniu_name
            winner_id = user1_id
            winner_data = user1_data
            winner_user = user1_name

            loser_name = user2_niuniu_name
            loser_id = user2_id
            loser_data = user2_data
            loser_user = user2_name
        else:
            winner_name = user2_niuniu_name
            winner_id = user2_id
            winner_data = user2_data
            winner_user = user2_name

            loser_name = user1_niuniu_name
            loser_id = user1_id
            loser_data = user1_data
            loser_user = user1_name
            # 需要将优势计算反转一下
            power_diff = -power_diff
        # 公布结果
        if power_diff > 0:
            text += random.choice([
                f"🥊 {winner_name}在这场决斗中势不可挡\n\n",
                f"🥊 {winner_name}展现了天牛下凡般的实力\n\n",
                f"🥊 {winner_name}获得了胜利并擦了擦身上在决斗时留下的液体\n\n",
                f"🥊 整个战场变成{winner_name}的单方面碾压，{loser_name}被按在地上摩擦\n\n",
            ])
            # 后续
            winner_add_length = random_normal_distribution_int(1, 6, 1)
            winner_ture_add = self.data_manager.add_length(group_id, winner_id, winner_add_length)
            text += get_add_text(winner_ture_add, winner_add_length, winner_name,
                                 self.data_manager.get_user_data(winner_id))

            loser_del_length = random_normal_distribution_int(1, 6, 1)
            self.data_manager.del_length(group_id, loser_id, loser_del_length)
            text += f"📏 {loser_name}的长度减少{loser_del_length}cm，当前长度：{format_length(self.data_manager.get_user_data(loser_id)['length'])}\n"
            # 结算收益
            winner_add_coins = random_normal_distribution_int(1, 21, 2)
            self.data_manager.add_coins(winner_id, winner_add_coins)
            text += f"💰 {winner_user}获得了{winner_add_coins}个金币\n"
        else:
            text += random.choice([
                f"🥊 {winner_name}在这场决斗中觉醒出了新的实力，终结了{loser_name}\n\n",
                f"🥊 {winner_name}顽强挣扎，活生生耗光了{loser_name}的体力\n\n",
                f"🥊 {winner_name}失去了意识，但依旧给了{loser_name}最后一击\n\n",
                f"🥊 {winner_name}居然是扮猪吃老虎，完全拿捏了{loser_name}\n\n",
            ])
            # 后续
            winner_add_length = random_normal_distribution_int(10, 21, 1)
            winner_ture_add = self.data_manager.add_length(group_id, winner_id, winner_add_length)
            if winner_ture_add < winner_add_length:
                text += f"📏 {winner_name}劣势获胜，长度在被寄生虫蚕食后暴增了{winner_ture_add}cm，当前长度：{format_length(self.data_manager.get_user_data(winner_id)['length'])}\n"
                text += f'各寄生虫窃取到了{winner_ture_add}，回馈到主人的牛牛中\n'
            else:
                text += f"📏 {winner_name}劣势获胜，长度暴增{winner_ture_add}cm，当前长度：{format_length(self.data_manager.get_user_data(winner_id)['length'])}\n"

            loser_del_length = random_normal_distribution_int(10, 21, 1)
            self.data_manager.del_length(group_id, loser_id, loser_del_length)
            text += f"📏 {loser_name}优势落败，长度骤减{loser_del_length}cm，当前长度：{format_length(self.data_manager.get_user_data(loser_id)['length'])}\n"

            # 结算收益
            if winner_data['items']['pills']:
                text += f"💰 六味地黄丸使用成功，本次胜利不获得金币\n"
            else:
                winner_add_coins = random_normal_distribution_int(20, 41, 2)
                self.data_manager.add_coins(winner_id, winner_add_coins)
                text += f"💰 由于是劣势获胜，{winner_user}得到了牛牛女神的馈赠，获得{winner_add_coins}个金币\n"
        # 结算连胜
        if self.data_manager.reset_win_count(loser_id):
            text += f"😱 {winner_name}终结了{loser_name}的{loser_data['current_win_count']}连胜，{winner_name}会成为下一个牛牛魔王吗？\n"
        # 如果破纪录
        if self.data_manager.update_win_count(winner_id):
            text += f"😈 {winner_name}取得了{self.data_manager.get_user_data(winner_id)['current_win_count']}连胜，打破了自己的最高连胜记录！\n"
            # 破纪录收益
            reward = self.data_manager.get_user_data(winner_id)['current_win_count'] * self.record_breaking_reward
            text += f"💰 由于打破了最高记录，获得了{reward}个金币，下一级收益：{reward + self.record_breaking_reward}\n"
        user1_data = self.data_manager.get_user_data(user1_id)
        current_win_count = user1_data['current_win_count']
        win_count = user1_data['win_count']
        text += f'⚔ 当前连胜：{current_win_count} | 最高连胜：{win_count}'
        return text

    def niu_vs_hole(self, group_id, user1_id, user2_id) -> str:
        pass

    def hole_vs_niu(self, group_id, user1_id, user2_id) -> str:
        pass

    def hole_vs_hole(self, group_id, user1_id, user2_id) -> str:
        pass
