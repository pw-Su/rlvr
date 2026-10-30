"""
调用样例：演示环境 API 和验证引擎的标准调用方式

覆盖场景：
1. 正确结果：智能体返回完全正确的 Top 3 消费者
2. 错误结果：智能体返回错误的用户 ID 和金额
"""

from agent import Agent
from validator import evaluate


def demo_correct_result():
    """场景 1：正确结果 —— 智能体返回完全正确的 Top 3 消费者"""
    print("=" * 60)
    print("场景 1：正确结果演示")
    print("=" * 60)

    # 创建智能体并执行查询
    agent = Agent(top_n=3)
    result = agent.query_top_spenders()

    # 打印智能体输出
    print("\n智能体输出：")
    for item in result:
        print(
            f"  第{item['rank']}名: "
            f"user_id={item['user_id']}, "
            f"金额={item['total_amount']:.2f}, "
            f"品类数={item['distinct_categories']}"
        )

    # 调用验证引擎评估
    score = evaluate(result)

    print(f"\n验证结果：")
    print(f"  总分: {score['total_score']:.4f}")
    print(f"  各维度得分:")
    for dim, detail in score["dimensions"].items():
        print(f"    - {dim}: {detail['score']:.4f} (权重 {detail['weight']})")

    assert score["total_score"] == 1.0, "正确结果应得满分"
    print("\n  ✓ 验证通过：智能体完全正确地完成了任务。")
    return result, score


def demo_wrong_result():
    """场景 2：错误结果 —— 智能体返回错误的用户 ID 和金额"""
    print("\n" + "=" * 60)
    print("场景 2：错误结果演示")
    print("=" * 60)

    # 构造一个完全错误的预测结果
    wrong_result = [
        {
            "rank": 1,
            "user_id": 999,  # 不存在的用户
            "total_amount": 10000.00,
            "distinct_categories": 5,
        },
        {
            "rank": 2,
            "user_id": 888,  # 不存在的用户
            "total_amount": 8000.00,
            "distinct_categories": 4,
        },
        {
            "rank": 3,
            "user_id": 777,  # 不存在的用户
            "total_amount": 6000.00,
            "distinct_categories": 3,
        },
    ]

    print("\n智能体输出（错误）：")
    for item in wrong_result:
        print(
            f"  第{item['rank']}名: "
            f"user_id={item['user_id']}, "
            f"金额={item['total_amount']:.2f}, "
            f"品类数={item['distinct_categories']}"
        )

    # 调用验证引擎评估
    score = evaluate(wrong_result)

    print(f"\n验证结果：")
    print(f"  总分: {score['total_score']:.4f}")
    print(f"  各维度得分:")
    for dim, detail in score["dimensions"].items():
        print(f"    - {dim}: {detail['score']:.4f} (权重 {detail['weight']})")

    assert score["total_score"] == 0.0, "完全错误的结果应得零分"
    print("\n  ✓ 验证通过：验证引擎正确识别了错误结果。")
    return wrong_result, score


def demo_partial_result():
    """场景 3：部分正确 —— 用户 ID 正确但金额有偏差"""
    print("\n" + "=" * 60)
    print("场景 3：部分正确演示")
    print("=" * 60)

    # 先获取正确答案作为参考
    agent = Agent(top_n=3)
    correct_result = agent.query_top_spenders()

    # 构造部分正确的结果：用户 ID 正确，但金额有偏差
    partial_result = []
    for item in correct_result:
        partial_result.append({
            "rank": item["rank"],
            "user_id": item["user_id"],
            "total_amount": item["total_amount"] * 1.05,  # 金额偏差 5%
            "distinct_categories": item["distinct_categories"],
        })

    print("\n智能体输出（部分正确）：")
    for item in partial_result:
        print(
            f"  第{item['rank']}名: "
            f"user_id={item['user_id']}, "
            f"金额={item['total_amount']:.2f}, "
            f"品类数={item['distinct_categories']}"
        )

    # 调用验证引擎评估
    score = evaluate(partial_result)

    print(f"\n验证结果：")
    print(f"  总分: {score['total_score']:.4f}")
    print(f"  各维度得分:")
    for dim, detail in score["dimensions"].items():
        print(f"    - {dim}: {detail['score']:.4f} (权重 {detail['weight']})")

    assert 0.0 < score["total_score"] < 1.0, "部分正确应得部分分数"
    print("\n  ✓ 验证通过：验证引擎正确识别了部分正确结果。")
    return partial_result, score


if __name__ == "__main__":
    # 运行所有演示场景
    demo_correct_result()
    demo_wrong_result()
    demo_partial_result()

    print("\n" + "=" * 60)
    print("所有调用样例演示完成！")
    print("=" * 60)