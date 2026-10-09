"""
ZeroWaste Grocery Assistant - Telegram Bot
Implements the interactive Telegram chat interface using python-telegram-bot (v20+),
supporting natural language queries, rich markdown cards with action buttons,
interactive inline approvals, and report graph delivery.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger("ZeroWasteBot")

from orchestrator import Orchestrator
from decision_logger import DecisionLogger
from evaluator import Evaluator
from query_parser import parse_manager_query

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "reports")

class ZeroWasteGroceryBot:
    def __init__(self, bot_token: str = None):
        # Check environment variable first
        self.bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN")
        
        # If not set, check .env file
        if not self.bot_token:
            for env_path in [
                os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
            ]:
                if os.path.exists(env_path):
                    with open(env_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("TELEGRAM_BOT_TOKEN="):
                                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                                if val:
                                    self.bot_token = val
                                    break
                if self.bot_token:
                    break

        self.orchestrator = Orchestrator()
        self.logger = DecisionLogger()
        self.evaluator = Evaluator(logger=self.logger)
        self.user_current_store = {}  # user_id -> store_id

    def process_incoming_text(self, text: str, user_id: str = "STORE_MGR_01", store_id: str = None) -> dict:
        """
        Processes a store manager's text message, executes multi-agent orchestration,
        and returns response text, inline buttons, and optional photo attachment.
        """
        current_store = store_id or self.user_current_store.get(user_id, "STORE_001")
        parsed = parse_manager_query(text, default_store_id=current_store)
        intent = parsed["intent"]

        # Case 1: Store Manager Decision (Approve / Reject / Modify)
        if intent == "DECISION":
            rec_id = parsed.get("rec_id")
            if not rec_id:
                # Retrieve latest recommendation for this store
                latest = self.logger.get_latest_recommendation_for_sku(current_store)
                if latest:
                    rec_id = latest["rec_id"]

            if not rec_id:
                return {
                    "text": "⚠️ No active recommendation reference found to act upon. Please request a recommendation first.",
                    "buttons": None,
                    "photo": None,
                }

            decision_res = self.logger.log_decision(
                rec_id=rec_id,
                decision=parsed["decision"],
                notes=parsed.get("notes", ""),
                manager_id=user_id,
            )

            icon = "✅" if decision_res["decision"] == "APPROVED" else ("❌" if decision_res["decision"] == "REJECTED" else "✏️")
            reply = (
                f"{icon} *DECISION RECORDED*\n\n"
                f"🆔 *Ref:* `{rec_id}`\n"
                f"👤 *Store Manager:* `{user_id}`\n"
                f"📋 *Action Decision:* *{decision_res['decision']}*\n"
                f"⚙️ *Applied Operation:* `{decision_res['applied_action']}`\n"
                f"🕒 *Timestamp:* {decision_res['timestamp'][:19].replace('T', ' ')}\n\n"
                f"_Logged into audit database for evaluation tracking._"
            )
            return {"text": reply, "buttons": None, "photo": None}

        # Case 2: Store Waste Audit ("Is my store at risk of waste this week?")
        if intent == "STORE_WASTE_AUDIT":
            target_store = parsed["store_id"]
            audit = self.orchestrator.audit_store_waste_risks(target_store)
            
            # Log any active recommendations
            for r in audit["recommendations"]:
                self.logger.log_recommendation(r)

            buttons = [
                [{"text": "🥛 Check Milk Stock", "callback_data": f"sku:SKU_MILK_1L:{target_store}"},
                 {"text": "🍞 Check Bread Markdown", "callback_data": f"sku:SKU_BREAD_WHEAT:{target_store}"}],
                [{"text": "🍓 Check Berries Transfer", "callback_data": f"sku:SKU_BERRIES_250G:{target_store}"},
                 {"text": "📊 View Evaluation Report", "callback_data": f"report:{target_store}"}]
            ]
            return {"text": audit["summary_text"], "buttons": buttons, "photo": None}

        # Case 3: Transfer Audit
        if intent == "TRANSFER_AUDIT":
            target_store = parsed["store_id"]
            berries_rec = self.orchestrator.get_recommendation(target_store, "SKU_BERRIES_250G")
            self.logger.log_recommendation(berries_rec)
            
            rec_id = berries_rec["recommendation_id"]
            buttons = [
                [{"text": "✅ Approve Transfer", "callback_data": f"dec:APPROVE:{rec_id}"},
                 {"text": "❌ Reject", "callback_data": f"dec:REJECT:{rec_id}"}],
                [{"text": "✏️ Modify Quantity", "callback_data": f"dec:MODIFY:{rec_id}"}]
            ]
            return {"text": berries_rec["formatted_message"], "buttons": buttons, "photo": None}

        # Case 4: Evaluation Report / Graphs
        if intent == "REPORT":
            sim = self.evaluator.run_simulation(days=14)
            reply = (
                f"📊 *ZEROWASTE PERFORMANCE REPORT*\n"
                f"🔬 *14-Day Simulation: Multi-Agent AI vs. Baseline Policy*\n\n"
                f"♻️ *Waste Reduction:* *{sim['waste_reduction_pct']}%* "
                f"({sim['waste_units_saved']} units / ${sim['waste_cost_saved']} saved)\n"
                f"📦 *Stockout Reduction:* *{sim['stockout_reduction_pct']}%* fewer stockout incidents\n"
                f"💰 *Net Margin Gain:* *+{sim['margin_improvement_pct']}%* (+${sim['net_margin_gain']} gross profit)\n\n"
                f"📉 *Waste by Category:* Produce: {sim['category_waste_ai'].get('Produce', 0)} vs {sim['category_waste_baseline'].get('Produce', 0)} units baseline\n"
                f"📈 *Total Revenue:* ${sim['ai_revenue']} (AI) vs ${sim['baseline_revenue']} (Baseline)"
            )
            chart_path = os.path.join(REPORTS_DIR, "executive_kpis.png")
            return {"text": reply, "buttons": None, "photo": chart_path if os.path.exists(chart_path) else None}

        # Case 5: SKU Recommendation ("How much milk should I order today?", "Do I need to discount bread?")
        sku_id = parsed["sku_id"] or "SKU_MILK_1L"
        target_store = parsed["store_id"]
        rec = self.orchestrator.get_recommendation(target_store, sku_id)
        rec_id = self.logger.log_recommendation(rec)

        buttons = [
            [{"text": f"✅ Approve {rec['action']}", "callback_data": f"dec:APPROVE:{rec_id}"},
             {"text": "❌ Reject", "callback_data": f"dec:REJECT:{rec_id}"}],
            [{"text": "✏️ Modify", "callback_data": f"dec:MODIFY:{rec_id}"},
             {"text": "🔄 Refresh Audit", "callback_data": f"audit:{target_store}"}]
        ]

        return {
            "text": rec["formatted_message"],
            "buttons": buttons,
            "photo": None,
            "recommendation": rec,
        }

    def process_callback_query(self, data: str, user_id: str = "STORE_MGR_01") -> dict:
        """
        Handles interactive inline button clicks from Telegram.
        Format: 'dec:APPROVE:REC-1234' or 'sku:SKU_MILK_1L:STORE_001' or 'report:STORE_001'
        """
        parts = data.split(":")
        prefix = parts[0]

        if prefix == "dec":
            decision = parts[1]
            rec_id = parts[2]
            decision_res = self.logger.log_decision(
                rec_id=rec_id,
                decision=decision,
                notes=f"Button click by {user_id}",
                manager_id=user_id,
            )
            icon = "✅" if decision == "APPROVE" else ("❌" if decision == "REJECT" else "✏️")
            return {
                "text": f"{icon} *Action {decision}D for {rec_id}!*\nLogged by {user_id} at {datetime.now().strftime('%H:%M:%S')}.",
                "alert": f"Decision {decision} saved successfully!",
            }

        elif prefix == "sku":
            sku_id = parts[1]
            store_id = parts[2]
            return self.process_incoming_text(f"Check {sku_id}", user_id=user_id, store_id=store_id)

        elif prefix == "audit":
            store_id = parts[1]
            return self.process_incoming_text("Is my store at risk of waste this week?", user_id=user_id, store_id=store_id)

        elif prefix == "report":
            return self.process_incoming_text("Show evaluation report", user_id=user_id)

        return {"text": "Unknown button action", "alert": None}

    # -------------------------------------------------------------
    # Live python-telegram-bot Integration
    # -------------------------------------------------------------
    def run_live_telegram_bot(self):
        """
        Starts live polling Telegram bot using python-telegram-bot.
        """
        if not self.bot_token or self.bot_token.startswith("YOUR_"):
            print("Telegram Bot Token is not configured. Run in interactive test mode or set TELEGRAM_BOT_TOKEN.")
            return

        from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

        async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
            welcome = (
                "👋 *Welcome to ZeroWaste Grocery Assistant!*\n\n"
                "I am your AI Perishable Inventory & Waste Reduction Partner.\n"
                "I coordinate 5 specialized AI agents to help you:\n"
                "• Forecast short-term customer demand with ML\n"
                "• Detect spoilage risk using batch shelf-life\n"
                "• Avoid stockouts with proactive safety stock\n"
                "• Rescue near-expiry food with price elasticity markdowns\n"
                "• Balance stock across stores with refrigerated transfers\n\n"
                "💬 *You can ask me questions like:*\n"
                "• _'How much milk should I order today?'_\n"
                "• _'Do I need to discount bread?'_\n"
                "• _'Is my store at risk of waste this week?'_\n"
                "• _'What should I transfer to other stores?'_\n\n"
                "Or tap a quick action below:"
            )
            keyboard = [
                [InlineKeyboardButton("🥛 Order Milk", callback_data="sku:SKU_MILK_1L:STORE_001"),
                 InlineKeyboardButton("🍞 Discount Bread", callback_data="sku:SKU_BREAD_WHEAT:STORE_001")],
                [InlineKeyboardButton("🍓 Transfer Berries", callback_data="sku:SKU_BERRIES_250G:STORE_001"),
                 InlineKeyboardButton("🚨 Waste Audit", callback_data="audit:STORE_001")],
                [InlineKeyboardButton("📊 14-Day AI vs Baseline Report", callback_data="report:STORE_001")],
            ]
            await update.message.reply_text(welcome, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

        async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_msg = update.message.text
            user_id = update.effective_user.username or str(update.effective_user.id)
            res = self.process_incoming_text(user_msg, user_id=user_id)

            reply_markup = None
            if res.get("buttons"):
                keyboard = [
                    [InlineKeyboardButton(btn["text"], callback_data=btn["callback_data"]) for btn in row]
                    for row in res["buttons"]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

            if res.get("photo") and os.path.exists(res["photo"]):
                with open(res["photo"], "rb") as f:
                    await update.message.reply_photo(photo=f, caption=res["text"], parse_mode="Markdown", reply_markup=reply_markup)
            else:
                await update.message.reply_text(res["text"], parse_mode="Markdown", reply_markup=reply_markup)

        async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            query = update.callback_query
            await query.answer()
            user_id = query.from_user.username or str(query.from_user.id)
            res = self.process_callback_query(query.data, user_id=user_id)

            if res.get("alert"):
                await query.answer(text=res["alert"], show_alert=True)

            reply_markup = None
            if res.get("buttons"):
                keyboard = [
                    [InlineKeyboardButton(btn["text"], callback_data=btn["callback_data"]) for btn in row]
                    for row in res["buttons"]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

            if res.get("photo") and os.path.exists(res["photo"]):
                with open(res["photo"], "rb") as f:
                    await query.message.reply_photo(photo=f, caption=res["text"], parse_mode="Markdown", reply_markup=reply_markup)
            else:
                await query.edit_message_text(res["text"], parse_mode="Markdown", reply_markup=reply_markup)

        app = ApplicationBuilder().token(self.bot_token).build()
        app.add_handler(CommandHandler("start", start_cmd))
        app.add_handler(CommandHandler("help", start_cmd))
        app.add_handler(CommandHandler("report", lambda u, c: text_handler(u, c)))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
        app.add_handler(CallbackQueryHandler(callback_handler))

        print("🤖 ZeroWaste Telegram Bot is running in live polling mode!")
        app.run_polling()

if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    bot = ZeroWasteGroceryBot()

    if bot.bot_token and not bot.bot_token.startswith("YOUR_"):
        print("=======================================================")
        print(" 🤖 ZeroWaste Grocery Assistant - Live Telegram Mode")
        print("=======================================================")
        print(f"Token loaded: {bot.bot_token[:10]}********")
        print("Listening for messages on Telegram... (Press Ctrl+C to stop)")
        bot.run_live_telegram_bot()
    else:
        print("=======================================================")
        print(" ZeroWaste Grocery Assistant - Telegram Simulator Test")
        print(" (No TELEGRAM_BOT_TOKEN found. Running test queries)")
        print("=======================================================\n")

        # Test Query 1: "How much milk should I order today?"
        print("--- [User]: 'How much milk should I order today?' ---")
        r1 = bot.process_incoming_text("How much milk should I order today?")
        print(r1["text"])
        rec_id = r1.get("recommendation", {}).get("recommendation_id")

        # Test Query 2: "Approve"
        if rec_id:
            print(f"\n--- [User]: 'Approve {rec_id}' ---")
            r_app = bot.process_incoming_text(f"Approve {rec_id}")
            print(r_app["text"])

        # Test Query 3: "Do I need to discount bread?"
        print("\n--- [User]: 'Do I need to discount bread?' ---")
        r2 = bot.process_incoming_text("Do I need to discount bread?")
        print(r2["text"])

        # Test Query 4: "Is my store at risk of waste this week?"
        print("\n--- [User]: 'Is my store at risk of waste this week?' ---")
        r3 = bot.process_incoming_text("Is my store at risk of waste this week?")
        print(r3["text"])

        # Test Query 5: "Show evaluation report"
        print("\n--- [User]: 'Show evaluation report' ---")
        r4 = bot.process_incoming_text("Show evaluation report")
        print(r4["text"])
        print(f"Photo Attachment: {r4.get('photo')}")
