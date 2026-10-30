"""
env 包:RLVR 任务的环境层

包含数据库初始化模块和业务 API 模块。
智能体只能通过 api.py 暴露的接口与环境交互，不能直接访问数据库。
"""

from env.database import init_db, get_connection
from env.api import (
    get_orders_in_range,
    get_user_info,
    get_product_category,
    get_user_spending_summary,
)

__all__ = [
    "init_db",
    "get_connection",
    "get_orders_in_range",
    "get_user_info",
    "get_product_category",
    "get_user_spending_summary",
]