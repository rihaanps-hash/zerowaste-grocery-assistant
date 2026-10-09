"""
Markdown Agent
Calculates price elasticity and evaluates markdown tiers (15%, 25%, 35%, 50%)
to accelerate sales velocity of perishable stock before expiry, maximizing margin
and preventing physical food waste.
"""

import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

class MarkdownAgent:
    def __init__(self, freshness_agent=None, demand_forecaster=None):
        self.freshness_agent = freshness_agent
        self.demand_forecaster = demand_forecaster

    def evaluate_markdown(self, store_id: str, sku_id: str, freshness_info=None):
        df_prod = pd.read_csv(os.path.join(DATA_DIR, "products.csv"))
        prod_row = df_prod[df_prod["sku_id"] == sku_id]
        if prod_row.empty:
            raise ValueError(f"SKU {sku_id} not found in products catalog")

        prod_meta = prod_row.iloc[0].to_dict()
        unit_cost = float(prod_meta["unit_cost"])
        retail_price = float(prod_meta["retail_price"])
        elasticity = float(prod_meta["price_elasticity"])

        if freshness_info is None:
            if self.freshness_agent:
                freshness_info = self.freshness_agent.assess_freshness(store_id, sku_id)
            else:
                return {"recommend_discount": False, "discount_pct": 0, "reason": "No freshness data"}

        units_at_risk = freshness_info.get("units_at_risk", 0)
        days_left = freshness_info.get("days_to_earliest_expiry", 99)
        total_on_hand = freshness_info.get("total_on_hand", 0)
        daily_demand = freshness_info.get("daily_sales_velocity", prod_meta["base_daily_demand"])

        # If zero units at risk or plenty of days left, no discount needed
        if units_at_risk == 0 or days_left >= 4:
            return {
                "store_id": store_id,
                "sku_id": sku_id,
                "product_name": prod_meta["name"],
                "recommend_discount": False,
                "discount_pct": 0,
                "timing": "None",
                "expected_units_saved": 0,
                "margin_gain": 0.0,
                "confidence_score": 0.95,
                "reason": f"Inventory is fresh (earliest expiry in {days_left} days). No markdown required.",
            }

        # Candidate markdown levels
        discount_tiers = [0.0, 0.15, 0.25, 0.35, 0.50]
        evaluations = []

        effective_days = max(1.0, float(days_left))

        for rate in discount_tiers:
            velocity_multiplier = 1.0 + (elasticity * rate)
            accelerated_sales = daily_demand * velocity_multiplier * effective_days
            units_sold = min(float(total_on_hand), accelerated_sales)
            units_wasted = max(0.0, total_on_hand - units_sold)

            disc_price = retail_price * (1.0 - rate)
            revenue = units_sold * disc_price
            cogs = units_sold * unit_cost
            waste_loss = units_wasted * unit_cost
            net_profit = revenue - cogs - waste_loss

            evaluations.append({
                "discount_pct": int(rate * 100),
                "discount_rate": rate,
                "discounted_price": round(disc_price, 2),
                "units_sold": round(units_sold, 1),
                "units_wasted": round(units_wasted, 1),
                "revenue": round(revenue, 2),
                "net_profit": round(net_profit, 2),
            })

        # Baseline is 0% discount
        baseline = evaluations[0]
        
        # Select best tier that maximizes net profit
        # If profit is close, prefer the one with fewer wasted units
        best_tier = max(evaluations, key=lambda x: (x["net_profit"], -x["units_wasted"]))

        if best_tier["discount_pct"] == 0 or best_tier["net_profit"] <= baseline["net_profit"]:
            # If even at discount we don't beat baseline, but units will spoil:
            # If critical expiry (1 day left) and waste is high, flash discount is always better than 100% loss
            if days_left <= 1 and units_at_risk > 0:
                best_tier = [e for e in evaluations if e["discount_pct"] == 35][0]
            else:
                return {
                    "store_id": store_id,
                    "sku_id": sku_id,
                    "product_name": prod_meta["name"],
                    "recommend_discount": False,
                    "discount_pct": 0,
                    "timing": "None",
                    "expected_units_saved": 0,
                    "margin_gain": 0.0,
                    "confidence_score": 0.85,
                    "reason": "Normal sales velocity will clear stock without margin-diluting discount.",
                }

        units_rescued = max(0, int(round(baseline["units_wasted"] - best_tier["units_wasted"])))
        profit_delta = round(best_tier["net_profit"] - baseline["net_profit"], 2)

        # Timing suggestion
        if days_left <= 1:
            timing = "Immediate (Today by 2:00 PM Flash Sale)"
        elif days_left == 2:
            timing = "Tomorrow Morning Opening (8:00 AM)"
        else:
            timing = "In 2 Days"

        confidence = 0.91 if days_left <= 2 else 0.82

        return {
            "store_id": store_id,
            "sku_id": sku_id,
            "product_name": prod_meta["name"],
            "recommend_discount": True,
            "discount_pct": best_tier["discount_pct"],
            "new_price": best_tier["discounted_price"],
            "original_price": retail_price,
            "timing": timing,
            "units_at_risk": units_at_risk,
            "expected_units_saved": units_rescued,
            "margin_gain": profit_delta,
            "projected_waste_units": best_tier["units_wasted"],
            "tier_evaluations": evaluations,
            "confidence_score": confidence,
            "reason": (
                f"Apply {best_tier['discount_pct']}% markdown (${best_tier['discounted_price']} vs ${retail_price}). "
                f"Boosts sales velocity by {round((1 + elasticity * best_tier['discount_rate'] - 1)*100)}% via price elasticity. "
                f"Rescues ~{units_rescued} units from disposal, improving net margin by ${profit_delta}."
            ),
        }

if __name__ == "__main__":
    from demand_forecaster import DemandForecasterAgent
    from freshness_agent import FreshnessAgent
    fc = DemandForecasterAgent()
    fa = FreshnessAgent(demand_forecaster=fc)
    agent = MarkdownAgent(freshness_agent=fa, demand_forecaster=fc)
    res = agent.evaluate_markdown("STORE_001", "SKU_BREAD_WHEAT")
    print("Markdown result:", res)
