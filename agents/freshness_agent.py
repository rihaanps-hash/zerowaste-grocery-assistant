"""
Freshness Agent
Estimates remaining shelf life and spoilage risk for perishable batches.
Simulates FEFO (First-Expired-First-Out) sales velocity to calculate exact
units at risk of expiring before being sold, and assesses spoilage hazard.
"""

import os
from datetime import datetime
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

class FreshnessAgent:
    def __init__(self, demand_forecaster=None):
        self.demand_forecaster = demand_forecaster

    def assess_freshness(self, store_id: str, sku_id: str, as_of_date=None):
        """
        Calculates remaining shelf life, batch hazard, and spoilage risk.
        """
        if as_of_date is None:
            as_of_date = datetime.now().date()
        elif isinstance(as_of_date, str):
            as_of_date = datetime.strptime(as_of_date, "%Y-%m-%d").date()

        df_inv = pd.read_csv(os.path.join(DATA_DIR, "inventory.csv"))
        df_prod = pd.read_csv(os.path.join(DATA_DIR, "products.csv"))

        prod_row = df_prod[df_prod["sku_id"] == sku_id]
        if prod_row.empty:
            raise ValueError(f"SKU {sku_id} not found in product catalog")
        
        prod_meta = prod_row.iloc[0].to_dict()
        unit_cost = float(prod_meta["unit_cost"])
        retail_price = float(prod_meta["retail_price"])

        # Filter batches for this store and SKU
        batches = df_inv[(df_inv["store_id"] == store_id) & (df_inv["sku_id"] == sku_id)].copy()
        
        if batches.empty:
            return {
                "store_id": store_id,
                "sku_id": sku_id,
                "product_name": prod_meta["name"],
                "total_on_hand": 0,
                "batches": [],
                "units_at_risk": 0,
                "risk_level": "OUT_OF_STOCK",
                "days_to_earliest_expiry": 0,
                "estimated_waste_cost": 0.0,
                "spoilage_probability": 0.0,
                "summary": "No inventory on hand."
            }

        # Calculate days until expiry
        batch_details = []
        total_on_hand = 0
        earliest_expiry_days = 999

        for _, row in batches.iterrows():
            exp_date = datetime.strptime(row["expiry_date"], "%Y-%m-%d").date()
            days_left = max(0, (exp_date - as_of_date).days)
            qty = int(row["quantity"])
            total_on_hand += qty
            earliest_expiry_days = min(earliest_expiry_days, days_left)

            batch_details.append({
                "batch_id": row["batch_id"],
                "quantity": qty,
                "received_date": row["received_date"],
                "expiry_date": row["expiry_date"],
                "days_remaining": days_left,
            })

        # Sort batches FEFO (First-Expired-First-Out)
        batch_details.sort(key=lambda b: b["days_remaining"])

        # Estimate daily demand velocity
        daily_demand = prod_meta["base_daily_demand"]
        if self.demand_forecaster:
            fc = self.demand_forecaster.forecast(store_id, sku_id, horizon_days=max(3, earliest_expiry_days + 1), target_date=as_of_date)
            daily_demand = fc["average_daily_demand"]

        # Simulate FEFO consumption to find units that won't be sold before expiry
        # For each batch, expected sales by expiry date = days_remaining * daily_demand
        accumulated_stock = 0
        units_at_risk = 0

        for b in batch_details:
            days = b["days_remaining"]
            expected_consumption_by_expiry = max(1.0, days * daily_demand)
            accumulated_stock += b["quantity"]

            if accumulated_stock > expected_consumption_by_expiry:
                surplus = accumulated_stock - expected_consumption_by_expiry
                units_at_risk = max(units_at_risk, int(round(surplus)))

        # Calculate risk classification and spoilage probability
        if earliest_expiry_days <= 1 and units_at_risk > 5:
            risk_level = "CRITICAL"
            spoilage_prob = 0.92
        elif earliest_expiry_days <= 2 and units_at_risk > 0:
            risk_level = "HIGH"
            spoilage_prob = 0.78
        elif earliest_expiry_days <= 3 and units_at_risk > 0:
            risk_level = "MODERATE"
            spoilage_prob = 0.45
        else:
            risk_level = "LOW"
            spoilage_prob = 0.12

        estimated_waste_cost = round(units_at_risk * unit_cost, 2)
        potential_lost_revenue = round(units_at_risk * retail_price, 2)

        summary_text = (
            f"On-hand: {total_on_hand} units across {len(batch_details)} batch(es). "
            f"Earliest expiry in {earliest_expiry_days} day(s). "
            f"{units_at_risk} unit(s) projected to expire before selling at current sales velocity "
            f"(~{round(daily_demand, 1)} units/day)."
        )

        return {
            "store_id": store_id,
            "sku_id": sku_id,
            "product_name": prod_meta["name"],
            "category": prod_meta["category"],
            "total_on_hand": total_on_hand,
            "batches": batch_details,
            "days_to_earliest_expiry": earliest_expiry_days,
            "units_at_risk": units_at_risk,
            "risk_level": risk_level,
            "spoilage_probability": spoilage_prob,
            "estimated_waste_cost": estimated_waste_cost,
            "potential_lost_revenue": potential_lost_revenue,
            "daily_sales_velocity": round(daily_demand, 1),
            "summary": summary_text,
        }

if __name__ == "__main__":
    from demand_forecaster import DemandForecasterAgent
    fc = DemandForecasterAgent()
    agent = FreshnessAgent(demand_forecaster=fc)
    res = agent.assess_freshness("STORE_001", "SKU_BREAD_WHEAT")
    print("Freshness result:", res)
