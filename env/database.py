"""env/database.py：数据库访问层。"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "test.db")


def _ensure_db():
    """确保数据库文件存在并完成初始化。"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """
    )

    # 初始化用户数据
    users = [
        (1, "Alice"),
        (2, "Bob"),
        (3, "Charlie"),
        (4, "David"),
        (5, "Eve"),
    ]
    cursor.executemany("INSERT OR IGNORE INTO users VALUES (?, ?)", users)

    # 初始化订单数据
    orders = [
        (1, 1200.0, "electronics", "2026-10-20"),
        (1, 800.0, "clothing", "2026-10-22"),
        (1, 500.0, "food", "2026-10-25"),
        (2, 1500.0, "electronics", "2026-10-21"),
        (2, 900.0, "food", "2026-10-23"),
        (3, 1100.0, "clothing", "2026-10-19"),
        (3, 700.0, "food", "2026-10-24"),
        (3, 600.0, "electronics", "2026-10-26"),
        (4, 400.0, "food", "2026-10-25"),
        (5, 300.0, "clothing", "2026-10-26"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO orders (user_id, amount, category, created_at) VALUES (?, ?, ?, ?)",
        orders,
    )

    conn.commit()
    conn.close()


def _get_connection():
    _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def query_top_spenders(top_n: int = 3, recent_days: int = 7):
    """查询最近 recent_days 天内消费总额最高的 top_n 个用户。"""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            u.user_id,
            u.name,
            ROUND(SUM(o.amount), 2) AS total_amount,
            COUNT(DISTINCT o.category) AS distinct_categories
        FROM users u
        JOIN orders o ON u.user_id = o.user_id
        WHERE o.created_at >= date('now', ? || ' days')
        GROUP BY u.user_id, u.name
        ORDER BY total_amount DESC
        LIMIT ?
        """,
        (f"-{recent_days}", top_n),
    )

    rows = cursor.fetchall()
    conn.close()

    results = []
    for rank, row in enumerate(rows, start=1):
        results.append(
            {
                "rank": rank,
                "user_id": row["user_id"],
                "name": row["name"],
                "total_amount": row["total_amount"],
                "distinct_categories": row["distinct_categories"],
            }
        )

    return results