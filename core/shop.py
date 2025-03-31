from data.plugins.astrbot_plugin_douniuniu.core.data_manager import DataManager


class Shop:
    def __init__(self):
        self.data_manager = DataManager()

        self.max_len = 5
        self.items = {
            1: {"name": "伟哥", "price": 80, "description": "无视冷却连续打胶/自摸5次"},
            2: {"name": "迷幻菌子", "price": 150,
                "description": "使用后全群陷入迷幻，立即消耗本群5个人的打胶/自摸机会为自己打胶/自摸"},
            3: {"name": "春天的药", "price": 150, "description": "使用后变得欲求不满，随机挑选5人为自己锁牛牛/吸猫猫"},
            4: {"name": "黑店壮丁手术体验卡", "price": 50,
                "description": "获得一次乡下黑店的牛牛手术机会，30%概率长度翻倍，70%概率长度减半"},
            5: {"name": "诊所壮丁手术体验卡", "price": 200,
                "description": "获得一次小镇诊所的牛牛手术机会，50%概率长度翻倍，50%概率长度减半"},
            6: {"name": "医院壮丁手术体验卡", "price": 400,
                "description": "获得一次正规医院的牛牛手术机会，70%概率长度翻倍，30%概率长度减半"},
            7: {"name": "六味地黄丸", "price": 100, "description": "下次由你主动发起的比划必胜"},
            8: {"name": "负重沙袋", "price": 100,
                "description": "一个可以使用24h，能给牛牛增加负重的道具，期间锻炼效率翻倍"},
            9: {"name": "会跳的蛋", "price": 100,
                "description": "一个可以使用24h，能给猫猫增加负担的道具，期间锻炼效率翻倍"},
            10: {"name": "性转针筒", "price": 100,
                 "description": "一针下去24h内牛牛将暂时缩腹为猫，期间打工金币翻倍，再次使用将变回牛牛"},
            11: {"name": "牛牛转换器", "price": 500,
                 "description": "可以交换评分和自己相差不超过20%的目标用户的牛牛属性"},
            12: {"name": "猫猫转换器", "price": 500,
                 "description": "可以交换评分和自己相差不超过20%的目标用户的猫猫属性"},
            13: {"name": "春风精灵", "price": 50,
                 "description": "1小时内每次冷却完毕自动打胶/自摸，输入“/春风精灵提醒 开/关”设置是否提醒"},
            14: {"name": "牛牛盲盒", "price": 150, "description": "随机获得一件商品或金币奖励"},
            15: {"name": "牛牛寄生虫", "price": 200, "description": "24小时内目标用户牛牛增长的长度会被你窃取，对方寄生虫越多窃取越少"},
            16: {"name": "改名卡", "price": 50, "description": "修改牛牛的名字，名字需要在5个字以内"},
            17: {"name": "商店8折优惠券", "price": 100, "description": "使用后接下来5分钟商店所有商品将对你打8折"},
            18: {"name": "杀虫剂", "price": 50, "description": "使用后去掉一只牛牛寄生虫"},
        }

    def get_items(self, user_id) -> str:
        """获取所有商品的打印信息"""
        text = "🏬 牛牛商城 🏪\n"
        for key, value in self.items.items():
            text += f"🛒 {key}. {value['name']} 💰️ {value['price']}\n"
            text += f"     {value['description']}\n"
        money = self.data_manager.get_user_data(user_id)['coins']
        text += f'👛 持有金币：{money}\n'
        text += '发送“/购买 编号 数量”购买对应道具，不填数量将默认买1个'
        return text

    def purchase(self, user_id, item_id, num) -> str:
        if item_id > len(self.items) or item_id < 1:
            return f'✅ 商品编号错误，编号范围在1~{len(self.items)}'

        user_data = self.data_manager.get_user_data(user_id)
        user_money = user_data['coins']
        need_money = self.items[item_id]['price'] * num
        if user_money < need_money:

            return f'❌ 当前持有金币：{user_money}，需要{need_money}金币才能购买{num}个{self.items[item_id]["name"]}'

        user_data['coins'] -= num * self.items[item_id]['price']
        user_data['items_num'][self.items[item_id]['name']] += num
        now_money = user_data['coins']
        self.data_manager.save_user_data(user_id,user_data)
        return f'✅ 成功消耗{need_money}金币购买{num}个{self.items[item_id]["name"]}\n👛 剩余金币：{now_money}'

    def use_rename_card(self, user_id,name:str,config:dict) -> str:
        # 名称长度判断
        if len(name) > self.max_len:
            return f"❌ 名称需要在{self.max_len}个字之内"
        user_data = self.data_manager.get_user_data(user_id)
        # 改名卡判断
        if user_data['items_num']['改名卡'] < 1:
            return "❌ 改名需要改名卡，可以在牛牛商城购买"
        # 敏感词判断
        for item in config['disabled_name']:
            if item in name:
                return "😊 这个名字不文明哦~换一个吧"
        # 成功使用
        if self.data_manager.set_niuniu_name(user_id, name):
            # 更新一下修改名字后的data
            user_data = self.data_manager.get_user_data(user_id)
            user_data['items_num']['改名卡'] -= 1
            self.data_manager.save_user_data(user_id,user_data)
            return f"✅ 成功消耗改名卡，将牛牛改名为 {name}"
        else:
            return f"❌ 你的牛牛名称已是 {name}"