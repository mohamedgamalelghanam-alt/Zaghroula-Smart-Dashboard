import streamlit as st
import pandas as pd
import plotly.express as px
from docx import Document
from docx.shared import Inches
from io import BytesIO
from datetime import datetime
import re

# 1. إعدادات الصفحة والستايل الاحترافي
st.set_page_config(page_title="Zaghloula Smart Dashboard", layout="wide", page_icon="☕")

# CSS لتجميل الواجهة
st.markdown("""
<style>
    .main { background-color: #fcfcfc; }
    /* ستايل الكروت الملونة */
    .metric-card {
        background: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-top: 5px solid #27ae60; text-align: center;
    }
    .metric-card.profit { border-top: 5px solid #2980b9; }
    .metric-card.warning { border-top: 5px solid #e74c3c; }
    h2 { color: #2c3e50; font-size: 1.1rem; margin-bottom: 5px; }
    h1 { font-size: 1.8rem; margin: 0; color: #1e272e; }
    /* خلفية مائية خفيفة */
    .main::before {
        content: "ZAGHLOULA";
        position: fixed; top: 50%; left: 50%;
        transform: translate(-50%, -50%) rotate(-30deg);
        font-size: 8vw; color: rgba(0,0,0,0.02);
        z-index: -1; font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- وظيفة إنشاء ملف الوورد ---
def create_word_report(data, t_sales, t_profit, branch):
    doc = Document()
    doc.add_heading(f'تقرير مبيعات زغلولة - {branch}', 0)
    doc.add_paragraph(f'تاريخ التقرير: {datetime.now().strftime("%Y-%m-%d")}')
    doc.add_heading('الملخص المالي', level=1)
    doc.add_paragraph(f'إجمالي المبيعات: {t_sales:,.2f} جنيه')
    doc.add_paragraph(f'صافي الربح: {t_profit:,.2f} جنيه')
    table = doc.add_table(rows=1, cols=3); table.style = 'Table Grid'
    hdr = table.rows[0].cells; hdr[0].text, hdr[1].text, hdr[2].text = 'الصنف', 'المبيعات', 'الربح'
    for _, row in data.head(15).iterrows():
        row_cells = table.add_row().cells
        row_cells[0].text, row_cells[1].text, row_cells[2].text = str(row['الصنف']), f"{row['Total_Sales']:,.2f}", f"{row['Net_Profit']:,.2f}"
    target = BytesIO(); doc.save(target)
    return target.getvalue()

# --- واجهة الداشبورد ---
st.title("📊 نظام زغلولة للتحليل الذكي")
st.markdown("---")

uploaded_file = st.sidebar.file_uploader("📂 ارفع ملف المبيعات (xls/csv)", type=['xls', 'csv', 'xlsx'])

if uploaded_file:
    @st.cache_data
    def load_and_clean(file):
        try:
            df = pd.read_csv(file, encoding='cp1256')
        except:
            df = pd.read_excel(file)
            
        branch = df['الفرع'].dropna().iloc[0] if 'الفرع' in df.columns else "الفرع الرئيسي"
        df_sales = df.dropna(subset=[df.columns[0]]).copy() # اختيار أول عمود للفاتورة تلقائياً
        
        # تنظيف الأصناف
        if 'الصنف' in df_sales.columns:
            df_sales = df_sales[~df_sales['الصنف'].astype(str).str.contains('اجمالى|وارد', na=False)]
        
        # تنظيف الأرقام (الزتونة اللي في ملفك)
        for col in ['الكمية', 'السعر', 'س شراء', 'الكمية المتبقية']:
            if col in df_sales.columns:
                df_sales[col] = pd.to_numeric(df_sales[col].astype(str).str.replace('×', '').str.replace('x', '').str.strip(), errors='coerce').fillna(0)
        
        df_sales['Total_Sales'] = df_sales['الكمية'] * df_sales['السعر']
        df_sales['Net_Profit'] = df_sales['Total_Sales'] - df_sales['س شراء'].fillna(0)
        return df_sales, branch

    data, branch = load_and_clean(uploaded_file)
    t_sales = data['Total_Sales'].sum()
    t_profit = data['Net_Profit'].sum()
    low_stock = data[data['الكمية المتبقية'] <= 5]

    # --- عرض الكروت الاحترافية ---
    st.subheader(f"📍 مراجعة أداء: {branch}")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><h2>💰 إجمالي المبيعات</h2><h1>{t_sales:,.2f} <small>ج.م</small></h1></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card profit"><h2>📈 صافي الأرباح</h2><h1>{t_profit:,.2f} <small>ج.م</small></h1></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card warning"><h2>🚨 أصناف للنواقص</h2><h1>{len(low_stock["الصنف"].unique())}</h1></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- التبويبات ---
    tab1, tab2, tab3 = st.tabs(["📊 التحليل البياني", "🛒 قائمة النواقص", "📥 التقارير"])

    with tab1:
        col_left, col_right = st.columns(2)
        with col_left:
            top_p = data.groupby('الصنف')['Net_Profit'].sum().sort_values(ascending=False).head(10)
            fig1 = px.bar(top_p, orientation='h', title="أعلى الأصناف ربحية", color_continuous_scale='Greens', color=top_p.values)
            st.plotly_chart(fig1, use_container_width=True)
        with col_right:
            top_q = data.groupby('الصنف')['الكمية'].sum().sort_values(ascending=False).head(10)
            fig2 = px.pie(values=top_q.values, names=top_q.index, title="توزيع حجم المبيعات", hole=0.4)
            st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        st.subheader("📦 بضاعة قاربت على النفاد")
        if not low_stock.empty:
            st.dataframe(low_stock[['الصنف', 'الكمية المتبقية']].drop_duplicates().style.background_gradient(cmap='Reds'), use_container_width=True)
        else:
            st.success("كل الأصناف متوفرة بكميات كافية!")

    with tab3:
        st.markdown("### استخراج التقرير الرسمي")
        st.info("سيتم إنشاء ملف Word يحتوي على ملخص مالي وجدول لأهم مبيعات اليوم.")
        word_file = create_word_report(data, t_sales, t_profit, branch)
        st.download_button(
            label="📝 تحميل تقرير زغلولة (Word)",
            data=word_file,
            file_name=f"تقرير_زغلولة_{datetime.now().strftime('%Y%m%d')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

else:
    st.info("ارفع ملف المبيعات من القائمة الجانبية عشان نبدأ التحليل يا هندسة!")

st.markdown("---")
st.markdown("<center>تطوير المهندس محمد جمال | 2026</center>", unsafe_allow_html=True)
