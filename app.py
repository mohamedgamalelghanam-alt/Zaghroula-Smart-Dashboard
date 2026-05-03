import streamlit as st
import pandas as pd
import plotly.express as px
from docx import Document
from io import BytesIO
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="داشبورد زغلولة الذكية", layout="wide", page_icon="📈")

# --- وظيفة إنشاء ملف الوورد (Word) ---
def create_word_report(data, t_sales, t_profit, branch):
    doc = Document()
    doc.add_heading(f'تقرير مبيعات: {branch}', 0)
    doc.add_paragraph(f'تاريخ التقرير: {datetime.now().strftime("%Y-%m-%d")}')
    
    doc.add_heading('الملخص المالي اليومي', level=1)
    doc.add_paragraph(f'إجمالي المبيعات: {t_sales:,.2f} جنيه')
    doc.add_paragraph(f'صافي الأرباح: {total_profit:,.2f} جنيه')
    
    doc.add_heading('أعلى الأصناف ربحية', level=1)
    table = doc.add_table(rows=1, cols=3)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'الصنف'
    hdr_cells[1].text = 'المبيعات'
    hdr_cells[2].text = 'صافي الربح'
    
    # إضافة أول 20 صنف رابح للجدول
    for _, row in data.sort_values(by='صافي_الربح', ascending=False).head(20).iterrows():
        row_cells = table.add_row().cells
        row_cells[0].text = str(row['الصنف'])
        row_cells[1].text = f"{row['إجمالي_البيع']:,.2f}"
        row_cells[2].text = f"{row['صافي_الربح']:,.2f}"
        
    target = BytesIO()
    doc.save(target)
    return target.getvalue()

# --- واجهة المستخدم ---
st.title("📊 نظام تحليل مبيعات زغلولة الذكي")

with st.expander("📖 دليل الاستخدام السريع"):
    st.markdown("""
    1. ارفع ملف الـ **Excel** الناتج من سيستم المحل مباشرة.
    2. النظام هيحسب الربح بناءً على: `(الكمية * السعر) - س شراء`.
    3. تقدر تحمل تقرير Word رسمي بالأرقام دي في أي وقت.
    """)

st.markdown("---")

# دعم رفع ملفات الإكسيل مباشرة
uploaded_file = st.file_uploader("📥 ارفع ملف مبيعات اليوم (Excel)", type=['xls', 'xlsx'])

if uploaded_file:
    @st.cache_data
    def process_excel_data(file):
        # قراءة الإكسيل مباشرة
        try:
            df = pd.read_excel(file)
        except Exception as e:
            st.error(f"حدث خطأ أثناء قراءة الملف: {e}")
            return None, None
            
        branch = df['الفرع'].dropna().iloc[0] if 'الفرع' in df.columns else "الفرع الرئيسي"
        
        # تنظيف البيانات (حذف الصفوف الفاضية والكلمات الزيادة)
        df = df.dropna(subset=['الصنف']).copy()
        df = df[~df['الصنف'].str.contains('اجمالى|وارد', na=False)]
        
        # تحويل الأعمدة لأرقام لضمان دقة الحسابات
        cols_to_fix = ['الكمية', 'السعر', 'س شراء']
        for col in cols_to_fix:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # --- الحسبة الصحيحة بناءً على ملفك ---
        df['إجمالي_البيع'] = df['الكمية'] * df['السعر']
        # صافي الربح = إجمالي البيع - إجمالي التكلفة (س شراء)
        df['صافي_الربح'] = df['إجمالي_البيع'] - df['س شراء']
        
        return df, branch

    data, branch = process_excel_data(uploaded_file)

    if data is not None:
        # المؤشرات الرئيسية
        total_sales = data['إجمالي_البيع'].sum()
        total_profit = data['صافي_الربح'].sum()
        
        m1, m2 = st.columns(2)
        m1.metric("💰 إجمالي المبيعات", f"{total_sales:,.2f} ج.م")
        m2.metric("📈 صافي الأرباح", f"{total_profit:,.2f} ج.م")

        st.markdown("---")
        
        # التحليل البياني وتقرير الوورد
        col_left, col_right = st.columns([7, 3])
        
        with col_left:
            top_p = data.groupby('الصنف')['صافي_الربح'].sum().sort_values(ascending=False).head(10)
            fig = px.bar(top_p, orientation='h', title="أعلى 10 أصناف تحقيقاً للربح",
                         labels={'value':'الربح بالجنيه', 'الصنف':''},
                         color=top_p.values, color_continuous_scale='Greens')
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.info("📂 تقرير الوورد")
            word_btn = create_word_report(data, total_sales, total_profit, branch)
            st.download_button(
                label="📝 تحميل التقرير (Word)",
                data=word_btn,
                file_name=f"Zaghroula_Report_{datetime.now().strftime('%Y%m%d')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            
            st.markdown("### 📋 معاينة البيانات")
            st.dataframe(data[['الصنف', 'إجمالي_البيع', 'صافي_الربح']].head(10), hide_index=True)

st.markdown("---")
st.caption(f"تطوير المهندس محمد جمال | 2026")
