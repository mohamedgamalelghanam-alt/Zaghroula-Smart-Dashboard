import streamlit as st
import pandas as pd
import plotly.express as px

# 1. إعداد الصفحة
st.set_page_config(page_title="Zaghloula Dashboard", layout="wide")

# 2. دالة المعالجة
@st.cache_data
def load_data(file):
    try:
        df = pd.read_excel(file)
    except:
        df = pd.read_csv(file, encoding='cp1256')
    
    df.columns = [str(c).strip() for c in df.columns]
    
    if 'صنف' in df.columns:
        df = df.dropna(subset=['صنف'])
        df = df[~df['صنف'].astype(str).str.contains('بيع|إجمالي', na=False)]
    
    # تحويل الأرقام
    for c in ['كمية', 'قيمة', 'إجمالي ربح', 'الرصيد الحالي']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    
    return df

# 3. الواجهة
st.title("📊 Zaghloula Smart Dashboard")

file = st.sidebar.file_uploader("ارفع ملف السبت", type=["xlsx", "xls", "csv"])

if file:
    df = load_data(file)
    
    # حسابات سريعة
    sales = df['قيمة'].sum() if 'قيمة' in df.columns else 0
    profit = df['إجمالي ربح'].sum() if 'إجمالي ربح' in df.columns else 0
    
    col1, col2 = st.columns(2)
    col1.metric("💰 إجمالي المبيعات", f"{sales:,.2f} ج.م")
    col2.metric("📈 صافي الأرباح", f"{profit:,.2f} ج.م")
    
    # الرسم البياني
    if 'صنف' in df.columns:
        st.subheader("🚀 الأصناف الأكثر ربحية")
        top = df.groupby('صنف')['إجمالي ربح'].sum().sort_values(ascending=False).head(10).reset_index()
        fig = px.bar(top, x='إجمالي ربح', y='صنف', orientation='h', color='إجمالي ربح')
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("ارفع ملف مبيعات السبت يا هندسة عشان نطلع الأرباح")
