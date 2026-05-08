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
# CSS (تنسيق الكروت والـ UI)
# ---------------------------------------------------
st.markdown("""
<style>
.main { background-color: #f8f9fa; }
.card {
    padding: 20px;
    border-radius: 15px;
    background: white;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    text-align: center;
    margin-bottom: 10px;
}
.card h2 { color: #2c3e50; font-size: 18px; margin-bottom: 10px; }
.card h1 { color: #27ae60; font-size: 24px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# تقرير Word
# ---------------------------------------------------
def create_word_report(data, total_sales, total_profit, branch):
    doc = Document()
    doc.add_heading(f"تقرير مبيعات - {branch}", 0)
    doc.add_paragraph(f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d')}")
    
    doc.add_heading("الملخص المالي", level=1)
    doc.add_paragraph(f"إجمالي المبيعات: {total_sales:,.2f} جنيه")
    doc.add_paragraph(f"صافي الأرباح: {total_profit:,.2f} جنيه")

    top_products = data.groupby('الصنف')['Net_Profit'].sum().sort_values(ascending=False).head(10).reset_index()

    doc.add_heading("أفضل 10 أصناف من حيث الربح", level=1)
    table = doc.add_table(rows=1, cols=2)
    table.style = "Table Grid"
    headers = table.rows[0].cells
    headers[0].text = "الصنف"
    headers[1].text = "صافي الربح"

    for _, row in top_products.iterrows():
        cells = table.add_row().cells
        cells[0].text = str(row["الصنف"])
        cells[1].text = f"{row['Net_Profit']:,.2f}"

    file = BytesIO()
    doc.save(file)
    return file.getvalue()

# ---------------------------------------------------
# قراءة وتنظيف البيانات
# ---------------------------------------------------
@st.cache_data
def load_data(file):
    # محاولة القراءة بأكثر من ترميز لتجنب مشاكل اللغة العربية
    try:
        df = pd.read_excel(file)
    except:
        try:
            df = pd.read_csv(file, encoding='utf-8-sig')
        except:
            df = pd.read_csv(file, encoding='cp1256')
    
    df.columns = [str(c).strip() for c in df.columns]
    
    # تحديد الفرع
    branch = df["الفرع"].iloc[0] if "الفرع" in df.columns else "الفرع الرئيسي"
    
    # تنظيف الصفوف الوهمية (مثل كلمة بيع أو إجمالي)
    unwanted = ["وارد", "اجمالى", "بيع نقدي", "إجمالي"]
    df = df.dropna(subset=['الصنف'])
    df = df[~df['الصنف'].astype(str).str.contains("|".join(unwanted), na=False)]
    
    # تحويل الأعمدة لأرقام
    numeric_map = {
        'الكمية': 'الكمية',
        'السعر': 'السعر',
        'س شراء': 'س شراء',
        'الكمية المتبقية': 'الكمية المتبقية'
    }
    
    for col in numeric_map.values():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # معادلة الحساب الصحيحة
    if 'الكمية' in df.columns and 'السعر' in df.columns:
        df['Total_Sales'] = df['الكمية'] * df['السعر']
    else:
        df['Total_Sales'] = 0

    if 'س شراء' in df.columns:
        # الربح = (سعر البيع - سعر الشراء) * الكمية
        df['Net_Profit'] = (df['السعر'] - df['س شراء']) * df['الكمية']
    else:
        df['Net_Profit'] = 0
        
    return df, branch

# ---------------------------------------------------
# Sidebar
# ---------------------------------------------------
with st.sidebar:
    st.title("🛒 زغلولة")
    uploaded_file = st.file_uploader("ارفع ملف المبيعات", type=["csv", "xls", "xlsx"])

# ---------------------------------------------------
# Main App
# ---------------------------------------------------
st.title("📊 نظام تحليل مبيعات زغلولة")

if uploaded_file:
    data, branch = load_data(uploaded_file)
    
    selected_product = st.selectbox("بحث عن صنف محدد", ["الكل"] + sorted(list(data["الصنف"].unique())))
    
    filtered_data = data.copy()
    if selected_product != "الكل":
        filtered_data = filtered_data[filtered_data["الصنف"] == selected_product]

    # الحسابات
    total_sales = filtered_data["Total_Sales"].sum()
    total_profit = filtered_data["Net_Profit"].sum()
    
    # تنبيهات المخزن
    low_stock_col = "الكمية المتبقية" if "الكمية المتبقية" in data.columns else None
    low_stock = filtered_data[filtered_data[low_stock_col] <= 5] if low_stock_col else pd.DataFrame()

    tab1, tab2, tab3, tab4 = st.tabs(["📊 لوحة التحكم", "📦 المخزن", "⚠️ تنبيهات", "📝 التقارير"])

    with tab1:
        st.subheader(f"📍 فرع: {branch}")
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="card"><h2>إجمالي المبيعات</h2><h1>{total_sales:,.2f} ج.م</h1></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="card"><h2>صافي الأرباح</h2><h1>{total_profit:,.2f} ج.م</h1></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="card"><h2>أصناف قاربت للنفاد</h2><h1>{len(low_stock)}</h1></div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            top_profit = filtered_data.groupby("الصنف")["Net_Profit"].sum().sort_values(ascending=False).head(10).reset_index()
            fig1 = px.bar(top_profit, x="Net_Profit", y="الصنف", orientation="h", title="الأصناف الأكثر ربحية")
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.pie(filtered_data.head(20), values="Total_Sales", names="الصنف", title="توزيع مبيعات أعلى الأصناف")
            st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        st.subheader("📦 حالة المخزن الحالية")
        if low_stock_col:
            st.dataframe(filtered_data[["الصنف", low_stock_col]].drop_duplicates(), use_container_width=True)
        else:
            st.info("عمود 'الكمية المتبقية' غير موجود في الملف")

    with tab3:
        st.subheader("⚠️ أصناف تحتاج مراجعة")
        at_loss = filtered_data[filtered_data['Net_Profit'] < 0]
        if not at_loss.empty:
            st.error(f"يوجد {len(at_loss)} أصناف تباع بخسارة!")
            st.dataframe(at_loss[['الصنف', 'السعر', 'س شراء', 'Net_Profit']])
        else:
            st.success("لا توجد أصناف تباع بخسارة حالياً.")

    with tab4:
        st.subheader("📝 استخراج التقارير")
        if st.button("توليد تقرير Word"):
            word_file = create_word_report(filtered_data, total_sales, total_profit, branch)
            st.download_button("📥 تحميل التقرير", data=word_file, file_name=f"تقرير_مبيعات_{branch}.docx")

    # التوقيع
    st.markdown("---")
    st.markdown('<div style="text-align: center; color: #7f8c8d;">تطوير المهندس محمد جمال | 01029796096</div>', unsafe_allow_html=True)

else:
    st.info("الرجاء رفع ملف المبيعات (Excel أو CSV) للبدء في التحليل")
