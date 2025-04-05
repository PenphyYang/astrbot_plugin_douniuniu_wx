import random
import time

from data.plugins.astrbot_plugin_douniuniu.core.data_manager import DataManager
from data.plugins.astrbot_plugin_douniuniu.core.utils import random_normal_distribution_int, get_add_text, \
    format_length, check_cooldown


class DoOther:
    def __init__(self):
        self.data_manager = DataManager()
        self.probabilities_niu = {
            '锁爽了': 50,
            '锁痛了': 30,
            '躲了': 15,
            '锁断了': 5,  # 长度减半
        }
        self.reason_niu = {
            '锁爽了': [
                '🥵 对方完全陶醉在你的口技之中',
                '🥵 对方对你的技术赞不绝口，他的牛牛在这个过程中获得了成长',
            ],
            '锁痛了': [
                '😡 锁的过程中你突然想磨牙，最终没控制好力道把对方锁痛了',
                '😡 对方想脱离你的夺命连环锁，但是你就是不松口，强制脱离导致断了一节',
            ],
            '躲了': [
                '🤡 对方一个转身躲过了你的血盆大口',
                '🤡 对方牛牛捏捏的说：“今天状态不好，还是算了吧”',
                '🤡 就在你准备开始的时候，对方的牛牛突然被另一个群友锁住',
            ],
            '锁断了': [
                '😱 对方的牛牛突然开始融化，你在完全融化之前松了口',
                '😱 对方的牛牛堵得你喘不过气，快窒息的你求生意识下咬断了一节',
            ]
        }

    def do_other_niu(self, group_id,user1_id, user2_id,do_other_cd) -> str:
        """1锁2的牛牛"""
        user1_data = self.data_manager.get_user_data(user1_id)
        user2_data = self.data_manager.get_user_data(user2_id)
        text = ''
        can_do_other,remain_time = check_cooldown(user1_data['time_recording']['do_other'],do_other_cd)
        if not can_do_other:
            text += f'❌ 心急锁不到热牛牛，cd剩余：{remain_time}'
            return text
        # 更新1的cd
        self.data_manager.set_value(user1_id,['time_recording','do_other'],time.time())
        result = random.choices(
            list(self.probabilities_niu.keys()),
            weights=list(self.probabilities_niu.values()),
            k=1
        )[0]
        # 添加原因
        text += f"{random.choice(self.reason_niu[result])}\n"
        niuniu_name = user2_data['niuniu_name']
        # 各个原因具体处理
        if result == '锁爽了':
            add_length = random_normal_distribution_int(1, 6, 1)
            true_length = self.data_manager.add_length(group_id, user2_id, add_length)
            text += get_add_text(true_length, add_length, user2_data)
        elif result == '锁痛了':
            del_length = random_normal_distribution_int(1, 4, 1)
            self.data_manager.del_length(user2_id, del_length)
            user2_data = self.data_manager.get_user_data(user2_id)
            text += f"📏 {niuniu_name}的长度减少了{del_length}cm，当前长度：{format_length(user2_data['length'])}\n"
        elif result == '躲了':
            pass
        elif result == '锁断了':
            del_length = int(user2_data['length'] / 2)
            user2_data['length'] -= del_length
            self.data_manager.save_user_data(user2_id, user2_data)
            text += f"📏 {niuniu_name}的长度减少了{del_length}cm，当前长度：{format_length(user2_data['length'])}\n"
        return text

    def do_other_mao(self, group_id, user1_id, user2_id, do_other_cd) -> str:
        return ''
