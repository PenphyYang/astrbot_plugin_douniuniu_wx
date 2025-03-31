from collections import OrderedDict

import yaml
import json
import os
from typing import Dict, Any
from pathlib import Path

from data.plugins.astrbot_plugin_douniuniu.core.exceptions import DataLoadError, DataSaveError
from data.plugins.astrbot_plugin_douniuniu.core.utils import random_normal_distribution_int, format_length


class DataManager:
    def __init__(self, file_path='data/douniuniu_plugin/user.yaml'):
        self.file_path = Path(file_path)
        self._ensure_file_exists()
        self.default_yaml = {
            "groups": {},
            "users": {}
        }

    def _ensure_file_exists(self):
        """确保必要文件存在"""
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, 'w') as f:
                yaml.dump(self.default_yaml, f)

    # --------------------------
    # 核心方法
    # --------------------------
    def load_all_data(self) -> Dict[str, Any]:
        """加载全部数据"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or self.default_yaml
        except Exception as e:
            raise DataLoadError(str(self.file_path), str(e))

    def save_all_data(self, data: Dict[str, Any]):
        """保存全部数据"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True)
        except Exception as e:
            raise DataSaveError(str(self.file_path), str(e))

    def get_group_data(self, group_id: str) -> Dict[str, Any]:
        """获取群数据（不存在时初始化）"""
        data = self.load_all_data()
        group_id = str(group_id)

        if group_id not in data["groups"]:
            data["groups"][group_id] = {
                "plugin_enabled": False,
                "manager": ["1097694383"],
                "rank": {}
            }
            self.save_all_data(data)

        return data["groups"][group_id]

    def save_group_data(self, group_id: str, group_data: Dict[str, Any]):
        """保存群数据"""
        data = self.load_all_data()
        data["groups"][str(group_id)] = group_data
        self.save_all_data(data)

    def get_group_rank_all(self, group_id: str) -> Dict[str, Any]:
        """获取群排行榜数据，无排序"""
        group_data = self.get_group_data(group_id)
        return group_data['rank']

    def get_group_rank_n(self, group_id: str, n: int = 10) -> Dict[str, Any]:
        """获取群前n名排行榜数据，有排序，默认前十名"""
        rank_data = self.get_group_data(group_id)['rank']
        sorted_items = sorted(rank_data.items(), key=lambda x: x[1][1], reverse=True)[:n]
        sorted_rank_data_n = OrderedDict(sorted_items)
        return sorted_rank_data_n

    def save_group_rank(self, group_id: str, rank_data: Dict[str, Any]):
        """保存排行榜数据"""
        group_data = self.get_group_data(group_id)
        group_data['rank'] = rank_data
        self.save_group_data(group_id, group_data)

    def update_rank(self, group_id, user_id, user_name):
        """加入/更新排行榜"""
        rank = self.get_group_rank_all(group_id)
        user_data = self.get_user_data(user_id)
        score = round(user_data['length'] * 0.3 + user_data['hardness'] *0.7, 2)

        rank[str(user_id)] = [str(user_name), score]
        self.save_group_rank(group_id, rank)

    def get_user_data(self, user_id: str) -> Dict[str, Any]:
        """获取用户数据（不存在时返回空字典）"""
        data = self.load_all_data()
        return data["users"].get(str(user_id), {})

    def save_user_data(self, user_id: str, user_data: Dict[str, Any]):
        """保存用户数据"""
        data = self.load_all_data()
        data["users"][str(user_id)] = user_data
        self.save_all_data(data)

    def create_user(self, group_id: str, user_id: str, user_name: str):
        """创建一个初始化牛牛"""
        min_length = 1
        max_length = 10
        init_length = random_normal_distribution_int(min_length, max_length + 1, 1)
        init_hardness = random_normal_distribution_int(min_length, max_length + 1, 1)

        if init_length / (max_length - min_length + 1) < 0.3:
            message = '😑 长度好短，牛牛从小就自卑\n'
        elif init_length / (max_length - min_length + 1) <= 0.6:
            message = '🤨 长度资质平平，牛牛达到了平均水平\n'
        else:
            message = '😍 长度超长！牛牛犹如天牛下凡\n'

        if init_hardness / (max_length - min_length + 1) < 0.3:
            message += '😑 硬度好软，牛牛从小体弱多病'
        elif init_hardness / (max_length - min_length + 1) <= 0.6:
            message += '🤨 硬度资质平平，牛牛能直立行走'
        else:
            message += '😍 硬度超硬！牛牛硬的像根钢管'

        init_user_data = {
            "niuniu_name": f'{user_name}的牛牛',
            "length": init_length,
            "coins": 0,
            "hardness": init_hardness,
            "hole": 0,  # 洞洞深度
            "sensitivity": 0,  # 敏感度
            "win_count": 0,  # 历史连胜最高次数
            "current_win_count": 0,  # 当前连胜最高次数
            'items': {
                # 道具状态
                'viagra': 0,  # 伟哥剩余次数
                'transfer': False,  # 是否已使用性转
                'pills': False,  # 是否有六味地黄丸效果
                'drone': [], # 寄生虫效果['user_id1','user_id2']
                'elf_reminder': False, # 春风精灵提醒
            },
            'items_num':{
                # 拥有对应商品数量统计
                '伟哥': 0,  # 伟哥
                '迷幻菌子': 0,  #
                '春天的药': 0,  #
                '黑店壮丁手术体验卡': 0,  #
                '诊所壮丁手术体验卡': 0,  # 诊所
                '医院壮丁手术体验卡': 0,  # 医院
                '六味地黄丸': 0,  # 六味地黄丸
                '负重沙袋': 0,  # 负重沙袋
                '会跳的蛋': 0,  # 会跳的蛋
                '性转针筒': 0,  # 性转针筒
                '牛牛转换器': 0,  # 牛牛转换器
                '猫猫转换器': 0,  # 猫猫转换器
                '春风精灵': 0,  # 春风精灵
                '牛牛盲盒': 0,  # 牛牛盲盒
                '牛牛寄生虫': 0,  # 牛牛寄生虫
                '改名卡': 0,  # 改名卡
                '商店8折优惠券': 0,  # 优惠券
                '杀虫剂': 0,  # 杀虫剂
            },
            'time_recording': {
                'sign': 0,  # 上次签到时间
                'do_self': 0,  # 上次打胶/自摸时间
                'do_other': 0,  # 上次锁牛牛/吸猫猫时间
                'start_work': 0,  # 开始打工的时间
                'start_exercise': 0,  # 开始锻炼的时间
                'start_trans': 0,  # 开始性转时间
                'start_20off': 0,  # 使用8折券时间
            },
        }
        # 保存数据
        self.save_user_data(user_id, init_user_data)
        # 加入排行榜
        self.update_rank(group_id, user_id, user_name)
        return message, init_length, init_hardness

    def delete_user(self, user_id: str):
        """注销指定用户"""
        pass

    def add_group_manager(self, group_id, user_id):
        """向指定群添加管理员"""
        group_data = self.get_group_data(group_id)
        if user_id not in group_data['manager']:
            group_data['manager'].append(user_id)
            self.save_group_data(group_id, group_data)

    def del_group_manager(self, group_id, user_id):
        """向指定群删除管理员"""
        group_data = self.get_group_data(group_id)
        if user_id in group_data['manager']:
            group_data['manager'].remove(user_id)
            self.save_group_data(group_id, group_data)

    def set_group_enabled(self, group_id, enabled: bool):
        """开启群里牛牛"""
        group_data = self.get_group_data(group_id)
        plugin_enabled = group_data['plugin_enabled']
        # 只有不相同的时候才做处理
        if enabled != plugin_enabled:
            group_data['plugin_enabled'] = enabled
            self.save_group_data(group_id, group_data)

    def set_value(self, user_id, item_path:list, item_value:Any):
        """修改属性参数"""
        user_data = self.get_user_data(user_id)
        if len(item_path) == 1:
            user_data[item_path[0]] = item_value
        elif len(item_path) == 2:
            user_data[item_path[0]][item_path[1]] = item_value
        self.save_user_data(user_id, user_data)

    def set_niuniu_name(self, user_id, niuniu_name: str) -> bool:
        user_data = self.get_user_data(user_id)
        # 只有不相同的时候才改
        if user_data['niuniu_name'] != str(niuniu_name):
            user_data['niuniu_name'] = str(niuniu_name)
            self.save_user_data(user_id, user_data)
            return True
        return False

    def add_length(self, group_id, user_id, length: int):
        """增加长度"""
        user_data = self.get_user_data(user_id)
        user_drone = user_data['items']['drone']
        if len(user_drone)>0:
            # 寄生虫加长度
            length = int(length/len(user_drone))
            if length>0:
                for i in user_drone:
                    self.add_length(group_id, i, length)
        user_data['length'] += length
        self.save_user_data(user_id, user_data)

        # 更新排行榜
        user_name = self.get_group_rank_all(group_id)[user_id][0]
        self.update_rank(group_id, user_id, user_name)
        # 返回实际增加长度
        return length

    def del_length(self, group_id, user_id, length: int):
        """减少长度"""
        user_data = self.get_user_data(user_id)
        user_data['length'] = max(1, user_data['length'] - length)
        self.save_user_data(user_id, user_data)

        # 更新排行榜
        user_name = self.get_group_rank_all(group_id)[user_id][0]
        self.update_rank(group_id, user_id, user_name)

    def add_hardness(self, group_id, user_id, hardness: int):
        """增加硬度"""
        user_data = self.get_user_data(user_id)
        user_data['hardness'] += hardness
        self.save_user_data(user_id, user_data)

        # 更新排行榜
        user_name = self.get_group_rank_all(group_id)[user_id][0]
        self.update_rank(group_id, user_id, user_name)

    def del_hardness(self, group_id, user_id, hardness: int):
        """减少硬度"""
        user_data = self.get_user_data(user_id)
        user_data['hardness'] = max(1, user_data['hardness'] - hardness)
        self.save_user_data(user_id, user_data)

        # 更新排行榜
        user_name = self.get_group_rank_all(group_id)[user_id][0]
        self.update_rank(group_id, user_id, user_name)

    def add_coins(self, user_id, coins: int):
        """增加金币"""
        user_data = self.get_user_data(user_id)
        user_data['coins'] += coins
        self.save_user_data(user_id, user_data)

    def del_coins(self, user_id, coins: int):
        """减少金币,金币可以为负"""
        user_data = self.get_user_data(user_id)
        user_data['coins'] -= coins
        self.save_user_data(user_id, user_data)

    def reset_win_count(self, user_id):
        """重置当前连胜次数，并返回是否终结连胜"""
        user_data = self.get_user_data(user_id)
        if user_data['current_win_count'] == 0:
            return False
        else:
            user_data['current_win_count'] = 0
            self.save_user_data(user_id, user_data)
            return True

    def update_win_count(self, user_id):
        """更新连胜次数，每次调用增加1连胜，并返回是否破纪录"""
        user_data = self.get_user_data(user_id)
        user_data['current_win_count'] += 1
        if user_data['current_win_count'] > user_data['win_count']:
            user_data['win_count'] = user_data['current_win_count']
            self.save_user_data(user_id, user_data)
            return True
        return False

    def use_item(self,user_id,item_path:list,num:int=1):
        user_data = self.get_user_data(user_id)
        if len(item_path)==2:
            user_data[item_path[0]][item_path[1]] -= num
            self.save_user_data(user_id, user_data)
