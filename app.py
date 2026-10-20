import streamlit as st
import pandas as pd
import plotly.express as px
import os
from engine import validate_and_process_data, compute_kpis
from generate_sample_data import generate_data

st.set_page_config(page_title="MarginLens", page_icon="📊", layout="wide")

st.title("📊 MarginLens")
st.markdown("**Simple & Fast Sales & Profit Analyzer**")

# Sidebar
st.sidebar.header("1. Data Source")
data_option = st.sidebar.radio("Select source:", ["Use Demo Data", "Upload File"])

df_raw = None
if data_option == "Use Demo Data":
    if not os.path.exists("sample_sales_data.csv"):
        generate_data("sample_sales_data.csv")
    df_raw = pd.read_csv("sample_sales_data.csv")
    st.sidebar.success("Loaded demo data (500 rows)")
else:
    file = st.sidebar.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
    if file:
        if file.name.endswith(".csv"):
            df_raw = pd.read_csv(file)
            st.sidebar.success(f"Loaded {file.name}")
        else:
            # Read all sheet names from the Excel file
            excel_file = pd.ExcelFile(file)
            sheet_names = excel_file.sheet_names
            
            # Let the user choose which sheet to load
            selected_sheet = st.sidebar.selectbox("Select Excel Sheet", sheet_names)
            df_raw = pd.read_excel(file, sheet_name=selected_sheet)
            st.sidebar.success(f"Loaded sheet: '{selected_sheet}'")

if df_raw is not None:
    st.sidebar.header("2. Map Columns")
    cols = list(df_raw.columns)
    
    def find_col(kws):
        for c in cols:
            if any(k in c.lower() for k in kws):
                return c
        return cols[0]

    date_c = st.sidebar.selectbox("Date", cols, index=cols.index(find_col(["date"])))
    prod_c = st.sidebar.selectbox("Product", cols, index=cols.index(find_col(["product", "item"])))
    qty_c = st.sidebar.selectbox("Quantity", cols, index=cols.index(find_col(["qty", "quantity"])))
    sales_c = st.sidebar.selectbox("Sales Revenue", cols, index=cols.index(find_col(["sale", "revenue"])))
    cost_c = st.sidebar.selectbox("Cost", cols, index=cols.index(find_col(["cost"])))

    mapping = {"date": date_c, "product": prod_c, "quantity": qty_c, "sales": sales_c, "cost": cost_c}

    try:
        df = validate_and_process_data(df_raw, mapping)
        kpis = compute_kpis(df)

        # Main KPI Metrics
        st.markdown("### Key Metrics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Revenue", f"₹{kpis['sales']:,.2f}")
        c2.metric("Total Cost", f"₹{kpis['cost']:,.2f}")
        c3.metric("Gross Profit", f"₹{kpis['profit']:,.2f}")
        c4.metric("Overall Margin", f"{kpis['margin']}%")

        st.markdown("---")

        # Charts Section
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("Top Products by Profit")
            prod_summary = df.groupby("Product")["Gross_Profit"].sum().reset_index()
            prod_summary = prod_summary.sort_values(by="Gross_Profit", ascending=True).tail(10)
            fig = px.bar(prod_summary, x="Gross_Profit", y="Product", orientation="h")
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.subheader("Monthly Revenue Trend")
            monthly = df.groupby("Month")["Sales"].sum().reset_index()
            fig2 = px.line(monthly, x="Month", y="Sales", markers=True)
            st.plotly_chart(fig2, use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("👈 Choose Demo Data or upload your Excel file in the sidebar to get started.")

