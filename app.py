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

overview_tab, insights_tab, product_tab = st.tabs(
    ["نظرة عامة", "الاكتشافات", "المنتج"]
)

with overview_tab:
    st.write("استخدمي الفلاتر الجانبية لتغيير المنطقة والفئة وأقصى خصم.")

    if filtered.empty:
        st.info("ما فيه بيانات للفلاتر الحالية. غيّري الاختيارات.")
    else:
        sales = filtered["Sales"].sum()
        profit = filtered["Profit"].sum()
        margin = f"{100 * profit / sales:.2f}%" if sales else "—"
        order_count = filtered["Order ID"].nunique()

        sales_col, profit_col, margin_col, orders_col = st.columns(4)
        sales_col.metric("إجمالي المبيعات", f"${sales:,.2f}")
        profit_col.metric("إجمالي الربح", f"${profit:,.2f}")
        margin_col.metric("هامش الربح", margin)
        orders_col.metric("عدد الطلبات", f"{order_count:,}")

with insights_tab:
    if filtered.empty:
        st.info("غيّري الفلاتر الجانبية لعرض الرسومات.")
    else:
        st.subheader("ربح أعلى ١٠ منتجات حسب المبيعات")
        products = filtered.groupby("Product Name")[["Sales", "Profit"]].sum()
        top_products = products.nlargest(10, "Sales")

        if not top_products.empty:
            st.bar_chart(top_products["Profit"], x_label="المنتج", y_label="الربح ($)")
            best_product = top_products["Profit"].idxmax()
            best_profit = top_products.loc[best_product, "Profit"]
            st.caption(
                f"أعلى ربح ضمن المنتجات المعروضة كان لمنتج {best_product} "
                f"بقيمة ${best_profit:,.2f}."
            )

        st.subheader("هامش الربح حسب الخصم")
        discounts = filtered.groupby("Discount")[["Sales", "Profit"]].sum()
        discounts = discounts.loc[discounts["Sales"] != 0].copy()
        discounts["Margin (%)"] = 100 * discounts["Profit"] / discounts["Sales"]

        if not discounts.empty:
            st.bar_chart(
                discounts.reset_index(),
                x="Discount",
                y="Margin (%)",
                x_label="الخصم (٠ إلى ١)",
                y_label="هامش الربح (%)",
            )
            lowest_discount = discounts["Margin (%)"].idxmin()
            lowest_margin = discounts.loc[lowest_discount, "Margin (%)"]
            st.caption(
                f"أقل هامش ربح كان {lowest_margin:.2f}% "
                f"عند خصم {lowest_discount:.0%}."
            )

        st.subheader("هامش الربح حسب المنطقة")
        regional = filtered.groupby("Region")[["Sales", "Profit"]].sum()
        regional = regional.loc[regional["Sales"] != 0].copy()
        regional["Margin (%)"] = 100 * regional["Profit"] / regional["Sales"]

        if not regional.empty:
            st.bar_chart(regional["Margin (%)"], x_label="المنطقة", y_label="هامش الربح (%)")
            best_region = regional["Margin (%)"].idxmax()
            best_margin = regional.loc[best_region, "Margin (%)"]
            st.caption(f"أعلى هامش ربح كان في منطقة {best_region} بنسبة {best_margin:.2f}%.")

        st.subheader("أهم الاكتشافات والتوصيات")
        if not discounts.empty:
            st.write(
                f"ضمن الفلاتر الحالية، سجّل خصم {lowest_discount:.0%} أقل هامش ربح. "
                "راجعي ربح الفئة عند هذا الخصم قبل استخدامه في عرض جديد."
            )
        if not regional.empty:
            st.write(
                f"منطقة {best_region} حققت أعلى هامش ضمن الاختيارات الحالية. "
                "قارني فئات المنتجات فيها قبل تحديد المنتجات اللي تركزين عليها."
            )

with product_tab:
    st.subheader("فحص الربح حسب الخصم")
    st.write(
        "اختاري الفئة ونطاق الخصم لعرض ربح سجلات مشابهة من بيانات المتجر. "
        "الأداة تستخدم بيانات المتجر كاملة."
    )

    category = st.selectbox("فئة المنتج", categories, key="product_category")
    min_rate, max_rate = st.slider("نطاق الخصم (%)", 0, 100, (0, 20))

    similar_profits = data.loc[
        data["Category"].eq(category)
        & data["Discount"].between(min_rate / 100, max_rate / 100),
        "Profit",
    ].dropna()

    if similar_profits.empty:
        st.info("ما فيه سجلات مطابقة. جرّبي توسّعين نطاق الخصم أو تغيّرين الفئة.")
    else:
        median_col, count_col = st.columns(2)
        median_col.metric("وسيط الربح لكل سجل", f"${similar_profits.median():,.2f}")
        count_col.metric("عدد السجلات المشابهة", f"{len(similar_profits):,}")
        st.caption(
            "حسبنا الوسيط بعد اختيار السجلات اللي تطابق الفئة ونطاق الخصم. "
            "الوسيط هو القيمة اللي تقع في منتصف قيم الربح بعد ترتيبها."
        )
