import streamlit as st
import pandas as pd
import plotly.express as px
import os
from engine import validate_and_process_data, compute_kpis
from generate_sample_data import generate_data

st.set_page_config(page_title="MarginLens", page_icon="📊", layout="wide")

st.title("📊 MarginLens")
st.markdown("**Multi-Sheet & Custom Range Sales Analyzer**")

# Sidebar
st.sidebar.header("1. Data Source")
data_option = st.sidebar.radio("Select source:", ["Use Demo Data", "Upload Excel / CSV"])

df_raw = None
if data_option == "Use Demo Data":
    if not os.path.exists("sample_sales_data.csv"):
        generate_data("sample_sales_data.csv")
    df_raw = pd.read_csv("sample_sales_data.csv")
    st.sidebar.success("Loaded demo data (500 rows)")
else:
    file = st.sidebar.file_uploader("Upload Excel or CSV", type=["csv", "xlsx"])
    if file:
        if file.name.endswith(".csv"):
            df_raw = pd.read_csv(file)
            st.sidebar.success(f"Loaded CSV: {file.name}")
        else:
            excel_file = pd.ExcelFile(file)
            sheet_names = excel_file.sheet_names
            
            # Multi-sheet selector
            selected_sheet = st.sidebar.selectbox("Select Excel Sheet", sheet_names)
            
            # Optional Header row customization
            header_row = st.sidebar.number_input("Header Row Index (0 for first row)", min_value=0, value=0, step=1)
            
            df_raw = pd.read_excel(file, sheet_name=selected_sheet, header=header_row)
            st.sidebar.success(f"Loaded sheet: '{selected_sheet}'")

if df_raw is not None:
    # Row Range Selector
    st.sidebar.header("2. Specify Row Range")
    total_rows = len(df_raw)
    row_range = st.sidebar.slider(
        "Select Row Range to Analyze",
        min_value=1,
        max_value=max(1, total_rows),
        value=(1, total_rows)
    )
    
    # Slice dataframe based on selected range
    start_idx, end_idx = row_range
    df_sliced = df_raw.iloc[start_idx-1:end_idx].copy()

    with st.expander(f"📋 Preview Table Data (Rows {start_idx} to {end_idx})", expanded=True):
        st.dataframe(df_sliced.head(10), use_container_width=True)

    st.sidebar.header("3. Map Table Headers")
    cols = list(df_sliced.columns)
    
    def find_col(kws):
        for c in cols:
            if any(k in str(c).lower() for k in kws):
                return c
        return cols[0]

    date_c = st.sidebar.selectbox("Date Column", cols, index=cols.index(find_col(["date"])))
    prod_c = st.sidebar.selectbox("Product Column", cols, index=cols.index(find_col(["product", "item"])))
    qty_c = st.sidebar.selectbox("Quantity Column", cols, index=cols.index(find_col(["qty", "quantity"])))
    sales_c = st.sidebar.selectbox("Sales Revenue Column", cols, index=cols.index(find_col(["sale", "revenue"])))
    cost_c = st.sidebar.selectbox("Cost Column", cols, index=cols.index(find_col(["cost"])))

    mapping = {
        "date": date_c, 
        "product": prod_c, 
        "quantity": qty_c, 
        "sales": sales_c, 
        "cost": cost_c
    }

    try:
        df = validate_and_process_data(df_sliced, mapping)
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
        st.error(f"Error processing data range: {e}")
else:
    st.info("👈 Choose Demo Data or upload your multi-sheet Excel file in the sidebar to get started.")
