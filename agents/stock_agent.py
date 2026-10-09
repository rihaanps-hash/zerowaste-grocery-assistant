"""
Stock Agent
Monitors inventory levels, lead-time demand, and safety stock thresholds.
Detects impending stockouts or excess inventory buffers, and computes
exact replenishment quantities.
"""

import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

class StockAgent:
    def __init__(self, demand_forecaster=None):
        self.demand_forecaster = demand_forecaster

    def assess_stock(self, store_id: str, sku_id: str, lead_time_days: int = 1):
        df_inv = pd.read_csv(os.path.join(DATA_DIR, "inventory.csv"))
        df_prod = pd.read_csv(os.path.join(DATA_DIR, "products.csv"))

        prod_row = df_prod[df_prod["sku_id"] == sku_id]
        if prod_row.empty:
            raise ValueError(f"SKU {sku_id} not found in products catalog")

        prod_meta = prod_row.iloc[0].to_dict()
        safety_stock = int(prod_meta["safety_stock"])
        reorder_batch = int(prod_meta["reorder_batch_size"])
        base_demand = float(prod_meta["base_daily_demand"])

        # Current on hand
        batches = df_inv[(df_inv["store_id"] == store_id) & (df_inv["sku_id"] == sku_id)]
        current_on_hand = int(batches["quantity"].sum()) if not batches.empty else 0

        # Forecast daily demand
        daily_demand = base_demand
        if self.demand_forecaster:
            fc = self.demand_forecaster.forecast(store_id, sku_id, horizon_days=3)
            daily_demand = fc["average_daily_demand"]

        # Reorder Point (ROP) = (Demand * Lead Time) + Safety Stock
        lead_time_demand = daily_demand * lead_time_days
        reorder_point = round(lead_time_demand + safety_stock, 1)

        # Days of Inventory (DOI)
        doi = round(current_on_hand / daily_demand, 1) if daily_demand > 0 else 99.0

        # Determine stockout / excess status
        if current_on_hand < lead_time_demand:
            status = "CRITICAL_STOCKOUT"
            stockout_risk = 0.95
            urgency = "IMMEDIATE"
            recommended_reorder = max(reorder_batch, int(round(reorder_point + daily_demand * 2 - current_on_hand)))
        elif current_on_hand <= reorder_point:
            status = "BELOW_SAFETY_STOCK"
            stockout_risk = 0.70
            urgency = "HIGH"
            recommended_reorder = reorder_batch
        elif doi > (prod_meta["shelf_life_days"] * 1.5):
            status = "EXCESS_STOCK"
            stockout_risk = 0.05
            urgency = "NONE"
            recommended_reorder = 0
        else:
            status = "HEALTHY"
            stockout_risk = 0.15
            urgency = "NORMAL"
            recommended_reorder = 0

        summary = (
            f"On hand: {current_on_hand} units | Daily demand: {round(daily_demand, 1)} units | "
            f"DOI: {doi} days | Reorder Point: {reorder_point} units (Safety stock: {safety_stock}). "
            f"Status: {status}."
        )

        return {
            "store_id": store_id,
            "sku_id": sku_id,
            "product_name": prod_meta["name"],
            "current_on_hand": current_on_hand,
            "daily_demand": round(daily_demand, 1),
            "safety_stock": safety_stock,
            "reorder_point": reorder_point,
            "days_of_inventory": doi,
            "status": status,
            "stockout_risk": stockout_risk,
            "urgency": urgency,
            "recommended_reorder_qty": recommended_reorder,
            "reorder_batch_size": reorder_batch,
            "summary": summary,
        }

if __name__ == "__main__":
    from demand_forecaster import DemandForecasterAgent
    fc = DemandForecasterAgent()
    agent = StockAgent(demand_forecaster=fc)
    res = agent.assess_stock("STORE_001", "SKU_MILK_1L")
    print("Stock Agent result:", res)
