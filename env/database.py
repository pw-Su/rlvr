"""
数据库模块：负责 SQLite 数据库的创建、初始化和连接管理。

设计原则：
1. 自包含：调用 init_db() 即可完成建表 + 数据种子插入，无需外部文件。
2. 幂等性：多次调用不会重复插入数据。
3. 封闭世界：所有 ground truth 都从这份数据中推导，不依赖外部数据源。
"""

import os
import sqlite3
from datetime import datetime, timedelta

from config.task_config import DB_PATH, RECENT_DAYS, SEED_USERS, SEED_PRODUCTS, SEED_ORDERS


def get_connection() -> sqlite3.Connection:
    """获取数据库连接，确保目录存在并开启外键支持。"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row  # 支持按列名访问
    return conn


def _create_tables(conn: sqlite3.Connection) -> None:
    """创建三张核心表：users、products、orders。"""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id   INTEGER PRIMARY KEY,
            name      TEXT    NOT NULL,
            region    TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY,
            name       TEXT    NOT NULL,
            category   TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS orders (
            order_id   INTEGER PRIMARY KEY,
            user_id    INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            amount     REAL    NOT NULL,
            order_date TEXT    NOT NULL,
            FOREIGN KEY (user_id)    REFERENCES users(user_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );
    """)


def _seed_data(conn: sqlite3.Connection) -> None:
    """插入模拟数据种子。仅在表为空时执行，保证幂等性。"""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        return  # 已有数据，跳过

    # 插入用户
    conn.executemany(
        "INSERT INTO users (user_id, name, region) VALUES (?, ?, ?)",
        SEED_USERS,
    )

    # 插入商品
    conn.executemany(
        "INSERT INTO products (product_id, name, category) VALUES (?, ?, ?)",
        SEED_PRODUCTS,
    )

    # 插入订单（动态计算日期，确保"最近 N 天"的语义始终正确）
    today = datetime.now().date()
    orders_with_dates = []
    for order_id, user_id, product_id, amount, days_ago in SEED_ORDERS:
        order_date = (today - timedelta(days=days_ago)).isoformat()
        orders_with_dates.append((order_id, user_id, product_id, amount, order_date))

    conn.executemany(
        "INSERT INTO orders (order_id, user_id, product_id, amount, order_date) VALUES (?, ?, ?, ?, ?)",
        orders_with_dates,
    )
    conn.commit()


def init_db() -> None:
    """初始化数据库：建表 + 插入种子数据。可安全重复调用。"""
    conn = get_connection()
    try:
        _create_tables(conn)
        _seed_data(conn)
    finally:
        conn.close()