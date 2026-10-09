"""
ZeroWaste Grocery Assistant - Synthetic Data Generator & Simulation Engine
Generates realistic datasets for perishable grocery inventory, multi-store operations,
weather effects, shelf-life, and demand dynamics.
"""

import os
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Set seeds for reproducible realism
np.random.seed(42)
random.seed(42)

def generate_all_datasets(reference_date=None):
    if reference_date is None:
        reference_date = datetime.now().date()
    elif isinstance(reference_date, str):
        reference_date = datetime.strptime(reference_date, "%Y-%m-%d").date()

    print(f"Generating synthetic datasets using reference date: {reference_date}")

    # 1. Product Catalog & Shelf Life
    products = [
        {
            "sku_id": "SKU_MILK_1L",
            "name": "Whole Milk 1L",
            "category": "Dairy",
            "shelf_life_days": 7,
            "unit_cost": 1.80,
            "retail_price": 3.49,
            "safety_stock": 18,
            "reorder_batch_size": 45,
            "base_daily_demand": 32,
            "price_elasticity": 1.4,
            "temp_optimum_c": 3.5,
        },
        {
            "sku_id": "SKU_BREAD_WHEAT",
            "name": "Artisan Whole Wheat Bread",
            "category": "Bakery",
            "shelf_life_days": 4,
            "unit_cost": 1.10,
            "retail_price": 2.99,
            "safety_stock": 14,
            "reorder_batch_size": 35,
            "base_daily_demand": 26,
            "price_elasticity": 1.8,
            "temp_optimum_c": 20.0,
        },
        {
            "sku_id": "SKU_BERRIES_250G",
            "name": "Fresh Strawberries 250g",
            "category": "Produce",
            "shelf_life_days": 3,
            "unit_cost": 2.20,
            "retail_price": 4.99,
            "safety_stock": 10,
            "reorder_batch_size": 25,
            "base_daily_demand": 19,
            "price_elasticity": 2.2,
            "temp_optimum_c": 2.0,
        },
        {
            "sku_id": "SKU_YOGURT_500G",
            "name": "Greek Yogurt 500g",
            "category": "Dairy",
            "shelf_life_days": 12,
            "unit_cost": 1.60,
            "retail_price": 3.79,
            "safety_stock": 15,
            "reorder_batch_size": 40,
            "base_daily_demand": 22,
            "price_elasticity": 1.2,
            "temp_optimum_c": 4.0,
        },
        {
            "sku_id": "SKU_SALAD_BOWL",
            "name": "Organic Salad Bowl",
            "category": "Produce",
            "shelf_life_days": 4,
            "unit_cost": 2.10,
            "retail_price": 4.89,
            "safety_stock": 12,
            "reorder_batch_size": 30,
            "base_daily_demand": 24,
            "price_elasticity": 2.0,
            "temp_optimum_c": 4.0,
        },
        {
            "sku_id": "SKU_CHICKEN_500G",
            "name": "Fresh Chicken Breast 500g",
            "category": "Meat",
            "shelf_life_days": 4,
            "unit_cost": 3.80,
            "retail_price": 6.99,
            "safety_stock": 12,
            "reorder_batch_size": 25,
            "base_daily_demand": 20,
            "price_elasticity": 1.6,
            "temp_optimum_c": 1.5,
        },
    ]
    df_products = pd.DataFrame(products)
    df_products.to_csv(os.path.join(DATA_DIR, "products.csv"), index=False)

    # 2. Stores Network
    stores = [
        {
            "store_id": "STORE_001",
            "store_name": "Downtown Express",
            "location": "Metro Financial Center",
            "traffic_factor": 1.35,
            "manager_name": "Alex Vance",
            "contact_email": "alex.vance@zerowastegrocery.com",
        },
        {
            "store_id": "STORE_002",
            "store_name": "Suburban Hub",
            "location": "Westfield Green District",
            "traffic_factor": 0.90,
            "manager_name": "Sarah Jenkins",
            "contact_email": "sarah.j@zerowastegrocery.com",
        },
        {
            "store_id": "STORE_003",
            "store_name": "Uptown Fresh Mart",
            "location": "Northside Residential Ave",
            "traffic_factor": 1.10,
            "manager_name": "Marcus Rivera",
            "contact_email": "marcus.r@zerowastegrocery.com",
        },
    ]
    df_stores = pd.DataFrame(stores)
    df_stores.to_csv(os.path.join(DATA_DIR, "stores.csv"), index=False)

    # 3. Inter-Store Distances & Transfer Costs
    distances = [
        {"from_store": "STORE_001", "to_store": "STORE_002", "distance_km": 7.4, "transfer_fee": 9.50, "transit_hours": 1.0},
        {"from_store": "STORE_001", "to_store": "STORE_003", "distance_km": 4.8, "transfer_fee": 6.50, "transit_hours": 0.5},
        {"from_store": "STORE_002", "to_store": "STORE_001", "distance_km": 7.4, "transfer_fee": 9.50, "transit_hours": 1.0},
        {"from_store": "STORE_002", "to_store": "STORE_003", "distance_km": 9.2, "transfer_fee": 11.00, "transit_hours": 1.2},
        {"from_store": "STORE_003", "to_store": "STORE_001", "distance_km": 4.8, "transfer_fee": 6.50, "transit_hours": 0.5},
        {"from_store": "STORE_003", "to_store": "STORE_002", "distance_km": 9.2, "transfer_fee": 11.00, "transit_hours": 1.2},
    ]
    df_dist = pd.DataFrame(distances)
    df_dist.to_csv(os.path.join(DATA_DIR, "store_distances.csv"), index=False)

    # 4. Weather & Local Events (Past 90 days + next 7 days forecast)
    start_date = reference_date - timedelta(days=90)
    end_date = reference_date + timedelta(days=7)
    current = start_date
    weather_list = []
    weather_types = ["Sunny", "Partly Cloudy", "Rainy", "Heavy Storm", "Mild", "Heatwave"]
    weather_probs = [0.40, 0.25, 0.18, 0.05, 0.08, 0.04]

    special_events = {
        -45: "Community Sports Meet",
        -28: "Downtown Street Fair",
        -14: "Long Weekend Holiday",
        -3: "Midweek Marathon",
        1: "Local Farmers Market",
        3: "Heatwave Advisory",
        5: "Weekend Music Festival",
    }

    while current <= end_date:
        w = np.random.choice(weather_types, p=weather_probs)
        temp = 22.0
        if w == "Sunny":
            temp = np.random.normal(26.0, 2.5)
        elif w == "Heatwave":
            temp = np.random.normal(33.0, 1.5)
        elif w == "Rainy":
            temp = np.random.normal(18.0, 2.0)
        elif w == "Heavy Storm":
            temp = np.random.normal(15.0, 2.5)
        else:
            temp = np.random.normal(21.0, 2.0)

        days_diff = (current - reference_date).days
        event_name = special_events.get(days_diff, "Normal Day")
        is_weekend = 1 if current.weekday() in (5, 6) else 0

        # Multiplier on general store foot traffic
        foot_traffic_mult = 1.0
        if w == "Heavy Storm":
            foot_traffic_mult *= 0.70
        elif w == "Rainy":
            foot_traffic_mult *= 0.85
        elif w == "Heatwave":
            foot_traffic_mult *= 1.10
        elif w == "Sunny":
            foot_traffic_mult *= 1.05

        if event_name != "Normal Day":
            foot_traffic_mult *= 1.25
        if is_weekend:
            foot_traffic_mult *= 1.20

        weather_list.append({
            "date": current.strftime("%Y-%m-%d"),
            "weather": w,
            "temperature_c": round(temp, 1),
            "event": event_name,
            "is_weekend": is_weekend,
            "foot_traffic_multiplier": round(foot_traffic_mult, 3),
        })
        current += timedelta(days=1)

    df_weather = pd.DataFrame(weather_list)
    df_weather.to_csv(os.path.join(DATA_DIR, "weather_events.csv"), index=False)

    # 5. Historical Daily Sales (90 days)
    sales_rows = []
    weather_dict = {row["date"]: row for row in weather_list}

    for days_back in range(90, 0, -1):
        sale_date = reference_date - timedelta(days=days_back)
        date_str = sale_date.strftime("%Y-%m-%d")
        w_info = weather_dict.get(date_str, {})
        weather_type = w_info.get("weather", "Sunny")
        temp = w_info.get("temperature_c", 22.0)
        event = w_info.get("event", "Normal Day")
        is_weekend = w_info.get("is_weekend", 0)
        traffic_mult = w_info.get("foot_traffic_multiplier", 1.0)

        for store in stores:
            s_id = store["store_id"]
            s_factor = store["traffic_factor"]

            for prod in products:
                sku = prod["sku_id"]
                base_demand = prod["base_daily_demand"]
                elasticity = prod["price_elasticity"]
                price = prod["retail_price"]

                # Random promotional discount occasional (10% chance)
                has_promo = 1 if (random.random() < 0.12 and not is_weekend) else 0
                discount_rate = 0.20 if has_promo else 0.0

                # Category specific weather effects
                cat_mult = 1.0
                if prod["category"] == "Produce" and weather_type in ("Sunny", "Heatwave"):
                    cat_mult = 1.30
                elif prod["category"] == "Produce" and weather_type in ("Rainy", "Heavy Storm"):
                    cat_mult = 0.85
                elif prod["category"] == "Dairy" and weather_type == "Heatwave":
                    cat_mult = 1.20
                elif prod["category"] == "Bakery" and is_weekend:
                    cat_mult = 1.25

                # Price discount boost: demand * (1 + elasticity * discount_rate)
                price_mult = 1.0 + (elasticity * discount_rate)

                expected_demand = base_demand * s_factor * traffic_mult * cat_mult * price_mult
                noise = np.random.normal(0, expected_demand * 0.10)
                actual_demand = max(2, int(round(expected_demand + noise)))

                effective_price = round(price * (1.0 - discount_rate), 2)
                revenue = round(actual_demand * effective_price, 2)

                sales_rows.append({
                    "date": date_str,
                    "store_id": s_id,
                    "sku_id": sku,
                    "units_sold": actual_demand,
                    "price": effective_price,
                    "discount_rate": discount_rate,
                    "is_promotion": has_promo,
                    "weather": weather_type,
                    "temperature_c": temp,
                    "event": event,
                    "is_weekend": is_weekend,
                    "revenue": revenue,
                })

    df_sales = pd.DataFrame(sales_rows)
    df_sales.to_csv(os.path.join(DATA_DIR, "sales_history.csv"), index=False)

    # 6. Current On-Hand Batch Inventory (Realistic as of today)
    # We craft specific realistic scenarios:
    # - STORE_001 Milk: on-hand is low -> Stockout Risk -> Reorder Recommendation!
    # - STORE_001 Bread: batch expiring tomorrow, high stock -> Spoilage Risk -> Markdown Recommendation!
    # - STORE_001 Berries: excess stock expiring in 2 days; STORE_002 Berries has zero stock & high demand -> Transfer Recommendation!
    # - STORE_002 Yogurt: balanced stock, fresh batches -> Healthy / Steady.
    # - STORE_003 Chicken: near expiry, moderate surplus -> Markdown / Reorder combo.
    inventory_batches = [
        # STORE_001 (Downtown Express)
        {
            "store_id": "STORE_001",
            "sku_id": "SKU_MILK_1L",
            "batch_id": "BATCH_M101",
            "quantity": 12,  # Low! Safety stock is 18, daily demand ~46. Will stockout today!
            "received_date": (reference_date - timedelta(days=4)).strftime("%Y-%m-%d"),
            "expiry_date": (reference_date + timedelta(days=3)).strftime("%Y-%m-%d"),
        },
        {
            "store_id": "STORE_001",
            "sku_id": "SKU_BREAD_WHEAT",
            "batch_id": "BATCH_B201",
            "quantity": 62,  # High stock! Shelf life remaining 1 day (expires tomorrow). ~22 units at risk!
            "received_date": (reference_date - timedelta(days=3)).strftime("%Y-%m-%d"),
            "expiry_date": (reference_date + timedelta(days=1)).strftime("%Y-%m-%d"),
        },
        {
            "store_id": "STORE_001",
            "sku_id": "SKU_BERRIES_250G",
            "batch_id": "BATCH_R301",
            "quantity": 85,  # Substantial surplus (expires in 2 days). ~18 units at risk! STORE_002 needs it!
            "received_date": (reference_date - timedelta(days=1)).strftime("%Y-%m-%d"),
            "expiry_date": (reference_date + timedelta(days=2)).strftime("%Y-%m-%d"),
        },
        {
            "store_id": "STORE_001",
            "sku_id": "SKU_YOGURT_500G",
            "batch_id": "BATCH_Y401",
            "quantity": 35,  # Balanced, expires in 8 days
            "received_date": (reference_date - timedelta(days=4)).strftime("%Y-%m-%d"),
            "expiry_date": (reference_date + timedelta(days=8)).strftime("%Y-%m-%d"),
        },
        {
            "store_id": "STORE_001",
            "sku_id": "SKU_SALAD_BOWL",
            "batch_id": "BATCH_S501",
            "quantity": 28,  # Expires in 2 days, demand is high
            "received_date": (reference_date - timedelta(days=2)).strftime("%Y-%m-%d"),
            "expiry_date": (reference_date + timedelta(days=2)).strftime("%Y-%m-%d"),
        },
        {
            "store_id": "STORE_001",
            "sku_id": "SKU_CHICKEN_500G",
            "batch_id": "BATCH_C601",
            "quantity": 14,  # Moderate, expires in 2 days
            "received_date": (reference_date - timedelta(days=2)).strftime("%Y-%m-%d"),
            "expiry_date": (reference_date + timedelta(days=2)).strftime("%Y-%m-%d"),
        },

        # STORE_002 (Suburban Hub)
        {
            "store_id": "STORE_002",
            "sku_id": "SKU_MILK_1L",
            "batch_id": "BATCH_M102",
            "quantity": 40,
            "received_date": (reference_date - timedelta(days=2)).strftime("%Y-%m-%d"),
            "expiry_date": (reference_date + timedelta(days=5)).strftime("%Y-%m-%d"),
        },
        {
            "store_id": "STORE_002",
            "sku_id": "SKU_BREAD_WHEAT",
            "batch_id": "BATCH_B202",
            "quantity": 18,
            "received_date": (reference_date - timedelta(days=1)).strftime("%Y-%m-%d"),
            "expiry_date": (reference_date + timedelta(days=3)).strftime("%Y-%m-%d"),
        },
        {
            "store_id": "STORE_002",
            "sku_id": "SKU_BERRIES_250G",
            "batch_id": "BATCH_R302",
            "quantity": 4,  # Critically low! Stockout imminent! Ideal candidate for transfer from STORE_001!
            "received_date": (reference_date - timedelta(days=2)).strftime("%Y-%m-%d"),
            "expiry_date": (reference_date + timedelta(days=1)).strftime("%Y-%m-%d"),
        },
        {
            "store_id": "STORE_002",
            "sku_id": "SKU_YOGURT_500G",
            "batch_id": "BATCH_Y402",
            "quantity": 55,  # Well stocked
            "received_date": (reference_date - timedelta(days=3)).strftime("%Y-%m-%d"),
            "expiry_date": (reference_date + timedelta(days=9)).strftime("%Y-%m-%d"),
        },
        {
            "store_id": "STORE_002",
            "sku_id": "SKU_SALAD_BOWL",
            "batch_id": "BATCH_S502",
            "quantity": 16,
            "received_date": (reference_date - timedelta(days=1)).strftime("%Y-%m-%d"),
            "expiry_date": (reference_date + timedelta(days=3)).strftime("%Y-%m-%d"),
        },
        {
            "store_id": "STORE_002",
            "sku_id": "SKU_CHICKEN_500G",
            "batch_id": "BATCH_C602",
            "quantity": 22,
            "received_date": (reference_date - timedelta(days=1)).strftime("%Y-%m-%d"),
            "expiry_date": (reference_date + timedelta(days=3)).strftime("%Y-%m-%d"),
        },

        # STORE_003 (Uptown Fresh Mart)
        {
            "store_id": "STORE_003",
            "sku_id": "SKU_MILK_1L",
            "batch_id": "BATCH_M103",
            "quantity": 30,
            "received_date": (reference_date - timedelta(days=3)).strftime("%Y-%m-%d"),
            "expiry_date": (reference_date + timedelta(days=4)).strftime("%Y-%m-%d"),
        },
        {
            "store_id": "STORE_003",
            "sku_id": "SKU_BREAD_WHEAT",
            "batch_id": "BATCH_B203",
            "quantity": 20,
            "received_date": (reference_date - timedelta(days=2)).strftime("%Y-%m-%d"),
            "expiry_date": (reference_date + timedelta(days=2)).strftime("%Y-%m-%d"),
        },
        {
            "store_id": "STORE_003",
            "sku_id": "SKU_BERRIES_250G",
            "batch_id": "BATCH_R303",
            "quantity": 18,
            "received_date": (reference_date - timedelta(days=1)).strftime("%Y-%m-%d"),
            "expiry_date": (reference_date + timedelta(days=2)).strftime("%Y-%m-%d"),
        },
        {
            "store_id": "STORE_003",
            "sku_id": "SKU_YOGURT_500G",
            "batch_id": "BATCH_Y403",
            "quantity": 42,
            "received_date": (reference_date - timedelta(days=2)).strftime("%Y-%m-%d"),
            "expiry_date": (reference_date + timedelta(days=10)).strftime("%Y-%m-%d"),
        },
        {
            "store_id": "STORE_003",
            "sku_id": "SKU_SALAD_BOWL",
            "batch_id": "BATCH_S503",
            "quantity": 30,
            "received_date": (reference_date - timedelta(days=1)).strftime("%Y-%m-%d"),
            "expiry_date": (reference_date + timedelta(days=3)).strftime("%Y-%m-%d"),
        },
        {
            "store_id": "STORE_003",
            "sku_id": "SKU_CHICKEN_500G",
            "batch_id": "BATCH_C603",
            "quantity": 18,
            "received_date": (reference_date - timedelta(days=1)).strftime("%Y-%m-%d"),
            "expiry_date": (reference_date + timedelta(days=3)).strftime("%Y-%m-%d"),
        },
    ]

    # Calculate remaining shelf life days dynamically for current date
    for b in inventory_batches:
        exp_dt = datetime.strptime(b["expiry_date"], "%Y-%m-%d").date()
        rem_days = (exp_dt - reference_date).days
        b["remaining_shelf_days"] = max(0, rem_days)

    df_inventory = pd.DataFrame(inventory_batches)
    df_inventory.to_csv(os.path.join(DATA_DIR, "inventory.csv"), index=False)

    print("Successfully generated all synthetic datasets in:", DATA_DIR)
    return {
        "products": len(df_products),
        "stores": len(df_stores),
        "distances": len(df_dist),
        "weather_days": len(df_weather),
        "sales_records": len(df_sales),
        "inventory_batches": len(df_inventory),
    }

if __name__ == "__main__":
    generate_all_datasets()
