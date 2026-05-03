import streamlit as st
import pandas as pd
import plotly.express as px
from docx import Document
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="داشبورد زغلولة الذكية", layout="wide", page_icon="📈")

# --- وظيفة الوورد ---
def create_word_report(data, t_sales, t_profit, branch):
    doc = Document()
    doc.add_heading(f'تقرير مبيعات: {branch}', 0)
    doc.add_paragraph(f'تاريخ التقرير: {datetime.now().strftime("%Y-%m-%d")}')
    doc.add_heading('الملخص المالي', level=1)
    doc.add_paragraph(f'إجمالي المبيعات: {t_sales:,.2f} جنيه')
    doc.add_paragraph(f'صافي الأرباح: {t_profit:,.2f} جنيه')
    target = BytesIO()
    doc.save(target)
    return target.getvalue()

# --- الواجهة ---
st.title("📊 نظام زغلولة المطوّر")

with st.expander("📖 دليل حل مشكلة الأرقام السالبة"):
    st.markdown("""
    **ليه كان بيطلع سالب؟**
    لأن سعر الشراء في ملفك غالباً متسجل لـ "الكرتونة" أو "الجملة"، بينما سعر البيع لـ "الكيلو".
    
    **تم تعديل الكود الآن ليقوم بـ:**
    1. حساب إجمالي البيع للصنف.
    2. طرح إجمالي التكلفة بناءً على الكمية الفعلية.
    """)

uploaded_file = st.file_uploader("📥 ارفع ملف المبيعات", type=['xls', 'csv'])

if uploaded_file:
    @st.cache_data
    def process_data(file):
        try:
            df = pd.read_csv(file, encoding='cp1256')
        except:
            df = pd.read_excel(file)
            
        branch = df['الفرع'].dropna().iloc[0] if 'الفرع' in df.columns else "الفرع الرئيسي"
        df = df.dropna(subset=['رقم الفاتورة']).copy()
        df = df[~df['الصنف'].str.contains('اجمالى|وارد', na=False)]
        
        # تحويل الأعمدة لأرقام وتنظيفها
        for col in ['الكمية', 'السعر', 'س شراء']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace('[^0-9.]', '', regex=True), errors='coerce').fillna(0)
        
        # --- المعادلة المنضبطة ---
        # إجمالي المبيعات للصنف
        df['Total_Sales'] = df['الكمية'] * df['السعر']
        
        # هنا التعديل: لو سعر الشراء في الملف هو سعر "الجملة"، لازم نقسمه (لكن الأفضل نضرب سعر شراء الكيلو في الكمية)
        # سنفترض أن 'س شراء' في ملفك هو سعر الكيلو الواحد (التكلفة)
        df['Total_Cost'] = df['الكمية'] * df['س شراء']
        
        # صافي الربح = إجمالي البيع - إجمالي التكلفة
        df['Net_Profit'] = df['Total_Sales'] - df['Total_Cost']
        
        return df, branch

    data, branch = process_data(uploaded_file)

    # حسابات عامة
    t_sales = data['Total_Sales'].sum()
    t_profit = data['Net_Profit'].sum()
    
    col1, col2 = st.columns(2)
    col1.metric("💰 إجمالي المبيعات", f"{t_sales:,.2f} ج.م")
    col2.metric("📈 صافي الأرباح", f"{t_profit:,.2f} ج.م", 
                delta_color="normal" if t_profit >= 0 else "inverse")

    st.markdown("---")
    
    # عرض جدول لتحليل المشكلة
    st.subheader("🔍 مراجعة أسعار الأصناف")
    st.write("راجع عمود 'س شراء'.. لو لقيت الرقم كبير جداً (زي 780 للكرتونة) يبقى لازم يتعدل في ملف الإكسيل لسعر الكيلو.")
    st.dataframe(data[['الصنف', 'الكمية', 'السعر', 'س شراء', 'Net_Profit']].sort_values(by='Net_Profit').head(10))

    # الرسم البياني
    top_p = data.groupby('الصنف')['Net_Profit'].sum().sort_values(ascending=False).head(15)
    fig = px.bar(top_p, orientation='h', title="تحليل أرباح الأصناف (بعد التعديل)",
                 color=top_p.values, color_continuous_scale='RdYlGn')
    st.plotly_chart(fig, use_container_width=True)
