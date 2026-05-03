import streamlit as st
import pandas as pd
import plotly.express as px
from docx import Document
from io import BytesIO
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="داشبورد زغلولة الذكية", layout="wide", page_icon="📈")

# --- وظيفة إنشاء ملف الوورد ---
def create_word_report(data, t_sales, t_profit, branch):
    doc = Document()
    doc.add_heading(f'تقرير مبيعات: {branch}', 0)
    doc.add_paragraph(f'تاريخ التقرير: {datetime.now().strftime("%Y-%m-%d")}')
    
    doc.add_heading('الملخص المالي', level=1)
    doc.add_paragraph(f'إجمالي المبيعات: {t_sales:,.2f} جنيه')
    doc.add_paragraph(f'صافي الأرباح: {t_profit:,.2f} جنيه')
    
    doc.add_heading('تحليل الأصناف (الأكثر ربحية)', level=1)
    table = doc.add_table(rows=1, cols=3)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'الصنف'
    hdr_cells[1].text = 'إجمالي المبيعات'
    hdr_cells[2].text = 'صافي الربح'
    
    for _, row in data.sort_values(by='Net_Profit', ascending=False).head(20).iterrows():
        row_cells = table.add_row().cells
        row_cells[0].text = str(row['الصنف'])
        row_cells[1].text = f"{row['Total_Sales']:,.2f}"
        row_cells[2].text = f"{row['Net_Profit']:,.2f}"
        
    target = BytesIO()
    doc.save(target)
    return target.getvalue()

# --- الواجهة الرئيسية ---
st.title("📊 نظام زغلولة لإدارة المبيعات")

with st.expander("📖 دليل الاستخدام السريع"):
    st.markdown("""
    1. ارفع ملف الـ **Excel** أو **CSV** الناتج من سيستم الكاشير.
    2. تأكد أن الأعمدة تحتوي على (الصنف، الكمية، السعر، س شراء).
    3. النظام سيحسب الربح بالمعادلة: `(سعر البيع - سعر الشراء) * الكمية`.
    4. إذا ظهر الربح بالسالب، فهذا يعني أن سعر الشراء المسجل أكبر من سعر البيع.
    """)

uploaded_file = st.file_uploader("📥 ارفع ملف مبيعات اليوم", type=['xls', 'csv'])

if uploaded_file:
    @st.cache_data
    def process_data(file):
        try:
            df = pd.read_csv(file, encoding='cp1256')
        except:
            df = pd.read_excel(file)
            
        branch = df['الفرع'].dropna().iloc[0] if 'الفرع' in df.columns else "الفرع الرئيسي"
        
        # تنظيف البيانات الأساسية
        df = df.dropna(subset=['رقم الفاتورة']).copy()
        df = df[~df['الصنف'].str.contains('اجمالى|وارد', na=False)]
        
        # تحويل القيم لأرقام لضمان دقة الحسابات
        cols_to_fix = ['الكمية', 'السعر', 'س شراء', 'الكمية المتبقية']
        for col in cols_to_fix:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace('[^0-9.]', '', regex=True), errors='coerce').fillna(0)
        
        # --- الحسبة الصحيحة للربح ---
        df['Total_Sales'] = df['الكمية'] * df['السعر']
        # ربح القطعة الواحدة = سعر البيع - سعر الشراء
        df['Unit_Profit'] = df['السعر'] - df['س شراء']
        # إجمالي ربح الصنف = ربح القطعة * الكمية المباعة
        df['Net_Profit'] = df['Unit_Profit'] * df['الكمية']
        
        return df, branch

    data, branch = process_data(uploaded_file)

    # عرض المؤشرات
    t_sales = data['Total_Sales'].sum()
    t_profit = data['Net_Profit'].sum()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 إجمالي المبيعات", f"{t_sales:,.2f} ج.م")
    
    # تلوين الربح (أحمر لو خسارة، أخضر لو ربح)
    col2.metric("📈 صافي الأرباح", f"{t_profit:,.2f} ج.م", 
                delta=f"{((t_profit/t_sales)*100) if t_sales !=0 else 0:.1f}% هامش ربح",
                delta_color="normal" if t_profit >= 0 else "inverse")
    
    low_stock = data[data['الكمية المتبقية'] <= 5].drop_duplicates(subset=['الصنف'])
    col3.metric("🚨 نواقص المخزن", f"{len(low_stock)}")

    # التحليلات
    st.markdown("---")
    c1, c2 = st.columns([7, 3])
    
    with c1:
        # رسم بياني للأصناف الرابحة
        top_p = data.groupby('الصنف')['Net_Profit'].sum().sort_values(ascending=False).head(10)
        fig = px.bar(top_p, orientation='h', title="تحليل أرباح الأصناف",
                     labels={'value':'الربح/الخسارة بالجنيه', 'الصنف':''},
                     color=top_p.values, color_continuous_scale='RdYlGn')
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.info("📂 تقرير الوورد")
        report_btn = create_word_report(data, t_sales, t_profit, branch)
        st.download_button("📝 تحميل التقرير (Word)", report_btn, 
                           file_name=f"Report_{branch}_{datetime.now().strftime('%d-%m')}.docx")
        
        # تنبيه لو فيه خسائر
        losses = data[data['Net_Profit'] < 0]
        if not losses.empty:
            st.warning(f"⚠️ يوجد {len(losses)} أصناف مباعة بسعر أقل من التكلفة!")
            st.dataframe(losses[['الصنف', 'السعر', 'س شراء', 'Net_Profit']].head(), hide_index=True)

    st.markdown("---")
    st.caption(f"تم التحليل لفرع {branch} | تطوير المهندس محمد جمال")
