import streamlit as st
import pandas as pd
import plotly.express as px
from docx import Document
from io import BytesIO
from datetime import datetime

st.set_page_config(
    page_title="Zaghloula Smart Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------
# Custom CSS
# ---------------------------
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
</style>
""", unsafe_allow_html=True)


# ---------------------------
# Word Report
# ---------------------------
def create_word_report(data, total_sales, total_profit, branch):
    doc = Document()

    doc.add_heading(f'تقرير مبيعات - {branch}', 0)
    doc.add_paragraph(f'تاريخ التقرير: {datetime.now().strftime("%Y-%m-%d")}')

    doc.add_heading('الملخص المالي', level=1)
    doc.add_paragraph(f'إجمالي المبيعات: {total_sales:,.2f} جنيه')
    doc.add_paragraph(f'صافي الأرباح: {total_profit:,.2f} جنيه')

    doc.add_heading('أفضل الأصناف', level=1)

    table = doc.add_table(rows=1, cols=3)
    table.style = 'Table Grid'

    hdr = table.rows[0].cells
    hdr[0].text = 'الصنف'
    hdr[1].text = 'المبيعات'
    hdr[2].text = 'الربح'

    for _, row in data.head(10).iterrows():
        cells = table.add_row().cells
        cells[0].text = str(row['الصنف'])
        cells[1].text = f"{row['Total_Sales']:,.2f}"
        cells[2].text = f"{row['Net_Profit']:,.2f}"

    file = BytesIO()
    doc.save(file)
    return file.getvalue()


# ---------------------------
# Load Data
# ---------------------------
@st.cache_data
def load_data(file):
    try:
        df = pd.read_csv(file, encoding="cp1256")
    except:
        df = pd.read_excel(file)

    required = ['الصنف', 'الكمية', 'السعر', 'س شراء', 'الكمية المتبقية']
    missing = [c for c in required if c not in df.columns]

    if missing:
        st.error(f"أعمدة ناقصة: {missing}")
        st.stop()

    branch = (
        df['الفرع'].dropna().iloc[0]
        if 'الفرع' in df.columns
        else "الفرع الرئيسي"
    )

    if 'رقم الفاتورة' in df.columns:
        df = df.dropna(subset=['رقم الفاتورة'])

    df = df.copy()

    for col in required[1:]:
        df[col] = pd.to_numeric(
            df[col].astype(str)
            .str.replace('×', '')
            .str.replace('x', '')
            .str.strip(),
            errors='coerce'
        ).fillna(0)

    df['Total_Sales'] = df['الكمية'] * df['السعر']
    df['Net_Profit'] = df['الكمية'] * (df['السعر'] - df['س شراء'])

    return df, branch


# ---------------------------
# Sidebar
# ---------------------------
with st.sidebar:
    st.title("🛒 زغلولة")
    st.markdown("### Smart Sales Dashboard")
    uploaded_file = st.file_uploader(
        "ارفع ملف المبيعات",
        type=["csv", "xls", "xlsx"]
    )


# ---------------------------
# Main App
# ---------------------------
st.title("📊 نظام تحليل مبيعات زغلولة")

if uploaded_file:
    data, branch = load_data(uploaded_file)

    # Filter
    product_filter = st.selectbox(
        "فلترة حسب الصنف",
        ["الكل"] + list(data['الصنف'].unique())
    )

    if product_filter != "الكل":
        data = data[data['الصنف'] == product_filter]

    total_sales = data['Total_Sales'].sum()
    total_profit = data['Net_Profit'].sum()
    low_stock = data[data['الكمية المتبقية'] <= 5]

    best_product = data.groupby('الصنف')['Net_Profit'].sum().idxmax()

    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "📊 Dashboard",
        "📦 Inventory",
        "📝 Reports"
    ])

    # ---------------- Dashboard
    with tab1:
        st.subheader(f"📍 الفرع: {branch}")

        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown(f"""
            <div class="card">
            <h2>إجمالي المبيعات</h2>
            <h1>{total_sales:,.0f} ج.م</h1>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="card">
            <h2>صافي الأرباح</h2>
            <h1>{total_profit:,.0f} ج.م</h1>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div class="card">
            <h2>الأصناف الناقصة</h2>
            <h1>{len(low_stock)}</h1>
            </div>
            """, unsafe_allow_html=True)

        st.success(f"🔥 أكثر صنف ربحية اليوم: {best_product}")

        col1, col2 = st.columns(2)

        with col1:
            top_profit = (
                data.groupby('الصنف')['Net_Profit']
                .sum()
                .sort_values(ascending=False)
                .head(10)
                .reset_index()
            )

            fig1 = px.bar(
                top_profit,
                x='Net_Profit',
                y='الصنف',
                orientation='h',
                title='أعلى الأصناف ربحية'
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            fig2 = px.treemap(
                data,
                path=['الصنف'],
                values='Total_Sales',
                title='خريطة المبيعات'
            )
            st.plotly_chart(fig2, use_container_width=True)

    # ---------------- Inventory
    with tab2:
        st.subheader("📦 إدارة المخزون")

        if len(low_stock) > 0:
            st.warning("يوجد أصناف تحتاج إعادة طلب")

        st.dataframe(
            low_stock[['الصنف', 'الكمية المتبقية']].drop_duplicates(),
            use_container_width=True
        )

    # ---------------- Reports
    with tab3:
        st.subheader("📝 التقارير")

        word_file = create_word_report(
            data,
            total_sales,
            total_profit,
            branch
        )

        st.download_button(
            "📥 تحميل تقرير Word",
            data=word_file,
            file_name=f"تقرير_زغلولة_{datetime.now().strftime('%Y%m%d')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

else:
    st.info("ارفع ملف مبيعات للبدء")
