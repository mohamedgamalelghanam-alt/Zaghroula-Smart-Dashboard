import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="Zaghroula Smart Analytics", layout="wide", page_icon="📈")

# --- 1. الافتتاحية ---
st.title("🚀 نظام زغلولة للتحليل الذكي")

# --- 2. رفع الملف ---
uploaded_file = st.file_uploader("📥 ارفع ملف مبيعات اليوم (xls/csv)", type=['xls', 'csv'])

if uploaded_file:
    @st.cache_data
    def load_and_clean(file):
        try:
            df = pd.read_csv(file, encoding='cp1256')
        except:
            df = pd.read_excel(file)
            
        # استخراج اسم الفرع (بناخد أول قيمة غير فارغة من عمود 'الفرع')
        branch_name = df['الفرع'].dropna().iloc[0] if 'الفرع' in df.columns else "فرع غير معروف"
            
        df_sales = df.dropna(subset=['رقم الفاتورة']).copy()
        df_sales = df_sales[~df_sales['الصنف'].str.contains('اجمالى|وارد', na=False)]
        
        for col in ['الكمية', 'السعر', 'س شراء', 'الكمية المتبقية']:
            df_sales[col] = pd.to_numeric(df_sales[col].astype(str).str.replace('×', '').str.replace('x', '').str.strip(), errors='coerce')
        
        df_sales['س شراء'] = df_sales['س شراء'].fillna(0)
        df_sales['Total_Sales'] = df_sales['الكمية'] * df_sales['السعر']
        df_sales['Net_Profit'] = df_sales['Total_Sales'] - df_sales['س شراء']
        
        return df_sales, branch_name

    data, branch = load_and_clean(uploaded_file)

    # عرض اسم الفرع والبيانات التعريفية
    st.markdown(f"""
        ### 📍 تقرير: {branch}
        **مرحباً بك في منصة دعم القرار. هذا التقرير مخصص لتحليل مبيعات فرعكم لليوم.**
        ---
        *تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d')}*
    """)

    # --- 3. المؤشرات الرئيسية ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("💰 إجمالي المبيعات")
        st.subheader(f"{data['Total_Sales'].sum():,.2f} ج.م")
    with col2:
        st.success("📈 صافي الأرباح")
        st.subheader(f"{data['Net_Profit'].sum():,.2f} ج.م")
    with col3:
        low_stock = data[data['الكمية المتبقية'] <= 5]
        st.error("🚨 أصناف للنفاذ")
        st.subheader(f"{len(low_stock['الصنف'].unique())} صنف")

    st.markdown("---")

    # --- 4. الرسوم البيانية ---
    c1, c2 = st.columns(2)
    with c1:
        top_profit = data.groupby('الصنف')['Net_Profit'].sum().sort_values(ascending=False).head(10)
        fig_profit = px.bar(top_profit, x=top_profit.values, y=top_profit.index, orientation='h', 
                             title=f"أعلى الأصناف ربحية في {branch}", color_discrete_sequence=['#00CC96'])
        st.plotly_chart(fig_profit, use_container_width=True)

    with c2:
        top_qty = data.groupby('الصنف')['الكمية'].sum().sort_values(ascending=False).head(10)
        fig_qty = px.pie(values=top_qty.values, names=top_qty.index, title="توزيع سحب الكميات")
        st.plotly_chart(fig_qty, use_container_width=True)

    # --- 5. تصدير التقرير (مع إضافة اسم الفرع) ---
    st.markdown("### 📥 تصدير التقرير")
    
    report_data = data[['الصنف', 'الكمية', 'السعر', 'Total_Sales', 'Net_Profit', 'الكمية المتبقية']].copy()
    report_data['الفرع'] = branch # إضافة عمود الفرع في الملف المستخرج
    
    csv = report_data.to_csv(index=False).encode('utf-8-sig')
    
    st.download_button(
        label=f"🖨️ تحميل تقرير {branch} للطباعة",
        data=csv,
        file_name=f'Report_{branch}_{datetime.now().strftime("%Y-%m-%d")}.csv',
        mime='text/csv',
    )

    # --- 6. جدول النواقص ---
    if not low_stock.empty:
        st.warning(f"⚠️ قائمة النواقص لـ {branch}")
        st.dataframe(low_stock[['الصنف', 'الكمية المتبقية']].drop_duplicates(), use_container_width=True)
