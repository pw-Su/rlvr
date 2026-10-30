"""
config 包：RLVR 任务的全局配置中心

所有任务超参数、种子数据、路径常量统一定义在此，
实现"数据与逻辑分离"——业务代码只引用常量，不硬编码数值。
"""

from config.task_config import (
    # 任务超参数
    RECENT_DAYS,
    TOP_N,
    DB_PATH,
    # 奖励权重
    REWARD_WEIGHTS,
    # 种子数据
    SEED_USERS,
    SEED_PRODUCTS,
    SEED_ORDERS,
)

__all__ = [
    "RECENT_DAYS",
    "TOP_N",
    "DB_PATH",
    "REWARD_WEIGHTS",
    "SEED_USERS",
    "SEED_PRODUCTS",
    "SEED_ORDERS",
]