"""env/api.py：环境 API 调度层。"""

from env.database import query_top_spenders


ENV_REGISTRY = {
    "query_top_spenders": query_top_spenders,
}


def dispatch(action: str, **kwargs):
    """根据 action 分发到对应环境函数。

    当前支持：
    - "query_top_spenders"：查询 Top N 消费者。
    """
    if action not in ENV_REGISTRY:
        raise ValueError(f"未知环境动作: {action}")

    func = ENV_REGISTRY[action]
    return func(**kwargs)