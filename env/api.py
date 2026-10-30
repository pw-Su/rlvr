"""
业务 API 模块：暴露环境接口供智能体调用。

核心约束：智能体不能直接访问数据库，只能通过本模块的函数获取信息。
这模拟了真实业务场景中"数据平台提供 API，分析师通过 API 获取数据"的模式。
"""

from datetime import datetime, timedelta

from config.task_config import RECENT_DAYS
from env.database import get_connection


def get_orders_in_range(start_date: str, end_date: str) -> list[dict]:
    """
    查询指定时间范围内的所有订单。

    Args:
        start_date: 起始日期，格式 YYYY-MM-DD
        end_date:   结束日期，格式 YYYY-MM-DD

    Returns:
        订单列表，每个订单为 dict：
        {order_id, user_id, product_id, amount, order_date}
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            SELECT order_id, user_id, product_id, amount, order_date
            FROM orders
            WHERE order_date >= ? AND order_date <= ?
            ORDER BY order_date DESC
            """,
            (start_date, end_date),
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_user_info(user_id: int) -> dict | None:
    """
    查询单个用户的基本信息。

    Args:
        user_id: 用户 ID

    Returns:
        {user_id, name, region}，用户不存在时返回 None
    """
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT user_id, name, region FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_product_category(product_id: int) -> str | None:
    """
    查询单个商品的品类。

    Args:
        product_id: 商品 ID

    Returns:
        品类名称，商品不存在时返回 None
    """
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT category FROM products WHERE product_id = ?",
            (product_id,),
        ).fetchone()
        return row["category"] if row else None
    finally:
        conn.close()


def get_user_spending_summary(user_id: int, days: int = RECENT_DAYS) -> dict | None:
    """
    快捷接口：直接返回某用户在最近 N 天的消费汇总。

    这是一个"捷径 API"——智能体可以选择自己调用 get_orders_in_range 逐条聚合，
    也可以直接调用此接口一步到位。两种路径都应得到相同结果，
    这模拟了真实业务中"原始数据接口"与"聚合报表接口"并存的情况。

    Args:
        user_id: 用户 ID
        days:    回溯天数，默认使用配置中的 RECENT_DAYS

    Returns:
        {user_id, total_amount, distinct_categories, order_count}，
        无订单时返回 None
    """
    today = datetime.now().date()
    start_date = (today - timedelta(days=days)).isoformat()
    end_date = today.isoformat()

    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT
                o.user_id,
                SUM(o.amount)          AS total_amount,
                COUNT(DISTINCT p.category) AS distinct_categories,
                COUNT(*)               AS order_count
            FROM orders o
            JOIN products p ON o.product_id = p.product_id
            WHERE o.user_id = ?
              AND o.order_date >= ?
              AND o.order_date <= ?
            GROUP BY o.user_id
            """,
            (user_id, start_date, end_date),
        ).fetchone()
        if row is None:
            return None
        return {
            "user_id": row["user_id"],
            "total_amount": row["total_amount"],
            "distinct_categories": row["distinct_categories"],
            "order_count": row["order_count"],
        }
    finally:
        conn.close()