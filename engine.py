import pandas as pd
import numpy as np

def validate_and_process_data(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    if df is None or df.empty:
        raise ValueError("The uploaded dataset is empty. Please provide a valid file.")

    required_keys = ['date', 'product', 'quantity', 'sales', 'cost']
    for key in required_keys:
        col_name = mapping.get(key)
        if not col_name or col_name not in df.columns:
            raise ValueError(f"Missing or invalid column mapping for required field: '{key}'.")

    processed = pd.DataFrame()
    processed['Date'] = pd.to_datetime(df[mapping['date']], errors='coerce')
    processed['Product'] = df[mapping['product']].astype(str).str.strip()
    processed['Product'] = processed['Product'].replace({'nan': 'Unknown Product', '': 'Unknown Product'})

    def clean_numeric(series):
        if series.dtype == object:
            series = series.astype(str).str.replace(r'[₹$,\s]', '', regex=True)
        return pd.to_numeric(series, errors='coerce')

    processed['Quantity'] = clean_numeric(df[mapping['quantity']])
    processed['Sales'] = clean_numeric(df[mapping['sales']])
    processed['Cost'] = clean_numeric(df[mapping['cost']])

    if mapping.get('expenses') and mapping['expenses'] != "None" and mapping['expenses'] in df.columns:
        processed['Expenses'] = clean_numeric(df[mapping['expenses']]).fillna(0.0)
    else:
        processed['Expenses'] = 0.0

    initial_count = len(processed)
    processed = processed.dropna(subset=['Date', 'Quantity', 'Sales', 'Cost']).copy()
    
    if processed.empty:
        raise ValueError("No valid rows remained after cleaning. Please check your data types.")

    processed = processed[
        (processed['Quantity'] > 0) & 
        (processed['Sales'] >= 0) & 
        (processed['Cost'] >= 0) & 
        (processed['Expenses'] >= 0)
    ].copy()

    if processed.empty:
        raise ValueError("All rows contained zero or negative quantities/sales.")

    processed['Gross_Profit'] = (processed['Sales'] - processed['Cost']).round(2)
    processed['Net_Profit'] = (processed['Gross_Profit'] - processed['Expenses']).round(2)

    processed['Gross_Margin_%'] = np.where(
        processed['Sales'] > 0,
        ((processed['Gross_Profit'] / processed['Sales']) * 100).round(2),
        0.0
    )
    processed['Net_Margin_%'] = np.where(
        processed['Sales'] > 0,
        ((processed['Net_Profit'] / processed['Sales']) * 100).round(2),
        0.0
    )

    processed['Month_Year'] = processed['Date'].dt.to_period('M').astype(str)
    processed.attrs['dropped_rows'] = initial_count - len(processed)

    return processed

def compute_summary_kpis(df: pd.DataFrame) -> dict:
    total_revenue = float(df['Sales'].sum())
    total_cost = float(df['Cost'].sum())
    total_gross_profit = float(df['Gross_Profit'].sum())
    total_expenses = float(df['Expenses'].sum())
    total_net_profit = float(df['Net_Profit'].sum())
    total_units = int(df['Quantity'].sum())

    gross_margin_pct = round((total_gross_profit / total_revenue) * 100, 2) if total_revenue > 0 else 0.0
    net_margin_pct = round((total_net_profit / total_revenue) * 100, 2) if total_revenue > 0 else 0.0

    return {
        "total_revenue": round(total_revenue, 2),
        "total_cost": round(total_cost, 2),
        "total_gross_profit": round(total_gross_profit, 2),
        "total_expenses": round(total_expenses, 2),
        "total_net_profit": round(total_net_profit, 2),
        "gross_margin_pct": gross_margin_pct,
        "net_margin_pct": net_margin_pct,
        "total_units": total_units,
        "total_transactions": len(df),
        "dropped_rows": df.attrs.get('dropped_rows', 0)
    }

def generate_deterministic_insights(df: pd.DataFrame, kpis: dict) -> list:
    insights = []
    prod_summary = df.groupby('Product').agg(
        Sales=('Sales', 'sum'),
        Net_Profit=('Net_Profit', 'sum'),
        Quantity=('Quantity', 'sum')
    ).reset_index()
    prod_summary['Net_Margin_%'] = np.where(
        prod_summary['Sales'] > 0,
        (prod_summary['Net_Profit'] / prod_summary['Sales']) * 100,
        0.0
    )

    if not prod_summary.empty:
        best_prod = prod_summary.loc[prod_summary['Net_Profit'].idxmax()]
        insights.append(
            f"🏆 **Top Profit Driver:** *{best_prod['Product']}* generated the highest net profit "
            f"(**₹{best_prod['Net_Profit']:,.2f}** across {int(best_prod['Quantity'])} units with a "
            f"**{best_prod['Net_Margin_%']:.1f}%** net margin)."
        )

        worst_margin_prod = prod_summary.loc[prod_summary['Net_Margin_%'].idxmin()]
        if worst_margin_prod['Product'] != best_prod['Product']:
            insights.append(
                f"⚠️ **Lowest Margin Item:** *{worst_margin_prod['Product']}* has your lowest net margin at "
                f"**{worst_margin_prod['Net_Margin_%']:.1f}%** (Net Profit: ₹{worst_margin_prod['Net_Profit']:,.2f})."
            )

    if kpis['total_expenses'] > 0 and kpis['total_gross_profit'] > 0:
        expense_ratio = (kpis['total_expenses'] / kpis['total_gross_profit']) * 100
        insights.append(
            f"📦 **Expense Impact:** Direct expenses consumed **{expense_ratio:.1f}%** of your gross profit "
            f"(₹{kpis['total_expenses']:,.2f} out of ₹{kpis['total_gross_profit']:,.2f})."
        )

    monthly = df.groupby('Month_Year')['Net_Profit'].sum().reset_index()
    if len(monthly) > 1:
        best_month = monthly.loc[monthly['Net_Profit'].idxmax()]
        insights.append(
            f"📅 **Peak Month:** Your strongest month was **{best_month['Month_Year']}**, "
            f"delivering **₹{best_month['Net_Profit']:,.2f}** in estimated net profit."
        )

    return insights
