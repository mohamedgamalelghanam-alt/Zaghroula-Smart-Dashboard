import streamlit as st
import pandas as pd
import plotly.express as px
from docx import Document
from io import BytesIO
from datetime import datetime
import re  # السطر ده هو اللي كان ناقص ومطلع الإيرور

# 1. إعداد الصفحة والستايل
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
    .metric-card {
        background: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); text-align: center;
        border-top: 5px solid #27ae60;
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
    table = doc.add_table(rows=1, cols=3); table.style = 'Table Grid'
    hdr = table.rows[0].cells; hdr[0].text, hdr[1].text, hdr[2].text = 'الصنف', 'المبيعات', 'الربح'
    for _, row in data.head(15).iterrows():
        c = table.add_row().cells
        c[0].text, c[1].text, c[2].text = str(row['الصنف']), f"{row['Total_Sales']:,.2f}", f"{row['Net_Profit']:,.2f}"
    target = BytesIO(); doc.save(target)
    return target.getvalue()

# واجهة التطبيق
st.title("📊 نظام زغلولة لإدارة البيانات والتحليل")

with st.expander("📘 دليل الاستخدام"):
    st.write("ارفع ملف الداتا (Day 1) وهنظف لك الأرقام ونطلع لك الأرباح فوراً.")

uploaded_file = st.sidebar.file_uploader("ارفع ملف المبيعات", type=['xls', 'csv', 'xlsx'])

if uploaded_file:
    try:
        # قراءة الملف بتشفير العربي
        try: df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
        except: df = pd.read_csv(uploaded_file, encoding='cp1256')
        
        # تنظيف الأرقام (نسف الـ × والـ *)
        def clean_num(x):
            if pd.isna(x): return 0
            val = re.sub(r'[^\d.]', '', str(x))
            try: return float(val)
            except: return 0

        # تحديد الأعمدة بالترتيب عشان نهرب من الرموز
        idx_name, idx_qty, idx_price = 2, 3, 4
        df['الصنف'] = df.iloc[:, idx_name]
        df['Qty'] = df.iloc[:, idx_qty].apply(clean_num)
        df['Price'] = df.iloc[:, idx_price].apply(clean_num)
        
        # حساب التكلفة (لو مش موجودة هنفترض ربح 20%)
        df['Total_Sales'] = df['Qty'] * df['Price']
        df['Net_Profit'] = df['Total_Sales'] * 0.20

        # فلترة
        df = df[df['Total_Sales'] > 0]
        df = df[~df['الصنف'].astype(str).str.contains('اجمالى|وارد', na=False)]

        # العرض
        ts, tp = df['Total_Sales'].sum(), df['Net_Profit'].sum()
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="metric-card"><h2>💰 مبيعات</h2><h1>{ts:,.0f}</h1></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card"><h2>📈 أرباح</h2><h1>{tp:,.0f}</h1></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card"><h2>📦 أصناف</h2><h1>{len(df)}</h1></div>', unsafe_allow_html=True)

        st.divider()
        tab1, tab2 = st.tabs(["📊 التحليل", "📝 التقرير"])
        with tab1:
            st.plotly_chart(px.bar(df.groupby('الصنف')['Total_Sales'].sum().nlargest(10).reset_index(), x='Total_Sales', y='الصنف', orientation='h'))
        with tab2:
            st.download_button("📥 تحميل التقرير (Word)", data=create_word_report(df, ts, tp, "زغلولة"), file_name="تقرير.docx")

    except Exception as e: st.error(f"حدث خطأ: {e}")
else:
    st.info("ارفع الملف يا هندسة!")

st.markdown("---")
st.markdown("<center>تطوير المهندس محمد جمال | 01029796096</center>", unsafe_allow_html=True)
