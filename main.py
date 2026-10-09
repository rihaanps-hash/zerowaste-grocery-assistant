"""
ZeroWaste Grocery Assistant - FastAPI Backend Server
Hosts REST endpoints, Telegram Bot integration, AI orchestration,
and serves an interactive Store Manager Web Dashboard.
"""

import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from orchestrator import Orchestrator
from decision_logger import DecisionLogger
from evaluator import Evaluator
from query_parser import parse_manager_query
from telegram_bot import ZeroWasteGroceryBot

# App initialization
app = FastAPI(
    title="ZeroWaste Grocery Assistant API",
    description="Multi-Agent AI Platform for Perishable Grocery Inventory & Waste Reduction",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Core services singletons
orchestrator = Orchestrator()
logger = DecisionLogger()
evaluator = Evaluator(logger=logger)
telegram_bot = ZeroWasteGroceryBot()

# Request Models
class ChatRequest(BaseModel):
    message: str
    store_id: Optional[str] = "STORE_001"
    user_id: Optional[str] = "STORE_MGR_01"

class DecisionRequest(BaseModel):
    recommendation_id: str
    decision: str  # APPROVED, REJECTED, MODIFIED
    modification_notes: Optional[str] = ""
    manager_id: Optional[str] = "STORE_MGR_01"

class RecommendRequest(BaseModel):
    store_id: str
    sku_id: str

# -------------------------------------------------------------
# REST API Endpoints
# -------------------------------------------------------------

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ZeroWaste Grocery Assistant",
        "timestamp": datetime.now().isoformat(),
        "agents": ["DemandForecaster", "FreshnessAgent", "StockAgent", "MarkdownAgent", "TransferAgent"],
        "orchestrator_ready": True,
        "database": "SQLite (zerowaste.db)",
    }

@app.get("/api/inventory")
def get_inventory(store_id: Optional[str] = None):
    import pandas as pd
    df_inv = pd.read_csv(os.path.join(BASE_DIR, "data", "inventory.csv"))
    df_prod = pd.read_csv(os.path.join(BASE_DIR, "data", "products.csv"))
    merged = df_inv.merge(df_prod, on="sku_id", how="left")
    
    if store_id:
        merged = merged[merged["store_id"] == store_id]
        
    return merged.to_dict(orient="records")

@app.get("/api/stores")
def get_stores():
    import pandas as pd
    df_stores = pd.read_csv(os.path.join(BASE_DIR, "data", "stores.csv"))
    return df_stores.to_dict(orient="records")

@app.get("/api/products")
def get_products():
    import pandas as pd
    df_prod = pd.read_csv(os.path.join(BASE_DIR, "data", "products.csv"))
    return df_prod.to_dict(orient="records")

@app.post("/api/recommend")
def recommend_sku(req: RecommendRequest):
    try:
        rec = orchestrator.get_recommendation(req.store_id, req.sku_id)
        logger.log_recommendation(rec)
        return rec
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/audit")
def audit_store(store_id: str = "STORE_001"):
    try:
        audit = orchestrator.audit_store_waste_risks(store_id)
        for r in audit["recommendations"]:
            logger.log_recommendation(r)
        return audit
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/chat")
def handle_chat(req: ChatRequest):
    """
    Handles natural language queries from chat interfaces.
    """
    try:
        result = telegram_bot.process_incoming_text(
            text=req.message,
            user_id=req.user_id,
            store_id=req.store_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/decision")
def record_decision(req: DecisionRequest):
    try:
        res = logger.log_decision(
            rec_id=req.recommendation_id,
            decision=req.decision,
            notes=req.modification_notes,
            manager_id=req.manager_id,
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/decisions")
def get_decisions(limit: int = 20):
    return {
        "stats": logger.get_decision_stats(),
        "recent": logger.get_recent_decisions(limit=limit),
    }

@app.get("/api/evaluation")
def run_evaluation(days: int = 14):
    try:
        res = evaluator.run_simulation(days=days)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request):
    """
    Webhook endpoint for receiving Telegram updates in production.
    """
    try:
        data = await request.json()
        # Process message or callback query
        if "message" in data and "text" in data["message"]:
            text = data["message"]["text"]
            user = data["message"].get("from", {}).get("username", "telegram_user")
            res = telegram_bot.process_incoming_text(text, user_id=user)
            return {"status": "ok", "reply": res["text"]}
        elif "callback_query" in data:
            cb_data = data["callback_query"]["data"]
            user = data["callback_query"].get("from", {}).get("username", "telegram_user")
            res = telegram_bot.process_callback_query(cb_data, user_id=user)
            return {"status": "ok", "reply": res["text"]}
        return {"status": "ignored"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# -------------------------------------------------------------
# Web Interface Dashboard Route
# -------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def serve_dashboard():
    dashboard_html_path = os.path.join(TEMPLATES_DIR, "dashboard.html")
    if os.path.exists(dashboard_html_path):
        with open(dashboard_html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>ZeroWaste Grocery Assistant API is Running</h1><p>Visit /docs for API documentation.</p>")

if __name__ == "__main__":
    import uvicorn
    print("Starting ZeroWaste Grocery Assistant FastAPI server on http://127.0.0.1:8050 ...")
    uvicorn.run("main:app", host="127.0.0.1", port=8050, reload=False)
