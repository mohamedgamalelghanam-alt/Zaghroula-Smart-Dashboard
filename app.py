import streamlit as st
import pandas as pd
import plotly.express as px
from docx import Document
from io import BytesIO
from datetime import datetime

# ---------------------------------------------------
# إعداد الصفحة
# ---------------------------------------------------
st.set_page_config(
    page_title="Zaghloula Smart Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------
# CSS (تنسيق الكروت والـ Footer)
# ---------------------------------------------------
st.markdown("""
<style>
.main {
    background-color: #f8f9fa;
}

.card {
    padding: 20px;
    border-radius: 15px;
    background: white;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    text-align: center;
}

.card h2 {
    color: #2c3e50;
    font-size: 20px;
}

.card h1 {
    color: #27ae60;
    font-size: 28px;
}

.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: #2c3e50;
    color: white;
    text-align: center;
    padding: 10px;
    font-family: 'Arial';
    z-index: 1000;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# تقرير Word
# ---------------------------------------------------
def create_word_report(data, total_sales, total_profit, branch):
    doc = Document()

    doc.add_heading(f"تقرير مبيعات - {branch}", 0)
    doc.add_paragraph(
        f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d')}"
    )

    doc.add_heading("الملخص المالي", level=1)
    doc.add_paragraph(f"إجمالي المبيعات: {total_sales:,.2f} جنيه")
    doc.add_paragraph(f"صافي الأرباح: {total_profit:,.2f} جنيه")

    top_products = (
        data.groupby('الصنف')[['Total_Sales', 'Net_Profit']]
        .sum()
        .sort_values(by='Total_Sales', ascending=False)
        .head(10)
        .reset_index()
    )

    doc.add_heading("أفضل الأصناف", level=1)

    table = doc.add_table(rows=1, cols=3)
    table.style = "Table Grid"

    headers = table.rows[0].cells
    headers[0].text = "الصنف"
    headers[1].text = "المبيعات"
    headers[2].text = "الربح"

    for _, row in top_products.iterrows():
        cells = table.add_row().cells
        cells[0].text = str(row["الصنف"])
        cells[1].text = f"{row['Total_Sales']:,.2f}"
        cells[2].text = f"{row['Net_Profit']:,.2f}"

    file = BytesIO()
    doc.save(file)
    return file.getvalue()


# ---------------------------------------------------
# قراءة وتنظيف البيانات
# ---------------------------------------------------
@st.cache_data
def load_data(file):
    try:
        df = pd.read_csv(file, encoding='cp1256')
    except:
        df = pd.read_excel(file)

    df = df.copy()

    branch = (
        df["الفرع"].dropna().iloc[0]
        if "الفرع" in df.columns
        else "الفرع الرئيسي"
    )

    # تنظيف البيانات من "الوارد" و "الاجمالى"
    unwanted_words = ["وارد", "اجمالى", "بيع نقدي"]
    df = df.dropna(subset=['الصنف', 'الكمية', 'السعر', 'س شراء'])
    df = df[~df['الصنف'].astype(str).str.contains("|".join(unwanted_words), na=False)]

    # تحويل البيانات لأرقام
    numeric_cols = ["الكمية", "السعر", "س شراء", "الكمية المتبقية"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # الحسبة المنضبطة
    df['Total_Sales'] = df['الكمية'] * df['السعر']
    df['Net_Profit'] = df['Total_Sales'] - df['س شراء']
    
    # حساب نسبة الربح (لمعرفة الأصناف ضعيفة الربح)
    # الربح / التكلفة
    df['Profit_Margin_Pct'] = (df['Net_Profit'] / df['س شراء'].replace(0, 1)) * 100

    return df, branch


# ---------------------------------------------------
# Sidebar
# ---------------------------------------------------
with st.sidebar:
    st.title("🛒 زغلولة")
    st.markdown("### Smart Sales Dashboard")

    uploaded_file = st.file_uploader(
        "ارفع ملف المبيعات",
        type=["csv", "xls", "xlsx"]
    )


# ---------------------------------------------------
# Main App
# ---------------------------------------------------
st.title("📊 نظام تحليل مبيعات زغلولة")

if uploaded_file:
    data, branch = load_data(uploaded_file)

    selected_product = st.selectbox(
        "فلترة حسب الصنف",
        ["الكل"] + sorted(list(data["الصنف"].unique()))
    )

    filtered_data = data.copy()
    if selected_product != "الكل":
        filtered_data = filtered_data[filtered_data["الصنف"] == selected_product]

    total_sales = filtered_data["Total_Sales"].sum()
    total_profit = filtered_data["Net_Profit"].sum()
    low_stock = filtered_data[filtered_data["الكمية المتبقية"] <= 5]

    # الأصناف التي تباع بأقل من سعر الشراء أو ربحها ضعيف (أقل من 5%)
    at_loss = filtered_data[filtered_data['Net_Profit'] < 0]
    low_margin = filtered_data[(filtered_data['Net_Profit'] >= 0) & (filtered_data['Profit_Margin_Pct'] < 5)]

    best_product = (
        filtered_data.groupby("الصنف")["Net_Profit"]
        .sum()
        .idxmax()
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard",
        "📦 Inventory",
        "⚠️ الأصناف تحت المراجعة",
        "📝 Reports",
        "📘 دليل الاستخدام"
    ])

    # ---------------- Dashboard
    with tab1:
        st.subheader(f"📍 الفرع: {branch}")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="card"><h2>إجمالي المبيعات</h2><h1>{total_sales:,.2f} ج.م</h1></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="card"><h2>صافي الأرباح</h2><h1>{total_profit:,.2f} ج.م</h1></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="card"><h2>الأصناف الناقصة</h2><h1>{len(low_stock)}</h1></div>', unsafe_allow_html=True)

        st.success(f"🔥 أكثر صنف ربحية: {best_product}")

        col1, col2 = st.columns(2)
        with col1:
            top_profit = filtered_data.groupby("الصنف")["Net_Profit"].sum().sort_values(ascending=False).head(10).reset_index()
            fig1 = px.bar(top_profit, x="Net_Profit", y="الصنف", orientation="h", title="أعلى 10 أصناف ربحية")
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.treemap(filtered_data, path=["الصنف"], values="Total_Sales", title="خريطة المبيعات")
            st.plotly_chart(fig2, use_container_width=True)

    # ---------------- Inventory
    with tab2:
        st.subheader("📦 إدارة المخزون")
        if len(low_stock) > 0:
            st.warning("يوجد أصناف تحتاج إعادة طلب")
        st.dataframe(low_stock[["الصنف", "الكمية المتبقية"]].drop_duplicates(), use_container_width=True)

    # ---------------- ⚠️ الأصناف تحت المراجعة (السكشن الجديد)
    with tab3:
        st.subheader("⚠️ تحليل الأصناف الخاسرة وضعيفة الربح")
        
        col_loss, col_margin = st.columns(2)
        
        with col_loss:
            st.error(f"❌ أصناف تباع بخسارة ({len(at_loss)})")
            if not at_loss.empty:
                st.dataframe(at_loss[['الصنف', 'الكمية', 'السعر', 'س شراء', 'Net_Profit']], use_container_width=True)
            else:
                st.write("لا يوجد أصناف تباع بخسارة حالياً.")

        with col_margin:
            st.warning(f"📉 أصناف ربحها ضعيف - أقل من 5% ({len(low_margin)})")
            if not low_margin.empty:
                st.dataframe(low_margin[['الصنف', 'الكمية', 'السعر', 'س شراء', 'Net_Profit']], use_container_width=True)
            else:
                st.write("جميع الأصناف المتبقية ربحها جيد.")

    # ---------------- Reports
    with tab4:
        st.subheader("📝 التقارير")
        word_file = create_word_report(filtered_data, total_sales, total_profit, branch)
        st.download_button("📥 تحميل تقرير Word", data=word_file, file_name=f"تقرير_زغلولة_{datetime.now().strftime('%Y%m%d')}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    # ---------------- Guide
    with tab5:
        st.header("📘 دليل استخدام الداشبورد")
        st.markdown("""
        - **Dashboard:** ملخص المبيعات والأرباح.
        - **Inventory:** مراقبة النواقص.
        - **الأصناف تحت المراجعة:** عرض الأصناف اللي محتاجة مراجعة تسعير (خسارة أو ربح بسيط).
        """)

    # ---------------- التوقيع (التفخيم)
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; padding: 20px; background-color: #f1f3f5; border-radius: 10px; border-left: 5px solid #27ae60;">
            <h3 style="margin: 0; color: #2c3e50;">تم تطوير هذا النظام بواسطة</h3>
            <h2 style="margin: 10px 0; color: #27ae60;">المهندس محمد جمال</h2>
            <p style="margin: 5px 0; font-size: 18px;">📞 <b>01029796096</b></p>
        </div>
        """, unsafe_allow_html=True
    )

else:
    st.info("ارفع ملف مبيعات للبدء")
