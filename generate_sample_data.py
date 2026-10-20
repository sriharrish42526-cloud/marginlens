import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_data(filename="sample_sales_data.csv"):
    np.random.seed(42)
    start_date = datetime(2025, 4, 1)
    dates = [start_date + timedelta(days=int(np.random.randint(0, 365))) for _ in range(500)]
    
    products = {
        "Premium Rice (5kg)": {"cost": 350, "margin": 1.25},
        "Lentils / Split Dal (1kg)": {"cost": 120, "margin": 1.30},
        "Iodized Salt (1kg)": {"cost": 24, "margin": 1.15},
        "Sunflower Cooking Oil (1L)": {"cost": 130, "margin": 1.18},
        "Whole Wheat Flour (10kg)": {"cost": 380, "margin": 1.20},
        "Assam Black Tea (500g)": {"cost": 280, "margin": 1.28},
        "Refined Sugar (5kg)": {"cost": 210, "margin": 1.12},
        "Roast Ground Coffee (250g)": {"cost": 160, "margin": 1.35}
    }
    
    product_names = list(products.keys())
    data = []
    
    for i in range(500):
        prod = np.random.choice(product_names)
        qty = int(np.random.randint(1, 15))
        unit_cost = products[prod]["cost"]
        total_cost = round(unit_cost * qty, 2)
        price_variation = np.random.uniform(0.97, 1.03)
        unit_price = round(unit_cost * products[prod]["margin"] * price_variation, 2)
        total_sales = round(unit_price * qty, 2)
        expense = float(np.random.choice([0, 0, 20, 50, 100]))
        
        data.append({
            "Transaction_Date": dates[i].strftime("%Y-%m-%d"),
            "Product_Name": prod,
            "Quantity_Sold": qty,
            "Sales_Revenue": total_sales,
            "Cost_of_Goods": total_cost,
            "Direct_Expenses": expense
        })
        
    df = pd.DataFrame(data).sort_values(by="Transaction_Date").reset_index(drop=True)
    df.to_csv(filename, index=False)
    print(f"✅ Successfully generated {filename} with {len(df)} rows!")

if __name__ == "__main__":
    generate_data()
