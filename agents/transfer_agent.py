"""
Transfer Agent
Scans the multi-store retail network to identify opportunities for inter-store stock
transfers. Matches donor stores (with perishable excess at risk of spoilage) to
recipient stores (with impending stockouts or high sales velocity).
Ensures logistics feasibility and positive net economic value.
"""

import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

class TransferAgent:
    def __init__(self, freshness_agent=None, stock_agent=None, demand_forecaster=None):
        self.freshness_agent = freshness_agent
        self.stock_agent = stock_agent
        self.demand_forecaster = demand_forecaster

    def evaluate_transfers(self, source_store_id: str, sku_id: str):
        df_stores = pd.read_csv(os.path.join(DATA_DIR, "stores.csv"))
        df_dist = pd.read_csv(os.path.join(DATA_DIR, "store_distances.csv"))
        df_prod = pd.read_csv(os.path.join(DATA_DIR, "products.csv"))

        prod_row = df_prod[df_prod["sku_id"] == sku_id]
        if prod_row.empty:
            raise ValueError(f"SKU {sku_id} not found")

        prod_meta = prod_row.iloc[0].to_dict()
        unit_cost = float(prod_meta["unit_cost"])
        retail_price = float(prod_meta["retail_price"])

        # Check source store status
        source_freshness = None
        source_stock = None
        if self.freshness_agent:
            source_freshness = self.freshness_agent.assess_freshness(source_store_id, sku_id)
        if self.stock_agent:
            source_stock = self.stock_agent.assess_stock(source_store_id, sku_id)

        units_at_risk = source_freshness.get("units_at_risk", 0) if source_freshness else 0
        source_on_hand = source_stock.get("current_on_hand", 0) if source_stock else 0
        days_left = source_freshness.get("days_to_earliest_expiry", 99) if source_freshness else 99

        # Need units at risk or excess stock to justify sending stock out
        if units_at_risk <= 3 and source_stock.get("status") != "EXCESS_STOCK":
            return {
                "recommend_transfer": False,
                "source_store_id": source_store_id,
                "sku_id": sku_id,
                "product_name": prod_meta["name"],
                "reason": "No critical surplus or spoilage risk at this store to warrant transfer outward.",
            }

        # Transferable quantity: up to units at risk, keeping safety stock
        safety_stock = int(prod_meta["safety_stock"])
        max_can_send = max(0, source_on_hand - safety_stock)
        transferable_qty = min(units_at_risk, max_can_send)

        if transferable_qty <= 3:
            return {
                "recommend_transfer": False,
                "source_store_id": source_store_id,
                "sku_id": sku_id,
                "product_name": prod_meta["name"],
                "reason": "Available surplus quantity too small to offset transfer logistics cost.",
            }

        # Look for neighboring stores
        other_stores = df_stores[df_stores["store_id"] != source_store_id]
        transfer_candidates = []

        for _, target in other_stores.iterrows():
            target_id = target["store_id"]
            
            # Lookup distance and transit fee
            dist_match = df_dist[(df_dist["from_store"] == source_store_id) & (df_dist["to_store"] == target_id)]
            if dist_match.empty:
                continue

            dist_info = dist_match.iloc[0]
            transit_fee = float(dist_info["transfer_fee"])
            transit_hours = float(dist_info["transit_hours"])

            # Evaluate recipient store inventory & demand
            recip_stock = None
            if self.stock_agent:
                recip_stock = self.stock_agent.assess_stock(target_id, sku_id)

            recip_on_hand = recip_stock.get("current_on_hand", 0) if recip_stock else 0
            recip_status = recip_stock.get("status", "HEALTHY") if recip_stock else "HEALTHY"
            recip_demand = recip_stock.get("daily_demand", prod_meta["base_daily_demand"]) if recip_stock else prod_meta["base_daily_demand"]

            # Feasibility: Can recipient store sell the transferred units before expiry?
            # Remaining days after transit
            remaining_shelf_at_target = max(1.0, float(days_left) - (transit_hours / 24.0))
            recipient_absorb_capacity = round(recip_demand * remaining_shelf_at_target)
            recipient_deficit = max(0, int(round((recip_stock.get("reorder_point", 20) if recip_stock else 20) - recip_on_hand)))

            # If recipient is facing stockout or has strong absorption capacity
            if recip_status in ("CRITICAL_STOCKOUT", "BELOW_SAFETY_STOCK") or recipient_absorb_capacity >= transferable_qty:
                transfer_qty = min(transferable_qty, max(recipient_deficit, int(recipient_absorb_capacity)))
                
                if transfer_qty >= 5:
                    # Economics
                    waste_avoided_value = transfer_qty * unit_cost
                    sales_recovered_value = transfer_qty * (retail_price - unit_cost)
                    gross_benefit = waste_avoided_value + sales_recovered_value
                    net_benefit = round(gross_benefit - transit_fee, 2)

                    if net_benefit > 15.0:  # Only if meaningfully profitable
                        transfer_candidates.append({
                            "target_store_id": target_id,
                            "target_store_name": target["store_name"],
                            "target_location": target["location"],
                            "recommended_qty": transfer_qty,
                            "transit_hours": transit_hours,
                            "transfer_fee": transit_fee,
                            "recipient_stockout_status": recip_status,
                            "recipient_on_hand": recip_on_hand,
                            "waste_avoided_value": round(waste_avoided_value, 2),
                            "net_benefit": net_benefit,
                            "confidence": 0.88 if recip_status == "CRITICAL_STOCKOUT" else 0.80,
                        })

        if not transfer_candidates:
            return {
                "recommend_transfer": False,
                "source_store_id": source_store_id,
                "sku_id": sku_id,
                "product_name": prod_meta["name"],
                "reason": "No neighboring stores currently have enough deficit or velocity to absorb transferred units before expiry.",
            }

        # Pick candidate with highest net benefit
        best_candidate = max(transfer_candidates, key=lambda c: c["net_benefit"])

        timing = "Dispatch today by 11:30 AM via regional refrigerated shuttle"

        return {
            "recommend_transfer": True,
            "source_store_id": source_store_id,
            "target_store_id": best_candidate["target_store_id"],
            "target_store_name": best_candidate["target_store_name"],
            "sku_id": sku_id,
            "product_name": prod_meta["name"],
            "quantity": best_candidate["recommended_qty"],
            "timing": timing,
            "transit_hours": best_candidate["transit_hours"],
            "transfer_fee": best_candidate["transfer_fee"],
            "net_benefit": best_candidate["net_benefit"],
            "confidence_score": best_candidate["confidence"],
            "recipient_status": best_candidate["recipient_stockout_status"],
            "reason": (
                f"Transfer {best_candidate['recommended_qty']} units to {best_candidate['target_store_name']} ({best_candidate['target_store_id']}). "
                f"Recipient is facing {best_candidate['recipient_stockout_status']} (only {best_candidate['recipient_on_hand']} on hand). "
                f"Saves ${best_candidate['waste_avoided_value']} in disposal loss and delivers ${best_candidate['net_benefit']} net network gain after logistics fee."
            ),
        }

if __name__ == "__main__":
    from demand_forecaster import DemandForecasterAgent
    from freshness_agent import FreshnessAgent
    from stock_agent import StockAgent

    fc = DemandForecasterAgent()
    fa = FreshnessAgent(demand_forecaster=fc)
    sa = StockAgent(demand_forecaster=fc)
    agent = TransferAgent(freshness_agent=fa, stock_agent=sa, demand_forecaster=fc)
    res = agent.evaluate_transfers("STORE_001", "SKU_BERRIES_250G")
    print("Transfer result:", res)
