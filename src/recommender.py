import logging
import os

import pandas as pd
from mlxtend.frequent_patterns import fpgrowth, association_rules

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUGMENTED_DATA_PATH = os.path.join(BASE_DIR, "Data", "DecoMate_Master_Augmented.csv")


def build_association_rules(
    min_support: float = 0.0001,
    min_confidence: float = 0.5,
) -> pd.DataFrame:
    """
    Build association rules using FP-Growth (faster than Apriori at scale).

    Production targets: min_support > 0.01, min_confidence > 0.70, lift > 1.
    Demo uses permissive thresholds because the dataset is small and synthetic.
    """
    if not os.path.exists(AUGMENTED_DATA_PATH):
        logger.error("Dataset not found: %s", AUGMENTED_DATA_PATH)
        return pd.DataFrame()

    try:
        df = pd.read_csv(AUGMENTED_DATA_PATH)

        unique_orders = df["OrderID"].nunique()
        multi_item_orders = (df.groupby("OrderID").size() > 1).sum()
        logger.info(
            "Orders: %d total, %d with 2+ items", unique_orders, multi_item_orders
        )

        if multi_item_orders < 5:
            logger.warning("Not enough multi-item orders for meaningful rules")
            return pd.DataFrame()

        basket = (
            df.groupby(["OrderID", "name"])
            .size()
            .unstack(fill_value=0)
            .clip(upper=1)   # binary encoding
            .astype(bool)
        )

        frequent_itemsets = fpgrowth(
            basket, min_support=min_support, use_colnames=True
        )

        if frequent_itemsets.empty:
            logger.warning("No frequent itemsets found at min_support=%.4f", min_support)
            return pd.DataFrame()

        rules = association_rules(
            frequent_itemsets, metric="confidence", min_threshold=min_confidence
        )
        rules = rules[rules["lift"] > 0.5].sort_values("confidence", ascending=False)

        logger.info("Rules built: %d (FP-Growth)", len(rules))
        return rules

    except Exception as e:
        logger.error("Recommender error: %s", e)
        return pd.DataFrame()


def get_recommendations(
    product_name: str, rules_df: pd.DataFrame, top_n: int = 3
) -> list[dict]:
    if rules_df.empty:
        return []

    target = product_name.lower()
    recommendations = []
    seen = set()

    for _, row in rules_df.iterrows():
        antecedents = list(row["antecedents"])
        if any(target in str(item).lower() for item in antecedents):
            consequent = list(row["consequents"])[0]
            if consequent not in seen:
                seen.add(consequent)
                recommendations.append({
                    "product": consequent,
                    "confidence": f"{row['confidence'] * 100:.1f}%",
                    "lift": round(float(row["lift"]), 2),
                    "reason": "Comprado frecuentemente junto",
                })
            if len(recommendations) >= top_n:
                break

    return recommendations


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate_recommender(
    rules_df: pd.DataFrame,
    k: int = 3,
    test_fraction: float = 0.2,
) -> dict:
    """
    Temporal train/test split evaluation of association rules.

    Strategy: sort orders by date, hold out the last `test_fraction` as test set.
    For each multi-item test order, hide one item and check if the rules
    predict it from the remaining items.

    Returns Precision@K and Hit Rate@K.
    """
    if rules_df.empty:
        return {"error": "No rules to evaluate"}

    if not os.path.exists(AUGMENTED_DATA_PATH):
        return {"error": "Dataset not found"}

    df = pd.read_csv(AUGMENTED_DATA_PATH)

    # Temporal split
    if "OrderDate" in df.columns:
        df["OrderDate"] = pd.to_datetime(df["OrderDate"], errors="coerce")
        df = df.sort_values("OrderDate")

    order_ids = df["OrderID"].unique()
    split = int(len(order_ids) * (1 - test_fraction))
    test_order_ids = set(order_ids[split:])
    test_df = df[df["OrderID"].isin(test_order_ids)]

    hits = 0
    precision_sum = 0.0
    evaluated = 0

    for order_id, group in test_df.groupby("OrderID"):
        items = list(group["name"].unique())
        if len(items) < 2:
            continue

        # Hide one item, try to predict it from the rest
        for i, hidden_item in enumerate(items):
            known_items = [it for j, it in enumerate(items) if j != i]
            predicted = set()
            for known in known_items:
                recs = get_recommendations(known, rules_df, top_n=k)
                predicted.update(r["product"] for r in recs)
                if len(predicted) >= k:
                    break

            top_k_predicted = list(predicted)[:k]
            hit = hidden_item in top_k_predicted
            precision = (1 / len(top_k_predicted)) if hit and top_k_predicted else 0.0

            hits += int(hit)
            precision_sum += precision
            evaluated += 1

    if evaluated == 0:
        return {"error": "No multi-item orders in test set"}

    return {
        "evaluated_orders": evaluated,
        "hit_rate_at_k": round(hits / evaluated, 4),
        "precision_at_k": round(precision_sum / evaluated, 4),
        "k": k,
        "test_fraction": test_fraction,
    }
