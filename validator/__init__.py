"""
validator 包：RLVR 任务的奖励引擎

提供多维度的稠密奖励计算，支持智能体部分正确时获得部分分数。
"""

from validator.reward_engine import RewardEngine, evaluate

__all__ = ["RewardEngine", "evaluate"]