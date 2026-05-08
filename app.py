import streamlit as st
import pandas as pd
import plotly.express as px
from docx import Document
from io import BytesIO
from datetime import datetime

# إعداد الصفحة
st.set_page_config(page_title="Zaghloula Smart Dashboard", layout="wide")

# CSS لتنسيق الكروت
st.markdown("""
<style>
.main { background-color: #f8f9fa; }
.card { padding: 20px; border-radius: 15px; background: white; box-shadow: 0 4px 12px rgba(0,0,0,0.08); text-align: center; }
.card h2 { color: #2c3e50; font-size: 18px; }
.card h1 { color: #27ae60; font-size: 24px; }
</style>
""", unsafe_allow_html=True)

def create_word_report(data, total_sales, total_profit):
    doc = Document()
    doc.add_heading("تقرير مبيعات زغلولة", 0)
    doc.add_paragraph(f"إجمالي المبيعات: {total_sales:,.2f}")
    doc.add_paragraph(f"صافي الأرباح: {total_profit:,.2f}")
    file = BytesIO()
    doc.save(file)
    return file.getvalue()

@st.cache_data
def load_data(file):
    try:
        df = pd.read_excel(file)
    except:
        df = pd.read_csv(file, encoding='utf-8-sig')
    
    # تنظيف أسماء الأعمدة من المسافات
    df.columns = [str(c).strip() for c in df.columns]
    
    # فلترة الصفوف الوهمية (مثل كلمة بيع أو إجمالي)
    if 'صنف' in df.columns:
        df = df.dropna(subset=['صنف'])
        df = df[~df['صنف'].astype(str).str.contains("بيع|إجمالي|اجمالى", na=False)]
    
    # تحويل الأعمدة لأرقام بناءً على أسماء ملفك الحقيقية
    cols = {'قيمة': 'قيمة', 'إجمالي ربح': 'إجمالي ربح', 'الرصيد الحالي': 'الرصيد الحالي'}
    for c in cols.values():
        if c in df.columns:
            df[c] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            
    return df

with st.sidebar:
    st.title("🛒 زغلولة")
    uploaded_file = st.file_uploader("ارفع ملف المبيعات", type=["csv", "xls", "xlsx"])

if uploaded_file:
    data = load_data(uploaded_file)
    
    # استخدام الأسماء الصحيحة من ملفك
    t_sales = data['قيمة'].sum() if 'قيمة' in data.columns else 0
    t_profit = data['إجمالي ربح'].sum() if 'إجمالي ربح' in data.columns else 0
    low_stock = data[data['الرصيد الحالي'] < 1] if 'الرصيد الحالي' in data.columns else pd.DataFrame()

    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📦 النواقص", "📝 تقرير"])

    with tab1:
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="card"><h2>إجمالي المبيعات</h2><h1>{t_sales:,.2f} ج.م</h1></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="card"><h2>صافي الأرباح</h2><h1>{t_profit:,.2f} ج.م</h1></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="card"><h2>أصناف ناقصة</h2><h1>{len(low_stock)}</h1></div>', unsafe_allow_html=True)
        
        if 'صنف' in data.columns:
            top_10 = data.groupby('صنف')['إجمالي ربح'].sum().sort_values(ascending=False).head(10).reset_index()
            fig = px.bar(top_10, x='إجمالي ربح', y='صنف', orientation='h', title="أعلى 10 أصناف ربحية")
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.dataframe(low_stock[['صنف', 'الرصيد الحالي']], use_container_width=True)

    with tab3:
        if st.button("تحميل تقرير Word"):
            word_file = create_word_report(data, t_sales, t_profit)
            st.download_button("📥 اضغط للتحميل", data=word_file, file_name="تقرير_زغلولة.docx")

    st.markdown("---")
    st.markdown('<div style="text-align: center; color: gray;">تطوير المهندس محمد جمال | 01029796096</div>', unsafe_allow_html=True)
else:
    st.info("ارفع ملف مبيعات السبت يا هندسة")
