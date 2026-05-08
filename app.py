import streamlit as st
import pandas as pd
import plotly.express as px
from docx import Document
from io import BytesIO
from datetime import datetime
import re

# 1. إعدادات الصفحة والستايل
st.set_page_config(page_title="داشبورد زغلولة الذكية", layout="wide")

st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .main::before {
        content: "ZAGHLOULA";
        position: fixed; top: 50%; left: 50%;
        transform: translate(-50%, -50%) rotate(-30deg);
        font-size: 10vw; color: rgba(0, 0, 0, 0.03);
        z-index: -1; font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# وظيفة إنشاء ملف الوورد
def create_word_report(data, t_sales, t_profit, branch):
    doc = Document()
    doc.add_heading(f'تقرير مبيعات زغلولة: {branch}', 0)
    doc.add_paragraph(f'تاريخ التقرير: {datetime.now().strftime("%Y-%m-%d")}')
    doc.add_heading('الملخص المالي', level=1)
    doc.add_paragraph(f'إجمالي المبيعات: {t_sales:,.2f} جنيه')
    doc.add_paragraph(f'صافي الربح: {t_profit:,.2f} جنيه')
    table = doc.add_table(rows=1, cols=3)
    table.style = 'Table Grid'
    headers = table.rows[0].cells
    headers[0].text, headers[1].text, headers[2].text = 'الصنف', 'المبيعات', 'الربح'
    for _, row in data.head(20).iterrows():
        cells = table.add_row().cells
        cells[0].text, cells[1].text, cells[2].text = str(row['الصنف']), f"{row['Total_Sales']:,.2f}", f"{row['Net_Profit']:,.2f}"
    target = BytesIO()
    doc.save(target)
    return target.getvalue()

# واجهة التطبيق
st.title("📊 نظام زغلولة لإدارة البيانات والتحليل")

with st.expander("📘 دليل الاستخدام السريع"):
    st.write("1. ارفع ملفك (CSV/Excel) | 2. راجع المبيعات والأرباح | 3. افحص الأصناف الخاسرة | 4. حمل تقرير الوورد.")

uploaded_file = st.sidebar.file_uploader("ارفع ملف المبيعات", type=['xls', 'csv', 'xlsx'])

if uploaded_file:
    try:
        # قراءة وتنظيف البيانات
        try: df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
        except: df = pd.read_csv(uploaded_file, encoding='cp1256')
        
        # تنظيف الأرقام من علامة (×) والرموز
        def clean_num(x):
            val = re.sub(r'[^\d.]', '', str(x))
            try: return float(val)
            except: return 0

        # تحديد الأعمدة بالترتيب لضمان القراءة الصحيحة
        name_col = df.columns[2]
        qty_col = df.columns[3]
        price_col = df.columns[4]
        cost_col = 'سعر التكلفة' if 'سعر التكلفة' in df.columns else df.columns[-1]

        df['Qty'] = df[qty_col].apply(clean_num)
        df['Price'] = df[price_col].apply(clean_num)
        df['Cost'] = df[cost_col].apply(clean_num) if cost_col in df.columns else 0
        
        df['Total_Sales'] = df['Qty'] * df['Price']
        df['Net_Profit'] = (df['Price'] - df['Cost']) * df['Qty']
        df['الصنف'] = df[name_col]

        # فلترة
        df = df[df['Total_Sales'] > 0]
        df = df[~df['الصنف'].astype(str).str.contains('اجمالى|وارد|????', na=False)]

        # العرض
        t_sales, t_profit = df['Total_Sales'].sum(), df['Net_Profit'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 إجمالي المبيعات", f"{t_sales:,.2f} ج.م")
        c2.metric("📈 صافي الأرباح", f"{t_profit:,.2f} ج.م")
        c3.metric("🚨 أصناف ناقصة", f"{len(df[df['Qty'] < 1])}")

        tab1, tab2 = st.tabs(["📊 التحليل", "⚠️ مراجعة التسعير"])
        with tab1:
            st.plotly_chart(px.bar(df.groupby('الصنف')['Net_Profit'].sum().nlargest(10).reset_index(), x='Net_Profit', y='الصنف', orientation='h', title="أعلى 10 أصناف ربحية"))
            st.download_button("📝 تحميل تقرير الوورد", data=create_word_report(df, t_sales, t_profit, "فرع زغلولة"), file_name="تقرير_زغلولة.docx")
        with tab2:
            loss = df[df['Price'] < df['Cost']][['الصنف', 'Cost', 'Price', 'Net_Profit']]
            if not loss.empty: st.warning("أصناف تخسر! راجع تسعيرها:"); st.dataframe(loss)
            else: st.success("كل الأصناف مسعرة صح!")
    except Exception as e: st.error(f"حدث خطأ: {e}")
else:
    st.info("ارفع الملف عشان نطلع الأرقام يا هندسة!")

st.markdown("---")
st.markdown("<center>تطوير المهندس محمد جمال | 01029796096</center>", unsafe_allow_html=True)
