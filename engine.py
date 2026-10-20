import pandas as pd
import numpy as np

def validate_and_process_data(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    if df is None or df.empty:
        raise ValueError("The uploaded dataset is empty.")

    required_keys = ['date', 'product', 'quantity', 'sales', 'cost']
    for key in required_keys:
        if not mapping.get(key) or mapping[key] not in df.columns:
            raise ValueError(f"Missing required column mapping for: '{key}'.")

    processed = pd.DataFrame()
    processed['Date'] = pd.to_datetime(df[mapping['date']], errors='coerce')
    processed['Product'] = df[mapping['product']].astype(str).str.strip()
    
    def clean_numeric(series):
        if series.dtype == object:
            series = series.astype(str).str.replace(r'[₹$,\s]', '', regex=True)
        return pd.to_numeric(series, errors='coerce')

    processed['Quantity'] = clean_numeric(df[mapping['quantity']])
    processed['Sales'] = clean_numeric(df[mapping['sales']])
    processed['Cost'] = clean_numeric(df[mapping['cost']])

    processed = processed.dropna(subset=['Date', 'Quantity', 'Sales', 'Cost']).copy()
    
    processed['Gross_Profit'] = (processed['Sales'] - processed['Cost']).round(2)
    processed['Margin_%'] = np.where(
        processed['Sales'] > 0,
        ((processed['Gross_Profit'] / processed['Sales']) * 100).round(2),
        0.0
    )
    
    processed['Month'] = processed['Date'].dt.to_period('M').astype(str)
    return processed

def compute_kpis(df: pd.DataFrame) -> dict:
    total_sales = float(df['Sales'].sum())
    total_cost = float(df['Cost'].sum())
    total_profit = float(df['Gross_Profit'].sum())
    overall_margin = round((total_profit / total_sales) * 100, 2) if total_sales > 0 else 0.0

    return {
        "sales": total_sales,
        "cost": total_cost,
        "profit": total_profit,
        "margin": overall_margin,
        "transactions": len(df)
    }
