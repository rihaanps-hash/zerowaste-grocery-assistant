"""
Natural Language Query Parser
Extracts intents, entities (SKUs, stores, actions), and parameters
from freeform text messages typed by store managers.
"""

import re

# SKU Synonyms Map
SKU_MAPPINGS = {
    "milk": "SKU_MILK_1L",
    "whole milk": "SKU_MILK_1L",
    "dairy milk": "SKU_MILK_1L",
    "bread": "SKU_BREAD_WHEAT",
    "wheat bread": "SKU_BREAD_WHEAT",
    "artisan bread": "SKU_BREAD_WHEAT",
    "berries": "SKU_BERRIES_250G",
    "strawberry": "SKU_BERRIES_250G",
    "strawberries": "SKU_BERRIES_250G",
    "yogurt": "SKU_YOGURT_500G",
    "greek yogurt": "SKU_YOGURT_500G",
    "salad": "SKU_SALAD_BOWL",
    "salad bowl": "SKU_SALAD_BOWL",
    "organic salad": "SKU_SALAD_BOWL",
    "chicken": "SKU_CHICKEN_500G",
    "chicken breast": "SKU_CHICKEN_500G",
    "meat": "SKU_CHICKEN_500G",
}

STORE_MAPPINGS = {
    "store 1": "STORE_001",
    "store 001": "STORE_001",
    "store_001": "STORE_001",
    "downtown": "STORE_001",
    "store 2": "STORE_002",
    "store 002": "STORE_002",
    "store_002": "STORE_002",
    "suburban": "STORE_002",
    "store 3": "STORE_003",
    "store 003": "STORE_003",
    "store_003": "STORE_003",
    "uptown": "STORE_003",
}

def parse_manager_query(text: str, default_store_id: str = "STORE_001") -> dict:
    text_lower = text.lower().strip()

    # 1. Check for Planner decision (Approve / Reject / Modify)
    rec_match = re.search(r'(rec-[a-f0-9]{8})', text_lower, re.IGNORECASE)
    rec_id = rec_match.group(1).upper() if rec_match else None

    if any(text_lower.startswith(w) for w in ["approve", "approved", "/approve", "yes", "accept", "confirm"]):
        return {
            "intent": "DECISION",
            "decision": "APPROVED",
            "rec_id": rec_id,
            "notes": text,
        }
    elif any(text_lower.startswith(w) for w in ["reject", "rejected", "/reject", "no", "deny", "cancel"]):
        return {
            "intent": "DECISION",
            "decision": "REJECTED",
            "rec_id": rec_id,
            "notes": text,
        }
    elif any(text_lower.startswith(w) for w in ["modify", "modified", "/modify", "change", "edit"]):
        # Extract notes or custom quantity if mentioned
        return {
            "intent": "DECISION",
            "decision": "MODIFIED",
            "rec_id": rec_id,
            "notes": text,
        }

    # 2. Extract store
    detected_store = default_store_id
    for store_keyword, store_id in STORE_MAPPINGS.items():
        if store_keyword in text_lower:
            detected_store = store_id
            break

    # 3. Extract SKU
    detected_sku = None
    for sku_keyword, sku_id in SKU_MAPPINGS.items():
        if re.search(r'\b' + re.escape(sku_keyword) + r'\b', text_lower):
            detected_sku = sku_id
            break

    # 4. Extract Intent
    intent = "GENERAL"

    if any(k in text_lower for k in ["report", "metrics", "stats", "performance", "kpi", "graph", "chart", "eval"]):
        intent = "REPORT"
    elif any(k in text_lower for k in ["risk", "waste", "spoil", "expire", "audit", "this week"]):
        intent = "STORE_WASTE_AUDIT" if not detected_sku else "SKU_RECOMMENDATION"
    elif any(k in text_lower for k in ["order", "how much", "buy", "reorder", "purchase", "restock"]):
        intent = "SKU_RECOMMENDATION"
    elif any(k in text_lower for k in ["discount", "markdown", "price", "sale", "promo"]):
        intent = "SKU_RECOMMENDATION"
    elif any(k in text_lower for k in ["transfer", "move", "ship", "balance"]):
        intent = "SKU_RECOMMENDATION" if detected_sku else "TRANSFER_AUDIT"
    elif detected_sku:
        intent = "SKU_RECOMMENDATION"

    return {
        "intent": intent,
        "store_id": detected_store,
        "sku_id": detected_sku,
        "raw_text": text,
        "rec_id": rec_id,
    }

if __name__ == "__main__":
    test_queries = [
        "How much milk should I order today?",
        "Do I need to discount bread?",
        "Is my store at risk of waste this week?",
        "What should I transfer from downtown?",
        "Show evaluation report and graphs",
        "Approve REC-64E8AFA1",
        "Modify REC-48331795 change to 30 loaves",
    ]
    for q in test_queries:
        print(f"'{q}' ->", parse_manager_query(q))
