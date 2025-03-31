import json
import random
import time
from datetime import datetime


def random_normal_distribution_int(a, b, n=15):
    """
    在区间 [a, b) 内生成近似正态分布的随机整数。
    通过取 n 个均匀分布随机数的平均值实现中心极限定理。
    :param a: 最小值（包含）
    :param b: 最大值（不包含）
    :param n: 采样数量（值越大分布越集中）
    :return: 符合近似正态分布的整数
    """
    if a >= b:
        return b
    # 生成 n 个均匀分布的随机数并计算均值
    samples = [random.randint(a, b - 1) for _ in range(n)]
    mean = sum(samples) / n
    # 四舍五入返回整数
    return round(mean)


def format_length(length: str) -> str:
    """格式化长度输出"""
    try:
        length = int(length)
    except Exception as e:
        print(f"转换长度出错：{e}")
        return length
    if length < 100:
        return f"{length}cm"
    elif length < 1000:
        return f"{round(length / 100, 2)}m"
    else:
        return f"{round(length / 1000, 2)}km"


def is_super_user(user_id: str) -> bool:
    """检查是否为超级用户"""
    try:
        with open("data/cmd_config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        if user_id in config.get("admins_id", []):
            return True
        else:
            return False
    except Exception as e:
        print(f"获取cmd_config.json出错：{e}")
        return False


def probabilistic_decision(probability: float) -> bool:
    """
    根据传入的概率返回 True 或 False。

    Args:
        probability (float): 返回 True 的概率，范围 [0.0, 1.0]

    Returns:
        bool: 以 probability 的概率返回 True，否则返回 False
    """
    if not 0.0 <= probability <= 1.0:
        raise ValueError("概率必须在 0.0 到 1.0 之间")
    return random.random() < probability


def is_timestamp_today(timestamp: float) -> bool:
    """
    判断时间戳是否属于今天（本地时区）

    :param timestamp: Unix时间戳（秒）
    :return: bool
    """
    try:
        # 转换为本地时区日期
        dt = datetime.fromtimestamp(timestamp)
        today = datetime.now()

        # 比较年月日是否相同
        return (dt.year, dt.month, dt.day) == (today.year, today.month, today.day)
    except (TypeError, OverflowError, OSError):
        # 处理非法时间戳（如None、字符串、超出范围的值）
        print('处理时间戳失败')
        return False


def check_cooldown(start_timestamp: float, cd: float) -> tuple[bool, str]:
    """
    检查冷却时间是否结束
    :param start_timestamp: 开始时间戳(秒级，如 time.time() 的返回值)
    :param cd: 冷却时长(秒)
    :return: (是否结束, 剩余时间)
            结束返回 (True, 0.0)
            未结束返回 (False, 剩余秒数)
    """
    current_time = time.time()
    elapsed = current_time - start_timestamp
    remaining = cd - elapsed
    if remaining < 60:
        text = f"{int(remaining)}秒"
    else:
        mins, secs = divmod(int(remaining), 60)
        text = f"{mins:02d}分{secs:02d}秒"

    if remaining <= 0:
        return True, text
    else:
        return False, text  # 保留两位小数


def get_add_text(true_add, original_add, uer_niuniu_name, user_data) -> str:
    text = ''
    if true_add < original_add:
        text += f"📏 {uer_niuniu_name}的长度在被寄生虫蚕食后增加了{true_add}cm，当前长度：{format_length(user_data['length'])}\n"
        text += f'各寄生虫窃取到了{true_add}cm，回馈到主人的牛牛中\n'
    else:
        text += f"📏 {uer_niuniu_name}的长度增加{true_add}cm，当前长度：{format_length(user_data['length'])}\n"
    return text
