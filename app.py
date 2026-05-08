import streamlit as st

import pandas as pd

import plotly.express as px

from docx import Document

from docx.shared import Inches

from io import BytesIO

from datetime import datetime



# إعدادات الصفحة

st.set_page_config(page_title="داشبورد زغلولة الذكية", layout="wide")



# --- وظيفة إنشاء ملف الوورد (Word) ---

def create_word_report(data, t_sales, t_profit, branch):

    doc = Document()

    # كتابة العنوان (بيدعم العربي عادي في الوورد)

    doc.add_heading(f'تقرير مبيعات: {branch}', 0)

    

    doc.add_paragraph(f'تاريخ التقرير: {datetime.now().strftime("%Y-%m-%d")}')

    

    # ملخص الأرقام

    doc.add_heading('الملخص المالي', level=1)

    doc.add_paragraph(f'إجمالي المبيعات: {t_sales:,.2f} جنيه')

    doc.add_paragraph(f'صافي الربح: {t_profit:,.2f} جنيه')

    

    # إضافة جدول الأصناف

    doc.add_heading('أعلى الأصناف مبيعاً', level=1)

    table = doc.add_table(rows=1, cols=3)

    table.style = 'Table Grid'

    hdr_cells = table.rows[0].cells

    hdr_cells[0].text = 'الصنف'

    hdr_cells[1].text = 'المبيعات'

    hdr_cells[2].text = 'الربح'

    

    # إضافة أول 15 صنف للجدول

    for _, row in data.head(15).iterrows():

        row_cells = table.add_row().cells

        row_cells[0].text = str(row['الصنف'])

        row_cells[1].text = f"{row['Total_Sales']:,.2f}"

        row_cells[2].text = f"{row['Net_Profit']:,.2f}"

        

    # حفظ الملف في ذاكرة مؤقتة

    target = BytesIO()

    doc.save(target)

    return target.getvalue()



# --- واجهة الداشبورد ---

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

        

        df_sales['Net_Profit'] = (df_sales['الكمية'] * df_sales['السعر']) - df_sales['س شراء'].fillna(0)

        df_sales['Total_Sales'] = df_sales['الكمية'] * df_sales['السعر']

        return df_sales, branch



    data, branch = load_and_clean(uploaded_file)



    # المؤشرات الرئيسية

    st.subheader(f"📍 فرع: {branch}")

    col1, col2, col3 = st.columns(3)

    t_sales = data['Total_Sales'].sum()

    t_profit = data['Net_Profit'].sum()

    

    col1.metric("💰 إجمالي المبيعات", f"{t_sales:,.2f} ج.م")

    col2.metric("📈 صافي الأرباح", f"{t_profit:,.2f} ج.م")

    

    low_stock = data[data['الكمية المتبقية'] <= 5]

    col3.metric("🚨 أصناف ناقصة", f"{len(low_stock['الصنف'].unique())}")



    # --- زرار تحميل الوورد (Word) ---

    st.markdown("### 📥 تحميل التقرير الرسمي")

    word_file = create_word_report(data, t_sales, t_profit, branch)

    st.download_button(

        label="📝 تحميل التقرير (Word Document)",

        data=word_file,

        file_name=f"تقرير_زغلولة_{datetime.now().strftime('%Y%m%d')}.docx",

        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    )



    # الرسوم البيانية

    c1, c2 = st.columns(2)

    with c1:

        top_p = data.groupby('الصنف')['Net_Profit'].sum().sort_values(ascending=False).head(10)

        st.plotly_chart(px.bar(top_p, orientation='h', title="أعلى الأصناف ربحية"), use_container_width=True)

    with c2:

        top_q = data.groupby('الصنف')['الكمية'].sum().sort_values(ascending=False).head(10)

        st.plotly_chart(px.pie(values=top_q.values, names=top_q.index, title="توزيع المبيعات"), use_container_width=True)



    # قائمة النواقص

    st.markdown("### 🛒 قائمة النواقص")

    st.dataframe(low_stock[['الصنف', 'الكمية المتبقية']].drop_duplicates(), use_container_width=True)
