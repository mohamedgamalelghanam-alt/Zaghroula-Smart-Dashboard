import streamlit as st
import pandas as pd
import plotly.express as px
from docx import Document
from io import BytesIO
from datetime import datetime
import re

# إعدادات الصفحة - Dark Mode مريح وواضح
st.set_page_config(page_title="Zaghloula Dashboard", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .metric-card {
        background-color: #1a1c23; padding: 20px; border-radius: 12px;
        border: 1px solid #30363d; text-align: center; margin-bottom: 10px;
    }
    .sales-val { color: #2ecc71; font-size: 2.2rem; font-weight: bold; }
    .profit-val { color: #3498db; font-size: 2.2rem; font-weight: bold; }
    .warning-val { color: #e74c3c; font-size: 2.2rem; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

def create_word_report(data, t_sales, t_profit, branch):
    doc = Document()
    doc.add_heading(f'تقرير زغلولة - {branch}', 0)
    table = doc.add_table(rows=1, cols=3); table.style = 'Table Grid'
    hdr = table.rows[0].cells
    hdr[0].text, hdr[1].text, hdr[2].text = 'الصنف', 'المبيعات', 'الربح'
    for _, row in data.head(20).iterrows():
        c = table.add_row().cells
        c[0].text, c[1].text, c[2].text = str(row['الصنف']), f"{row.get('Total_Sales', 0):,.2f}", f"{row.get('Net_Profit', 0):,.2f}"
    target = BytesIO(); doc.save(target)
    return target.getvalue()

st.title("📊 نظام زغلولة لإدارة البيانات")

uploaded_file = st.sidebar.file_uploader("📂 ارفع ملف (Excel Workbook)", type=['xlsx', 'xls', 'csv'])

if uploaded_file:
    try:
        # قراءة الملف بذكاء
        if uploaded_file.name.endswith('csv'):
            try: df = pd.read_csv(uploaded_file, encoding='cp1256')
            except: df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
        else:
            df = pd.read_excel(uploaded_file)

        # تنظيف الداتا: مسح الصفوف الفاضية تماماً
        df = df.dropna(how='all').reset_index(drop=True)
        
        if df.empty:
            st.error("⚠️ الملف ده فاضي يا هندسة، تأكد إنك حفظت البيانات فيه.")
        else:
            # محاولة إيجاد الأعمدة بذكاء لو الأسامي متغيرة
            cols = df.columns.tolist()
            col_item = next((c for c in cols if 'صنف' in str(c)), cols[0])
            col_qty = next((c for c in cols if 'كمية' in str(c)), cols[min(1, len(cols)-1)])
            col_price = next((c for c in cols if 'سعر' in str(c)), cols[min(2, len(cols)-1)])
            col_stock = next((c for c in cols if 'متبقي' in str(c) or 'رصيد' in str(c)), None)

            # تنظيف الأرقام
            def to_num(x):
                try: return float(re.sub(r'[^\d.]', '', str(x)))
                except: return 0.0

            df['الصنف'] = df[col_item].astype(str)
            df['Qty'] = df[col_qty].apply(to_num)
            df['Price'] = df[col_price].apply(to_num)
            df['Stock'] = df[col_stock].apply(to_num) if col_stock else 10.0
            
            df['Total_Sales'] = df['Qty'] * df['Price']
            df['Net_Profit'] = df['Total_Sales'] * 0.25 # نسبة ربح تقديرية

            df_final = df[df['Total_Sales'] > 0].copy()
            branch = "فرع إيتاي"

            # العرض
            ts, tp = df_final['Total_Sales'].sum(), df_final['Net_Profit'].sum()
            low_stock = df_final[df_final['Stock'] <= 5]

            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f'<div class="metric-card"><h2>💰 مبيعات اليوم</h2><div class="sales-val">{ts:,.2f}</div></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="metric-card"><h2>📈 الأرباح التقديرية</h2><div class="profit-val">{tp:,.2f}</div></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="metric-card"><h2>🚨 نواقص المخزن</h2><div class="warning-val">{len(low_stock)}</div></div>', unsafe_allow_html=True)

            t1, t2 = st.tabs(["🛒 قائمة النواقص", "📊 التحليل"])
            with t1:
                st.subheader("📦 بضاعة لازم تطلبها")
                st.dataframe(low_stock[['الصنف', 'Stock']].rename(columns={'Stock': 'الرصيد'}), use_container_width=True)
            with t2:
                st.plotly_chart(px.bar(df_final.nlargest(10, 'Total_Sales'), x='Total_Sales', y='الصنف', orientation='h', template="plotly_dark"))

    except Exception as e:
        st.error(f"⚠️ حصلت مشكلة: {e}. جرب تحفظ الملف بصيغة Excel Workbook وارفعُه تاني.")
else:
    st.info("مستني ترفع ملف المبيعات يا هندسة..")
st.title("📊 نظام زغلولة لإدارة البيانات")

uploaded_file = st.sidebar.file_uploader("📂 ارفع ملف (Excel Workbook)", type=['xlsx', 'xls', 'csv'])

if uploaded_file:
    try:
        # قراءة الملف بذكاء
        if uploaded_file.name.endswith('csv'):
            try: df = pd.read_csv(uploaded_file, encoding='cp1256')
            except: df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
        else:
            df = pd.read_excel(uploaded_file)

        # تنظيف الداتا: مسح الصفوف الفاضية تماماً
        df = df.dropna(how='all').reset_index(drop=True)
        
        if df.empty:
            st.error("⚠️ الملف ده فاضي يا هندسة، تأكد إنك حفظت البيانات فيه.")
        else:
            # محاولة إيجاد الأعمدة بذكاء لو الأسامي متغيرة
            cols = df.columns.tolist()
            col_item = next((c for c in cols if 'صنف' in str(c)), cols[0])
            col_qty = next((c for c in cols if 'كمية' in str(c)), cols[min(1, len(cols)-1)])
            col_price = next((c for c in cols if 'سعر' in str(c)), cols[min(2, len(cols)-1)])
            col_stock = next((c for c in cols if 'متبقي' in str(c) or 'رصيد' in str(c)), None)

            # تنظيف الأرقام
            def to_num(x):
                try: return float(re.sub(r'[^\d.]', '', str(x)))
                except: return 0.0

            df['الصنف'] = df[col_item].astype(str)
            df['Qty'] = df[col_qty].apply(to_num)
            df['Price'] = df[col_price].apply(to_num)
            df['Stock'] = df[col_stock].apply(to_num) if col_stock else 10.0
            
            df['Total_Sales'] = df['Qty'] * df['Price']
            df['Net_Profit'] = df['Total_Sales'] * 0.25 # نسبة ربح تقديرية

            df_final = df[df['Total_Sales'] > 0].copy()
            branch = "فرع إيتاي"

            # العرض
            ts, tp = df_final['Total_Sales'].sum(), df_final['Net_Profit'].sum()
            low_stock = df_final[df_final['Stock'] <= 5]

            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f'<div class="metric-card"><h2>💰 مبيعات اليوم</h2><div class="sales-val">{ts:,.2f}</div></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="metric-card"><h2>📈 الأرباح التقديرية</h2><div class="profit-val">{tp:,.2f}</div></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="metric-card"><h2>🚨 نواقص المخزن</h2><div class="warning-val">{len(low_stock)}</div></div>', unsafe_allow_html=True)

            t1, t2 = st.tabs(["🛒 قائمة النواقص", "📊 التحليل"])
            with t1:
                st.subheader("📦 بضاعة لازم تطلبها")
                st.dataframe(low_stock[['الصنف', 'Stock']].rename(columns={'Stock': 'الرصيد'}), use_container_width=True)
            with t2:
                st.plotly_chart(px.bar(df_final.nlargest(10, 'Total_Sales'), x='Total_Sales', y='الصنف', orientation='h', template="plotly_dark"))

    except Exception as e:
        st.error(f"⚠️ حصلت مشكلة: {e}. جرب تحفظ الملف بصيغة Excel Workbook وارفعُه تاني.")
else:
    st.info("مستني ترفع ملف المبيعات يا هندسة..")
