import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="داشبورد زغلولة الذكية", layout="wide")

st.title("📊 نظام تحليل مبيعات زغلولة اليومي")
st.markdown("---")

uploaded_file = st.file_uploader("ارفع ملف مبيعات اليوم (xls)", type=['xls', 'csv'])

if uploaded_file:
    @st.cache_data
    def load_and_clean(file):
        try:
            df = pd.read_csv(file, encoding='cp1256')
        except:
            df = pd.read_excel(file)
            
        branch = df['الفرع'].dropna().iloc[0] if 'الفرع' in df.columns else "الفرع الرئيسي"
        df_sales = df.dropna(subset=['رقم الفاتورة']).copy()
        df_sales = df_sales[~df_sales['الصنف'].str.contains('اجمالى|وارد', na=False)]
        
        for col in ['الكمية', 'السعر', 'س شراء', 'الكمية المتبقية']:
            df_sales[col] = pd.to_numeric(df_sales[col].astype(str).str.replace('×', '').str.replace('x', '').str.strip(), errors='coerce')
        
        df_sales['س شراء'] = df_sales['س شراء'].fillna(0)
        df_sales['Total_Sales'] = df_sales['الكمية'] * df_sales['السعر']
        df_sales['Net_Profit'] = df_sales['Total_Sales'] - df_sales['س شراء']
        return df_sales, branch

    data, branch = load_and_clean(uploaded_file)

    # 1. قسم الأرقام الرئيسية (Key Metrics)
    st.subheader(f"📍 فرع: {branch}")
    col1, col2, col3 = st.columns(3)
    t_sales = data['Total_Sales'].sum()
    t_profit = data['Net_Profit'].sum()
    
    col1.metric("💰 إجمالي المبيعات", f"{t_sales:,.2f} ج.م")
    col2.metric("📈 صافي الأرباح", f"{t_profit:,.2f} ج.م")
    
    low_stock = data[data['الكمية المتبقية'] <= 5]
    col3.metric("🚨 أصناف ناقصة", f"{len(low_stock['الصنف'].unique())}")

    st.markdown("---")

    # 2. الرسوم البيانية
    c1, c2 = st.columns(2)
    with c1:
        top_profit = data.groupby('الصنف')['Net_Profit'].sum().sort_values(ascending=False).head(10)
        fig_profit = px.bar(top_profit, x=top_profit.values, y=top_profit.index, orientation='h', 
                             title="أعلى 10 أصناف ربحية", color_discrete_sequence=['#2ecc71'])
        st.plotly_chart(fig_profit, use_container_width=True)

    with c2:
        top_qty = data.groupby('الصنف')['الكمية'].sum().sort_values(ascending=False).head(10)
        fig_qty = px.pie(values=top_qty.values, names=top_qty.index, title="توزيع الكميات المباعة")
        st.plotly_chart(fig_qty, use_container_width=True)

    # 3. قسم "الخلاصة للطباعة" (ال بديل للـ PDF)
    st.markdown("### 📋 ملخص التقرير اليومي")
    summary_text = f"""
    * **الفرع:** {branch}
    * **التاريخ:** {datetime.now().strftime('%Y-%m-%d')}
    * **إجمالي المبيعات:** {t_sales:,.2f} جنيه
    * **صافي الربح:** {t_profit:,.2f} جنيه
    * **عدد الأصناف المباعة:** {len(data)} صنف
    """
    st.info(summary_text)

    # 4. زرار تحميل إكسيل (CSV) شيك جداً وبيدعم العربي
    st.markdown("### 📥 تصدير البيانات")
    csv_data = data[['الصنف', 'الكمية', 'السعر', 'Total_Sales', 'Net_Profit', 'الكمية المتبقية']].to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 تحميل التقرير (Excel/CSV)",
        data=csv_data,
        file_name=f"تقرير_زغلولة_{datetime.now().strftime('%Y%m%d')}.csv",
        mime='text/csv',
    )

    # 5. جدول النواقص
    st.markdown("### 🛒 قائمة النواقص")
    if not low_stock.empty:
        st.dataframe(low_stock[['الصنف', 'الكمية المتبقية']].drop_duplicates(), use_container_width=True)
    else:
        st.success("المخزن تمام، مفيش نواقص!")
