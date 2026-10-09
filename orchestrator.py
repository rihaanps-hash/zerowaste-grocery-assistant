"""
Orchestration Layer
Coordinates outputs from the 5 AI agents (Demand Forecaster, Freshness, Stock,
Markdown, Transfer), resolves multi-objective business tradeoffs (waste minimization,
margin maximization, stockout avoidance), and synthesizes a single best recommendation.
Formats output into human-friendly text for Telegram Bot and web interfaces.
"""

import os
import uuid
from datetime import datetime
import pandas as pd

from agents.demand_forecaster import DemandForecasterAgent
from agents.freshness_agent import FreshnessAgent
from agents.stock_agent import StockAgent
from agents.markdown_agent import MarkdownAgent
from agents.transfer_agent import TransferAgent

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

class Orchestrator:
    def __init__(self):
        self.demand_agent = DemandForecasterAgent()
        self.freshness_agent = FreshnessAgent(demand_forecaster=self.demand_agent)
        self.stock_agent = StockAgent(demand_forecaster=self.demand_agent)
        self.markdown_agent = MarkdownAgent(freshness_agent=self.freshness_agent, demand_forecaster=self.demand_agent)
        self.transfer_agent = TransferAgent(freshness_agent=self.freshness_agent, stock_agent=self.stock_agent, demand_forecaster=self.demand_agent)

    def get_recommendation(self, store_id: str, sku_id: str) -> dict:
        """
        Orchestrates all agents for a specific store and SKU, executes business rules,
        and generates a single winning recommendation.
        """
        # 1. Run all agents
        forecast = self.demand_agent.forecast(store_id, sku_id, horizon_days=3)
        freshness = self.freshness_agent.assess_freshness(store_id, sku_id)
        stock = self.stock_agent.assess_stock(store_id, sku_id)
        markdown = self.markdown_agent.evaluate_markdown(store_id, sku_id, freshness_info=freshness)
        transfer = self.transfer_agent.evaluate_transfers(store_id, sku_id)

        # 2. Multi-Objective Business Arbitration
        rec_id = f"REC-{uuid.uuid4().hex[:8].upper()}"
        product_name = freshness.get("product_name") or stock.get("product_name")

        action = "MAINTAIN"
        timing = "Regular schedule"
        quantity_or_level = "Keep current stock"
        confidence = 0.90
        expected_effect = "Stock levels optimal; zero imminent waste or stockouts."
        rationale = "Healthy inventory balance."
        supporting_evidence = []

        # Evidence points
        daily_demand = forecast["average_daily_demand"]
        on_hand = stock["current_on_hand"]
        days_expiry = freshness.get("days_to_earliest_expiry", 99)
        units_at_risk = freshness.get("units_at_risk", 0)

        supporting_evidence.append(f"Current on-hand inventory: {on_hand} units across active batches.")
        supporting_evidence.append(f"ML 3-day forecasted demand: {daily_demand} units/day (R² = {forecast['model_r2']}).")
        if forecast["drivers"]:
            supporting_evidence.append(f"Demand drivers: {'; '.join(forecast['drivers'])}.")
        supporting_evidence.append(f"Earliest batch expiry: {days_expiry} day(s) remaining.")

        # Business Rule 1: Impending Stockout with fresh demand -> REORDER
        if stock["status"] in ("CRITICAL_STOCKOUT", "BELOW_SAFETY_STOCK"):
            action = "ORDER"
            timing = "Immediate (Submit before 4:00 PM supplier cutoff)"
            order_qty = stock["recommended_reorder_qty"]
            quantity_or_level = f"Reorder {order_qty} units"
            confidence = round(stock["stockout_risk"] * 0.95, 2)
            expected_effect = (
                f"Prevents complete stockout; avoids an estimated ${round(daily_demand * 3.49, 2)} in lost daily revenue "
                f"and restores safety stock to {stock['safety_stock']} units."
            )
            rationale = (
                f"Inventory ({on_hand} units) has breached safety threshold ({stock['safety_stock']} units). "
                f"With daily velocity of {daily_demand} units/day, stockout is projected within 24 hours."
            )

        # Business Rule 2: Perishable excess with cross-store deficit -> TRANSFER
        elif transfer.get("recommend_transfer") is True and transfer.get("net_benefit", 0) > 30.0:
            action = "TRANSFER"
            t_qty = transfer["quantity"]
            target_store = transfer["target_store_name"]
            quantity_or_level = f"Transfer {t_qty} units to {target_store}"
            timing = transfer["timing"]
            confidence = transfer["confidence_score"]
            expected_effect = (
                f"Eliminates {t_qty} units of imminent spoilage; preserves ${transfer['net_benefit']} net network margin "
                f"after ${transfer['transfer_fee']} delivery logistics."
            )
            rationale = transfer["reason"]
            supporting_evidence.append(
                f"Cross-network balance: {target_store} is facing {transfer['recipient_status']} and can sell transferred units before expiry."
            )

        # Business Rule 3: Spoilage risk unable to be transferred or high local surplus -> DISCOUNT
        elif markdown.get("recommend_discount") is True:
            action = "DISCOUNT"
            disc_pct = markdown["discount_pct"]
            new_price = markdown["new_price"]
            orig_price = markdown["original_price"]
            quantity_or_level = f"Apply {disc_pct}% Discount (Markdown to ${new_price})"
            timing = markdown["timing"]
            confidence = markdown["confidence_score"]
            expected_effect = (
                f"Accelerates sales velocity to rescue {markdown['expected_units_saved']} units from landfill; "
                f"yields +${markdown['margin_gain']} margin recovery vs zero-revenue spoilage."
            )
            rationale = markdown["reason"]
            supporting_evidence.append(
                f"Price elasticity multiplier will increase velocity by {disc_pct * 2}% before expiry."
            )

        # Business Rule 4: Excess stock without imminent spoilage -> HOLD / REDUCE FUTURE REORDER
        elif stock["status"] == "EXCESS_STOCK":
            action = "HOLD_REORDER"
            timing = "Next 5-7 days"
            quantity_or_level = "Pause replenishment orders"
            confidence = 0.88
            expected_effect = "Allows inventory buffer to absorb naturally without overstocking warehouse."
            rationale = f"DOI is {stock['days_of_inventory']} days (well above target). Ample freshness prevents waste."

        # Format human-friendly recommendation card
        formatted_message = self._format_chat_card(
            rec_id=rec_id,
            store_id=store_id,
            sku_name=product_name,
            sku_id=sku_id,
            action=action,
            timing=timing,
            quantity_or_level=quantity_or_level,
            confidence=confidence,
            expected_effect=expected_effect,
            rationale=rationale,
            supporting_evidence=supporting_evidence,
        )

        return {
            "recommendation_id": rec_id,
            "timestamp": datetime.now().isoformat(),
            "store_id": store_id,
            "sku_id": sku_id,
            "product_name": product_name,
            "action": action,
            "timing": timing,
            "quantity_or_level": quantity_or_level,
            "confidence_score": round(confidence * 100, 1),
            "expected_effect": expected_effect,
            "rationale": rationale,
            "supporting_evidence": supporting_evidence,
            "agent_details": {
                "forecast": forecast,
                "freshness": freshness,
                "stock": stock,
                "markdown": markdown,
                "transfer": transfer,
            },
            "formatted_message": formatted_message,
        }

    def audit_store_waste_risks(self, store_id: str) -> dict:
        """
        Scans all SKUs for the given store and generates a prioritized waste risk report.
        """
        df_prod = pd.read_csv(os.path.join(DATA_DIR, "products.csv"))
        recommendations = []

        for _, prod in df_prod.iterrows():
            rec = self.get_recommendation(store_id, prod["sku_id"])
            recommendations.append(rec)

        # Sort recommendations by risk priority: DISCOUNT / TRANSFER / ORDER first
        priority_map = {"DISCOUNT": 1, "TRANSFER": 2, "ORDER": 3, "HOLD_REORDER": 4, "MAINTAIN": 5}
        recommendations.sort(key=lambda r: (priority_map.get(r["action"], 99), -r["confidence_score"]))

        # Summary statistics
        total_skus = len(recommendations)
        action_required = sum(1 for r in recommendations if r["action"] in ("DISCOUNT", "TRANSFER", "ORDER"))
        waste_risks = [r for r in recommendations if r["action"] in ("DISCOUNT", "TRANSFER")]

        summary_lines = [
            f"🛒 *STORE AUDIT REPORT: {store_id}*",
            f"📅 Evaluated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"📊 Total Perishable SKUs Monitored: {total_skus}",
            f"⚠️ Items Requiring Action: {action_required}\n",
        ]

        if waste_risks:
            summary_lines.append("*🚨 Urgent Waste Prevention Opportunities:*")
            for w in waste_risks:
                summary_lines.append(
                    f"• *{w['product_name']}*: [{w['action']}] {w['quantity_or_level']} | Timing: {w['timing']}"
                )
        else:
            summary_lines.append("✅ *Zero critical waste risks detected! All inventories healthy.*")

        order_risks = [r for r in recommendations if r["action"] == "ORDER"]
        if order_risks:
            summary_lines.append("\n*📦 Replenishment Orders Needed:*")
            for o in order_risks:
                summary_lines.append(
                    f"• *{o['product_name']}*: {o['quantity_or_level']} ({o['timing']})"
                )

        summary_text = "\n".join(summary_lines)

        return {
            "store_id": store_id,
            "total_skus": total_skus,
            "action_required_count": action_required,
            "recommendations": recommendations,
            "summary_text": summary_text,
        }

    def _format_chat_card(self, rec_id, store_id, sku_name, sku_id, action, timing,
                          quantity_or_level, confidence, expected_effect, rationale, supporting_evidence) -> str:
        icon_map = {
            "ORDER": "📦",
            "DISCOUNT": "🏷️",
            "TRANSFER": "🚚",
            "HOLD_REORDER": "⏸️",
            "MAINTAIN": "✅",
        }
        icon = icon_map.get(action, "💡")

        evidence_str = "\n".join([f"  • {e}" for e in supporting_evidence])

        card = (
            f"{icon} *ZEROWASTE RECOMMENDATION: {sku_name}*\n"
            f"🆔 *Ref:* `{rec_id}` | *Store:* `{store_id}`\n\n"
            f"🎯 *Recommended Action:* *{action}*\n"
            f"🔢 *Target / Level:* {quantity_or_level}\n"
            f"⏰ *Timing:* {timing}\n"
            f"🎯 *Confidence Score:* {round(confidence * 100)}%\n\n"
            f"📈 *Expected Effect:*\n{expected_effect}\n\n"
            f"🔍 *Supporting Evidence:*\n{evidence_str}\n\n"
            f"📝 *AI Rationale:*\n{rationale}\n\n"
            f"👇 *Store Manager Action:* Reply *Approve*, *Reject*, or *Modify*."
        )
        return card

if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    orch = Orchestrator()
    print("Testing Milk:")
    print(orch.get_recommendation("STORE_001", "SKU_MILK_1L")["formatted_message"])
    print("\nTesting Bread:")
    print(orch.get_recommendation("STORE_001", "SKU_BREAD_WHEAT")["formatted_message"])
    print("\nTesting Berries:")
    print(orch.get_recommendation("STORE_001", "SKU_BERRIES_250G")["formatted_message"])
