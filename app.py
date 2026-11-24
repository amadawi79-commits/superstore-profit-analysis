from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="تحليل أرباح المبيعات", layout="wide")
st.title("لوحة تحليل أرباح المبيعات")


@st.cache_data
def load_data():
    csv_path = Path(__file__).resolve().parent / "data" / "clean.csv"
    return pd.read_csv(csv_path)


try:
    data = load_data()
except FileNotFoundError:
    st.error("ضعي clean.csv داخل مجلد data بجانب ملف app.py.")
    st.stop()

st.sidebar.header("الفلاتر")

regions = sorted(data["Region"].dropna().unique())
categories = sorted(data["Category"].dropna().unique())

selected_regions = st.sidebar.multiselect("المنطقة", regions, default=regions)
selected_categories = st.sidebar.multiselect("الفئة", categories, default=categories)
max_discount = st.sidebar.slider("أقصى خصم (%)", 0, 100, 100)

filtered = data[
    data["Region"].isin(selected_regions)
    & data["Category"].isin(selected_categories)
    & (data["Discount"] <= max_discount / 100)
]

sales = filtered["Sales"].sum()
profit = filtered["Profit"].sum()
margin = f"{100 * profit / sales:.2f}%" if sales else "—"

sales_col, profit_col, margin_col, orders_col = st.columns(4)
sales_col.metric("إجمالي المبيعات", f"${sales:,.2f}")
profit_col.metric("إجمالي الربح", f"${profit:,.2f}")
margin_col.metric("هامش الربح", margin)
orders_col.metric("عدد الطلبات", f'{filtered["Order ID"].nunique():,}')

if filtered.empty:
    st.info("ما فيه بيانات للفلاتر الحالية. غيّري الاختيارات لعرض الرسوم.")
    st.stop()

st.subheader("ربح أعلى 10 منتجات مبيعًا")
products = filtered.groupby("Product Name")[["Sales", "Profit"]].sum()
top_products = products.nlargest(10, "Sales")
st.bar_chart(top_products["Profit"], x_label="المنتج", y_label="الربح ($)")

st.subheader("هامش الربح حسب الخصم")
discounts = filtered.groupby("Discount")[["Sales", "Profit"]].sum()
discounts = discounts.loc[discounts["Sales"] != 0].copy()
discounts["Margin (%)"] = 100 * discounts["Profit"] / discounts["Sales"]
discounts.index = discounts.index.map(lambda rate: f"{rate:.0%}")
st.bar_chart(discounts["Margin (%)"], x_label="الخصم", y_label="هامش الربح (%)")

st.subheader("هامش الربح حسب المنطقة")
regional = filtered.groupby("Region")[["Sales", "Profit"]].sum()
regional = regional.loc[regional["Sales"] != 0].copy()
regional["Margin (%)"] = 100 * regional["Profit"] / regional["Sales"]
st.bar_chart(regional["Margin (%)"], x_label="المنطقة", y_label="هامش الربح (%)")
