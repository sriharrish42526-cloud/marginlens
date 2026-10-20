import streamlit as st
import pandas as pd
import plotly.express as px
import io
import os
from engine import validate_and_process_data, compute_summary_kpis, generate_deterministic_insights
from generate_sample_data import generate_data

st.set_page_config(
    page_title="MarginLens | Sales & Profit Analyzer",
    page_icon="📊",
    layout="wide"
)

secret_api_key = None
try:
    if "GEMINI_API_KEY" in st.secrets:
        secret_api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

st.sidebar.title("⚙️ MarginLens Controls")
st.sidebar.markdown("Upload your sales ledger to calculate exact margins and profitability.")

st.sidebar.header("1. Data Source")
data_source = st.sidebar.radio("Choose data input:", ["Use Demo Retail Data", "Upload CSV / Excel File"])

df_raw = None
if data_source == "Use Demo Retail Data":
    if not os.path.exists("sample_sales_data.csv"):
        generate_data("sample_sales_data.csv")
    df_raw = pd.read_csv("sample_sales_data.csv")
    st.sidebar.success("Loaded 500 rows of synthetic retail data.")
else:
    uploaded_file = st.sidebar.file_uploader("Upload XLSX or CSV", type=["csv", "xlsx"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.lower().endswith(".csv"):
                df_raw = pd.read_csv(uploaded_file)
            else:
                df_raw = pd.read_excel(uploaded_file, engine="openpyxl")
            st.sidebar.success(f"Loaded '{uploaded_file.name}' ({len(df_raw)} rows)")
        except Exception as e:
            st.sidebar.error(f"Error reading file: {e}")

st.sidebar.markdown("---")
st.sidebar.header("3. Optional Assistant")
user_api_key = st.sidebar.text_input("Gemini API Key (Optional)", type="password")
active_api_key = user_api_key.strip() if user_api_key else secret_api_key

if active_api_key:
    st.title("📊 MarginLens *(AI Explanations Enabled)*")
else:
    st.title("📊 MarginLens")

st.markdown("**Deterministic Sales, Margin & Profit Analysis for Small Businesses**")

if df_raw is not None:
    with st.expander("🔍 Preview Raw Data (First 10 Rows)", expanded=False):
        st.dataframe(df_raw.head(10), use_container_width=True)

    st.sidebar.header("2. Map Your Columns")
    cols = list(df_raw.columns)

    def guess_col(keywords, default_idx=0):
        for idx, col in enumerate(cols):
            if any(k in col.lower() for k in keywords):
                return idx
        return min(default_idx, len(cols) - 1)

    date_col = st.sidebar.selectbox("Transaction Date", cols, index=guess_col(["date", "time", "day"], 0))
    prod_col = st.sidebar.selectbox("Product / Item Name", cols, index=guess_col(["prod", "item", "name"], 1))
    qty_col = st.sidebar.selectbox("Quantity Sold", cols, index=guess_col(["qty", "quant", "unit"], 2))
    sales_col = st.sidebar.selectbox("Total Sales Revenue (₹)", cols, index=guess_col(["sale", "rev", "amount"], 3))
    cost_col = st.sidebar.selectbox("Total Cost of Goods (₹)", cols, index=guess_col(["cost", "cogs", "purchase"], 4))

    exp_options = ["None"] + cols
    exp_guess = 0
    for idx, col in enumerate(exp_options):
        if any(k in col.lower() for k in ["exp", "ship", "pack", "fee"]):
            exp_guess = idx
            break
    exp_col = st.sidebar.selectbox("Direct Expenses (Optional)", exp_options, index=exp_guess)

    mapping = {
        "date": date_col,
        "product": prod_col,
        "quantity": qty_col,
        "sales": sales_col,
        "cost": cost_col,
        "expenses": None if exp_col == "None" else exp_col
    }

    try:
        df_clean = validate_and_process_data(df_raw, mapping)
        kpis = compute_summary_kpis(df_clean)

        st.markdown("---")
        st.subheader("📌 Financial Summary")
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Total Revenue", f"₹{kpis['total_revenue']:,.2f}")
        k2.metric("Total Cost (COGS)", f"₹{kpis['total_cost']:,.2f}")
        k3.metric("Gross Profit", f"₹{kpis['total_gross_profit']:,.2f}", f"{kpis['gross_margin_pct']}% Gross Margin")
        k4.metric("Direct Expenses", f"₹{kpis['total_expenses']:,.2f}")
        k5.metric("Estimated Net Profit", f"₹{kpis['total_net_profit']:,.2f}", f"{kpis['net_margin_pct']}% Net Margin")

        st.markdown("---")
        st.subheader("💡 Automated Data-Driven Insights")
        insights = generate_deterministic_insights(df_clean, kpis)
        for item in insights:
            st.markdown(f"- {item}")

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📅 Monthly Revenue & Net Profit Trend")
            monthly_df = df_clean.groupby("Month_Year")[["Sales", "Gross_Profit", "Net_Profit"]].sum().reset_index()
            fig_trend = px.bar(monthly_df, x="Month_Year", y=["Sales", "Net_Profit"], barmode="group")
            st.plotly_chart(fig_trend, use_container_width=True)

        with c2:
            st.subheader("📦 Product Profitability Breakdown")
            prod_df = df_clean.groupby("Product")[["Sales", "Net_Profit", "Quantity"]].sum().reset_index()
            prod_df = prod_df.sort_values(by="Net_Profit", ascending=True)
            fig_prod = px.bar(prod_df, x="Net_Profit", y="Product", orientation="h")
            st.plotly_chart(fig_prod, use_container_width=True)

        st.markdown("---")
        st.subheader("📥 Downloadable Reports")
        prod_table = df_clean.groupby("Product").agg(
            Units_Sold=("Quantity", "sum"),
            Revenue=("Sales", "sum"),
            Cost=("Cost", "sum"),
            Gross_Profit=("Gross_Profit", "sum"),
            Expenses=("Expenses", "sum"),
            Net_Profit=("Net_Profit", "sum")
        ).reset_index()
        prod_table["Net_Margin_%"] = ((prod_table["Net_Profit"] / prod_table["Revenue"]) * 100).round(2)
        
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            prod_table.to_excel(writer, index=False, sheet_name="Product_Profitability")
            monthly_df.to_excel(writer, index=False, sheet_name="Monthly_Trends")
            df_clean.to_excel(writer, index=False, sheet_name="Cleaned_Transactions")
        
        st.download_button(
            label="📊 Download Full Excel Report (.xlsx)",
            data=excel_buffer.getvalue(),
            file_name="marginlens_financial_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        if active_api_key:
            st.markdown("---")
            st.subheader("🧠 Gemini Business Advisor")
            if st.button("✨ Generate Custom Business Explanation"):
                with st.spinner("Analyzing product margins..."):
                    from google import genai
                    client = genai.Client(api_key=active_api_key)
                    prompt = f"Review these metrics and provide 3 concrete actions to improve net profit:\nRevenue: {kpis['total_revenue']}, Net Profit: {kpis['total_net_profit']}"
                    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                    st.success("Analysis Complete")
                    st.markdown(response.text)

    except Exception as ex:
        st.error(f"Error processing data: {ex}")
else:
    st.info("👈 Select **Use Demo Retail Data** or upload your own spreadsheet in the sidebar to begin.")
