import streamlit as st
import pandas as pd
import plotly.express as px
from docx import Document
from io import BytesIO
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="داشبورد زغلولة الذكية", layout="wide")

# -------------------------------
# إنشاء تقرير Word
# -------------------------------
def create_word_report(data, total_sales, total_profit, branch):
    doc = Document()

    doc.add_heading(f'تقرير مبيعات - {branch}', 0)
    doc.add_paragraph(f'تاريخ التقرير: {datetime.now().strftime("%Y-%m-%d")}')

    doc.add_heading('الملخص المالي', level=1)
    doc.add_paragraph(f'إجمالي المبيعات: {total_sales:,.2f} جنيه')
    doc.add_paragraph(f'صافي الربح: {total_profit:,.2f} جنيه')

    doc.add_heading('أعلى الأصناف مبيعًا', level=1)

    table = doc.add_table(rows=1, cols=3)
    table.style = 'Table Grid'

    headers = table.rows[0].cells
    headers[0].text = 'الصنف'
    headers[1].text = 'المبيعات'
    headers[2].text = 'الربح'

    for _, row in data.head(15).iterrows():
        row_cells = table.add_row().cells
        row_cells[0].text = str(row['الصنف'])
        row_cells[1].text = f"{row['Total_Sales']:,.2f}"
        row_cells[2].text = f"{row['Net_Profit']:,.2f}"

    file = BytesIO()
    doc.save(file)
    return file.getvalue()


# -------------------------------
# قراءة وتنظيف البيانات
# -------------------------------
@st.cache_data
def load_and_clean(file):
    try:
        df = pd.read_csv(file, encoding='cp1256')
    except:
        df = pd.read_excel(file)

    required_cols = [
        'الصنف',
        'الكمية',
        'السعر',
        'س شراء',
        'الكمية المتبقية'
    ]

    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        st.error(f"الأعمدة الناقصة في الملف: {missing}")
        st.stop()

    branch = (
        df['الفرع'].dropna().iloc[0]
        if 'الفرع' in df.columns
        else "الفرع الرئيسي"
    )

    if 'رقم الفاتورة' in df.columns:
        df = df.dropna(subset=['رقم الفاتورة'])

    df = df.copy()
    df = df[~df['الصنف'].astype(str).str.contains('اجمالى|وارد', na=False)]

    numeric_cols = ['الكمية', 'السعر', 'س شراء', 'الكمية المتبقية']
    for col in numeric_cols:
        df[col] = pd.to_numeric(
            df[col].astype(str)
            .str.replace('×', '')
            .str.replace('x', '')
            .str.strip(),
            errors='coerce'
        ).fillna(0)

    # الحسابات الصحيحة
    df['Total_Sales'] = df['الكمية'] * df['السعر']
    df['Net_Profit'] = (
        df['الكمية'] * (df['السعر'] - df['س شراء'])
    )

    return df, branch


# -------------------------------
# الواجهة الرئيسية
# -------------------------------
st.title("📊 نظام تحليل مبيعات زغلولة اليومي")
st.markdown("---")

uploaded_file = st.file_uploader(
    "ارفع ملف المبيعات",
    type=["csv", "xls", "xlsx"]
)

if uploaded_file:
    data, branch = load_and_clean(uploaded_file)

    total_sales = data['Total_Sales'].sum()
    total_profit = data['Net_Profit'].sum()

    low_stock = data[data['الكمية المتبقية'] <= 5]

    st.subheader(f"📍 الفرع: {branch}")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "💰 إجمالي المبيعات",
        f"{total_sales:,.2f} ج.م"
    )

    col2.metric(
        "📈 صافي الأرباح",
        f"{total_profit:,.2f} ج.م"
    )

    col3.metric(
        "🚨 أصناف ناقصة",
        len(low_stock['الصنف'].unique())
    )

    if len(low_stock) > 0:
        st.warning("يوجد أصناف تحتاج إعادة طلب سريع")

    # تحميل تقرير Word
    st.markdown("### 📥 تحميل التقرير")

    word_file = create_word_report(
        data,
        total_sales,
        total_profit,
        branch
    )

    st.download_button(
        label="📝 تحميل التقرير Word",
        data=word_file,
        file_name=f"تقرير_زغلولة_{datetime.now().strftime('%Y%m%d')}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    # الرسوم البيانية
    st.markdown("## 📊 التحليلات")

    c1, c2 = st.columns(2)

    with c1:
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
            title="أعلى 10 أصناف ربحية"
        )
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        top_sales = (
            data.groupby('الصنف')['Total_Sales']
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )

        fig2 = px.bar(
            top_sales,
            x='Total_Sales',
            y='الصنف',
            orientation='h',
            title="أعلى 10 أصناف مبيعًا"
        )
        st.plotly_chart(fig2, use_container_width=True)

    # جدول النواقص
    st.markdown("## 🛒 قائمة النواقص")

    st.dataframe(
        low_stock[['الصنف', 'الكمية المتبقية']].drop_duplicates(),
        use_container_width=True
    )
