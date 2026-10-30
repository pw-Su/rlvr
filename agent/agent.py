"""
智能体模块：封装环境 API 调用逻辑

Agent 类负责与 env/api.py 中的接口交互，完成 Top N 消费者查询任务。
"""

import json
from typing import Any

from env.api import dispatch


class Agent:
    """智能体：封装 API 调用逻辑，完成 Top N 消费者查询任务。"""

    def __init__(self, top_n: int = 3):
        """
        初始化智能体。

        Args:
            top_n: 查询前 N 名消费者，默认 3。
        """
        self.top_n = top_n

    def query_top_spenders(self) -> list[dict[str, Any]]:
        """
        查询最近 N 天消费总额最高的前 K 名用户。

        调用流程：
        1. 调用 /users/top_spenders 获取用户 ID 和总金额
        2. 对每个用户调用 /users/{user_id}/categories 获取品类数
        3. 组装结构化结果并返回

        Returns:
            包含用户 ID、总金额、品类数、排名的字典列表，按排名升序排列。
        """
        # 第 1 步：获取 Top N 用户列表（含用户 ID 和总金额）
        top_users = self._call_api("/users/top_spenders", {"top_n": self.top_n})

        results = []
        for rank, user_info in enumerate(top_users, start=1):
            user_id = user_info["user_id"]
            total_amount = user_info["total_amount"]

            # 第 2 步：获取该用户的品类数量
            category_info = self._call_api(
                f"/users/{user_id}/categories", {"user_id": user_id}
            )
            distinct_categories = category_info["distinct_categories"]

            # 第 3 步：组装结果
            results.append({
                "rank": rank,
                "user_id": user_id,
                "total_amount": total_amount,
                "distinct_categories": distinct_categories,
            })

        return results

    def _call_api(self, path: str, params: dict[str, Any]) -> Any:
        """
        调用环境 API。

        Args:
            path: API 路径，如 "/users/top_spenders"。
            params: 查询参数字典。

        Returns:
            API 返回的解析后数据。

        Raises:
            RuntimeError: 当 API 返回错误时抛出异常。
        """
        response = dispatch(path, params)

        # 解析响应
        if isinstance(response, str):
            try:
                data = json.loads(response)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"API 响应解析失败: {e}")
        else:
            data = response

        # 检查错误
        if isinstance(data, dict) and data.get("error"):
            raise RuntimeError(f"API 错误: {data['error']}")

        return data

    def __repr__(self) -> str:
        return f"Agent(top_n={self.top_n})"