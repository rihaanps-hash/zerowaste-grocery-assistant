"""
Decision Logger & Storage Engine (SQLite)
Logs every AI recommendation, store manager planner interactions (Approve, Reject, Modify),
and provides audit queries and evaluation tracking.
"""

import os
import sqlite3
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zerowaste.db")

class DecisionLogger:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Recommendations table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                rec_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                store_id TEXT NOT NULL,
                sku_id TEXT NOT NULL,
                product_name TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity_or_level TEXT NOT NULL,
                timing TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                expected_effect TEXT,
                rationale TEXT,
                raw_json TEXT
            )
            """)

            # Store manager decisions table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rec_id TEXT NOT NULL,
                manager_id TEXT NOT NULL,
                decision TEXT NOT NULL,  -- 'APPROVED', 'REJECTED', 'MODIFIED'
                modification_notes TEXT,
                applied_action TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (rec_id) REFERENCES recommendations(rec_id)
            )
            """)

            # Evaluation metrics table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                waste_reduction_pct REAL,
                stockout_reduction_pct REAL,
                margin_improvement_pct REAL,
                baseline_waste_units REAL,
                ai_waste_units REAL,
                baseline_margin REAL,
                ai_margin REAL,
                summary_json TEXT
            )
            """)
            conn.commit()

    def log_recommendation(self, rec: dict) -> str:
        rec_id = rec.get("recommendation_id")
        timestamp = rec.get("timestamp") or datetime.now().isoformat()
        raw_json = json.dumps(rec)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO recommendations (
                rec_id, timestamp, store_id, sku_id, product_name,
                action, quantity_or_level, timing, confidence_score,
                expected_effect, rationale, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rec_id,
                timestamp,
                rec.get("store_id", "UNKNOWN"),
                rec.get("sku_id", "UNKNOWN"),
                rec.get("product_name", "UNKNOWN"),
                rec.get("action", "UNKNOWN"),
                rec.get("quantity_or_level", ""),
                rec.get("timing", ""),
                float(rec.get("confidence_score", 0.0)),
                rec.get("expected_effect", ""),
                rec.get("rationale", ""),
                raw_json
            ))
            conn.commit()
        return rec_id

    def log_decision(self, rec_id: str, decision: str, notes: str = "", manager_id: str = "STORE_MGR_01") -> dict:
        decision_clean = decision.strip().upper()
        if decision_clean not in ("APPROVED", "APPROVE", "REJECTED", "REJECT", "MODIFIED", "MODIFY"):
            # Map friendly terms
            if "APPROV" in decision_clean:
                decision_clean = "APPROVED"
            elif "REJECT" in decision_clean:
                decision_clean = "REJECTED"
            elif "MODIF" in decision_clean:
                decision_clean = "MODIFIED"
            else:
                decision_clean = "MODIFIED"

        if decision_clean in ("APPROVE",):
            decision_clean = "APPROVED"
        elif decision_clean in ("REJECT",):
            decision_clean = "REJECTED"
        elif decision_clean in ("MODIFY",):
            decision_clean = "MODIFIED"

        timestamp = datetime.now().isoformat()

        # Find corresponding recommendation
        rec = self.get_recommendation(rec_id)
        applied_action = rec.get("action", "UNKNOWN") if rec else "UNKNOWN"
        if decision_clean == "REJECTED":
            applied_action = "NO_ACTION"
        elif decision_clean == "MODIFIED":
            applied_action = f"CUSTOM: {notes}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO decisions (
                rec_id, manager_id, decision, modification_notes, applied_action, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?)
            """, (rec_id, manager_id, decision_clean, notes, applied_action, timestamp))
            conn.commit()

        return {
            "status": "SUCCESS",
            "rec_id": rec_id,
            "decision": decision_clean,
            "applied_action": applied_action,
            "manager_id": manager_id,
            "timestamp": timestamp,
            "notes": notes,
        }

    def get_recommendation(self, rec_id: str) -> dict:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM recommendations WHERE rec_id = ?", (rec_id,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                if d.get("raw_json"):
                    try:
                        d["details"] = json.loads(d["raw_json"])
                    except Exception:
                        pass
                return d
            return None

    def get_latest_recommendation_for_sku(self, store_id: str, sku_id: str = None) -> dict:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if sku_id:
                cursor.execute("""
                SELECT * FROM recommendations 
                WHERE store_id = ? AND sku_id = ? 
                ORDER BY timestamp DESC LIMIT 1
                """, (store_id, sku_id))
            else:
                cursor.execute("""
                SELECT * FROM recommendations 
                WHERE store_id = ? 
                ORDER BY timestamp DESC LIMIT 1
                """, (store_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_recent_decisions(self, limit: int = 15) -> list:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT d.id, d.rec_id, d.manager_id, d.decision, d.modification_notes,
                   d.applied_action, d.timestamp, r.product_name, r.action as orig_action,
                   r.quantity_or_level, r.store_id
            FROM decisions d
            LEFT JOIN recommendations r ON d.rec_id = r.rec_id
            ORDER BY d.id DESC LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_decision_stats(self) -> dict:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM recommendations")
            total_recs = cursor.fetchone()[0]

            cursor.execute("SELECT decision, count(*) FROM decisions GROUP BY decision")
            counts = dict(cursor.fetchall())

            approved = counts.get("APPROVED", 0)
            rejected = counts.get("REJECTED", 0)
            modified = counts.get("MODIFIED", 0)
            total_decisions = approved + rejected + modified

            adoption_rate = round((approved / total_decisions * 100), 1) if total_decisions > 0 else 0.0

            return {
                "total_recommendations": total_recs,
                "total_decisions": total_decisions,
                "approved": approved,
                "rejected": rejected,
                "modified": modified,
                "manager_adoption_rate_pct": adoption_rate,
            }

    def log_evaluation_run(self, run_id: str, summary: dict):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO evaluation_metrics (
                run_id, timestamp, waste_reduction_pct, stockout_reduction_pct,
                margin_improvement_pct, baseline_waste_units, ai_waste_units,
                baseline_margin, ai_margin, summary_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                datetime.now().isoformat(),
                summary.get("waste_reduction_pct", 0.0),
                summary.get("stockout_reduction_pct", 0.0),
                summary.get("margin_improvement_pct", 0.0),
                summary.get("baseline_waste_units", 0.0),
                summary.get("ai_waste_units", 0.0),
                summary.get("baseline_net_margin", 0.0),
                summary.get("ai_net_margin", 0.0),
                json.dumps(summary)
            ))
            conn.commit()

if __name__ == "__main__":
    logger = DecisionLogger()
    print("Decision Logger initialized. Current stats:", logger.get_decision_stats())
