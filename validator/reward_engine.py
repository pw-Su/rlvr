"""
奖励引擎：多维度稠密奖励计算

设计原则：
1. 多维度评分：用户集合、消费金额、排名顺序、品类数量分别计分，加权求和。
2. 容差机制：金额允许 1% 相对误差，避免因浮点精度导致误判。
3. 部分正确也有分：智能体即使只答对部分维度，也能获得对应权重比例的分数。
4. 裁判特权：直接读取数据库计算 ground truth，不经过 API 层。
"""

from config.task_config import DB_PATH, RECENT_DAYS, TOP_N, REWARD_WEIGHTS
from env.database import get_connection
from datetime import datetime, timedelta


class RewardEngine:
    """奖励引擎：计算智能体输出与标准答案的多维度相似度得分。"""

    def __init__(
        self,
        recent_days: int = RECENT_DAYS,
        top_n: int = TOP_N,
        weights: dict[str, float] | None = None,
    ):
        self.recent_days = recent_days
        self.top_n = top_n
        self.weights = weights or REWARD_WEIGHTS

    # ==================== Ground Truth 计算 ====================

    def _compute_ground_truth(self) -> list[dict]:
        """
        直接读取数据库，计算标准答案：最近 N 天消费总额 Top N 的用户。

        Returns:
            按消费总额降序排列的用户列表，每个元素包含：
            {user_id, total_amount, distinct_categories, rank}
        """
        today = datetime.now().date()
        start_date = (today - timedelta(days=self.recent_days)).isoformat()
        end_date = today.isoformat()

        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT
                    o.user_id,
                    SUM(o.amount)          AS total_amount,
                    COUNT(DISTINCT p.category) AS distinct_categories
                FROM orders o
                JOIN products p ON o.product_id = p.product_id
                WHERE o.order_date >= ? AND o.order_date <= ?
                GROUP BY o.user_id
                ORDER BY total_amount DESC
                LIMIT ?
                """,
                (start_date, end_date, self.top_n),
            ).fetchall()

            return [
                {
                    "user_id": row["user_id"],
                    "total_amount": row["total_amount"],
                    "distinct_categories": row["distinct_categories"],
                    "rank": idx + 1,
                }
                for idx, row in enumerate(rows)
            ]
        finally:
            conn.close()

    # ==================== 各维度评分 ====================

    def _score_user_set(self, predicted: list[dict], ground_truth: list[dict]) -> float:
        """
        用户集合正确率：预测的 Top N 中有多少个用户 ID 出现在标准答案中。

        计算方式：Jaccard 相似度变体 = |预测 ∩ 标准| / |标准|
        满分 1.0 表示预测的用户集合完全覆盖标准答案。
        """
        gt_ids = {g["user_id"] for g in ground_truth}
        pred_ids = {p["user_id"] for p in predicted}
        if not gt_ids:
            return 1.0  # 标准答案为空时，预测也为空则满分
        intersection = gt_ids & pred_ids
        return len(intersection) / len(gt_ids)

    def _score_amount(self, predicted: list[dict], ground_truth: list[dict]) -> float:
        """
        消费金额准确度：对每个匹配的用户，计算金额相对误差，取平均。

        容差：允许 1% 相对误差（相对误差 ≤ 0.01 视为完全正确）。
        超出容差时，得分 = max(0, 1 - 相对误差)。
        """
        gt_map = {g["user_id"]: g["total_amount"] for g in ground_truth}
        if not gt_map:
            return 1.0

        scores = []
        for pred in predicted:
            uid = pred["user_id"]
            if uid not in gt_map:
                scores.append(0.0)  # 用户不在标准答案中，金额得 0 分
                continue
            gt_amount = gt_map[uid]
            pred_amount = pred.get("total_amount", 0.0)
            if gt_amount == 0:
                # 标准金额为 0 时，预测也为 0 才满分
                scores.append(1.0 if pred_amount == 0 else 0.0)
                continue
            relative_error = abs(pred_amount - gt_amount) / gt_amount
            if relative_error <= 0.01:
                scores.append(1.0)  # 在容差范围内，满分
            else:
                scores.append(max(0.0, 1.0 - relative_error))

        return sum(scores) / len(scores) if scores else 0.0

    def _score_ranking(self, predicted: list[dict], ground_truth: list[dict]) -> float:
        """
        排名顺序正确率：预测的排名与标准答案的排名有多少一致。

        计算方式：对每个预测用户，检查其在预测中的排名是否等于标准答案中的排名。
        如果用户不在标准答案中，该用户排名得 0 分。
        """
        gt_rank_map = {g["user_id"]: g["rank"] for g in ground_truth}
        if not predicted:
            return 0.0

        correct = 0
        for idx, pred in enumerate(predicted):
            uid = pred["user_id"]
            pred_rank = idx + 1
            gt_rank = gt_rank_map.get(uid)
            if gt_rank is not None and pred_rank == gt_rank:
                correct += 1

        return correct / len(predicted)

    def _score_category_count(
        self, predicted: list[dict], ground_truth: list[dict]
    ) -> float:
        """
        品类数量正确率：对每个匹配的用户，检查品类数是否正确。

        计算方式：对每个预测用户，若品类数与标准答案一致则得 1 分，否则 0 分。
        用户不在标准答案中则得 0 分。
        """
        gt_cat_map = {g["user_id"]: g["distinct_categories"] for g in ground_truth}
        if not predicted:
            return 0.0

        correct = 0
        for pred in predicted:
            uid = pred["user_id"]
            gt_cat = gt_cat_map.get(uid)
            pred_cat = pred.get("distinct_categories")
            if gt_cat is not None and pred_cat == gt_cat:
                correct += 1

        return correct / len(predicted)

    # ==================== 主入口 ====================

    def evaluate(self, predicted: list[dict]) -> dict:
        """
        评估智能体的预测结果，返回多维度得分。

        Args:
            predicted: 智能体输出的 Top N 用户列表，每个元素应包含：
                       {user_id, total_amount, distinct_categories}
                       按消费总额降序排列。

        Returns:
            {
                "total_score": 加权总分 (0.0 ~ 1.0),
                "user_set": 用户集合得分,
                "amount": 金额准确度得分,
                "ranking": 排名顺序得分,
                "category_count": 品类数量得分,
                "details": { ... }  # 各维度原始分值，便于调试
            }
        """
        ground_truth = self._compute_ground_truth()

        scores = {
            "user_set": self._score_user_set(predicted, ground_truth),
            "amount": self._score_amount(predicted, ground_truth),
            "ranking": self._score_ranking(predicted, ground_truth),
            "category_count": self._score_category_count(predicted, ground_truth),
        }

        # 加权求和
        total_score = sum(
            scores[k] * self.weights.get(k, 0.0) for k in scores
        )

        return {
            "total_score": round(total_score, 4),
            "user_set": round(scores["user_set"], 4),
            "amount": round(scores["amount"], 4),
            "ranking": round(scores["ranking"], 4),
            "category_count": round(scores["category_count"], 4),
            "details": scores,  # 未舍入的原始值，用于调试
        }


# ==================== 便捷函数 ====================

def evaluate(predicted: list[dict]) -> dict:
    """
    便捷函数：使用默认配置评估预测结果。

    Args:
        predicted: 智能体输出的 Top N 用户列表

    Returns:
        多维度得分字典
    """
    engine = RewardEngine()
    return engine.evaluate(predicted)