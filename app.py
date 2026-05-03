import streamlit as st
import pandas as pd
from docx import Document
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="داشبورد زغلولة - النسخة المعتمدة", layout="wide")

st.title("📊 نظام تحليل مبيعات زغلولة")

uploaded_file = st.file_uploader("📥 ارفع تقرير اليوم (الذي يحتوي على س شراء)", type=['csv', 'xlsx'])

if uploaded_file:
    # قراءة الملف
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    except:
        df = pd.read_excel(uploaded_file)

    # تنظيف سريع
    df = df.dropna(subset=['الصنف'])
    
    # تحويل الأعمدة لأرقام (للتأكيد)
    for col in ['الكمية', 'السعر', 'س شراء']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # --- الحسبة المطابقة لسيستم المحل ---
    df['إجمالي_البيع'] = df['الكمية'] * df['السعر']
    df['صافي_الربح'] = df['إجمالي_البيع'] - df['س شراء']

    # إجمالي اليوم
    total_sales = df['إجمالي_البيع'].sum()
    total_profit = df['صافي_الربح'].sum()

    # العرض
    c1, c2 = st.columns(2)
    c1.metric("💰 إجمالي مبيعات اليوم", f"{total_sales:,.2f} ج.م")
    c2.metric("📈 صافي أرباح اليوم", f"{total_profit:,.2f} ج.م")

    st.markdown("---")
    st.subheader("📋 تفاصيل الأرباح لكل صنف")
    st.dataframe(df[['الصنف', 'الكمية', 'السعر', 'إجمالي_البيع', 'س شراء', 'صافي_الربح']])
