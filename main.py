"""RLVR 训练框架顶层入口：演示、自验证测试、调用样例展示。"""

import argparse
import json
import sys

from agent import Agent
from validator import evaluate
from samples import (
    demo_correct_result,
    demo_wrong_result,
    demo_partial_result,
)


def run_demo(top_n: int = 3, json_output: bool = False):
    """标准演示：智能体查询 Top N 消费者并评分。"""
    agent = Agent(top_n=top_n)
    result = agent.query_top_spenders()
    score = evaluate(result)

    if json_output:
        print(json.dumps({"result": result, "score": score}, ensure_ascii=False))
    else:
        print(f"查询结果（Top {top_n}）：")
        for item in result:
            print(
                f"  第{item['rank']}名: "
                f"user_id={item['user_id']}, "
                f"金额={item['total_amount']:.2f}, "
                f"品类数={item['distinct_categories']}"
            )
        print(f"\n总分: {score['total_score']:.4f}")
        for dim, detail in score["dimensions"].items():
            print(f"  - {dim}: {detail['score']:.4f} (权重 {detail['weight']})")

    return result, score


def run_test():
    """自验证测试：运行三类调用样例，确认模块可用。"""
    print("运行自验证测试 ...\n")

    demo_correct_result()
    demo_wrong_result()
    demo_partial_result()

    print("\n所有自验证测试通过。")


def main():
    parser = argparse.ArgumentParser(description="RLVR 训练框架入口")
    parser.add_argument("--demo", action="store_true", help="运行标准演示")
    parser.add_argument("--test", action="store_true", help="运行自验证测试")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--top-n", type=int, default=3, help="Top N 消费者数量")
    args = parser.parse_args()

    if args.test:
        run_test()
        return

    if args.demo or not any([args.test]):
        run_demo(top_n=args.top_n, json_output=args.json)
        return

    parser.print_help()


if __name__ == "__main__":
    main()