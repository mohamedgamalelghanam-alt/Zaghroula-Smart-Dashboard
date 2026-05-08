import streamlit as st
import pandas as pd
import plotly.express as px
from docx import Document
from io import BytesIO
from datetime import datetime
import re

# 1. إعدادات الصفحة والستايل الاحترافي المريح للعين
st.set_page_config(page_title="Zaghloula Smart Dashboard", layout="wide", page_icon="☕")

st.markdown("""
<style>
    .main { background-color: #fcfcfc; }
    /* ستايل الكروت الحديثة */
    .metric-card {
        background: white; padding: 25px; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-top: 5px solid #27ae60; text-align: center;
    }
    .metric-card.profit { border-top: 5px solid #2980b9; }
    .metric-card.warning { border-top: 5px solid #e74c3c; }
    h2 { color: #5c5c5c; font-size: 1.1rem; margin-bottom: 10px; font-weight: 500; }
    h1 { font-size: 2.2rem; margin: 0; color: #1e272e; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; background-color: #f1f2f6; border-radius: 10px;
        padding: 10px 25px; font-weight: bold;
    }
    .stTabs [aria-selected="true"] { background-color: #27ae60 !important; color: white !important; }
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
    for _, row in data.head(20).iterrows():
        row_cells = table.add_row().cells
        row_cells[0].text, row_cells[1].text, row_cells[2].text = str(row['الصنف']), f"{row['Total_Sales']:,.2f}", f"{row['Net_Profit']:,.2f}"
    target = BytesIO(); doc.save(target)
    return target.getvalue()

# --- هيدر التطبيق ---
st.title("📊 نظام زغلولة للتحليل الذكي")
st.markdown("---")

uploaded_file = st.sidebar.file_uploader("📂 ارفع ملف مبيعات اليوم", type=['xls', 'csv', 'xlsx'])

if uploaded_file:
    @st.cache_data
    def load_and_clean(file):
        try:
            df = pd.read_csv(file, encoding='utf-8-sig')
        except:
            try: df = pd.read_csv(file, encoding='cp1256')
            except: df = pd.read_excel(file)
        
        # تنظيف أسماء الأعمدة وحل مشكلة الرموز
        df.columns = [str(c).strip() for c in df.columns]
        branch = df['الفرع'].dropna().iloc[0] if 'الفرع' in df.columns else "فرع زغلولة"
        
        # مصفاة تنظيف الأرقام من علامات × و *
        def clean_val(x):
            if pd.isna(x): return 0
            val = re.sub(r'[^\d.]', '', str(x))
            try: return float(val)
            except: return 0

        # تحديد الأعمدة وحساب الربح
        df_sales = df.dropna(subset=[df.columns[2]]).copy() # اختيار عمود الصنف بالترتيب
        df_sales['الصنف'] = df_sales.iloc[:, 2]
        df_sales = df_sales[~df_sales['الصنف'].astype(str).str.contains('اجمالى|وارد', na=False)]
        
        # تطبيق التنظيف على أعمدة الحسابات
        for col in ['الكمية', 'السعر', 'س شراء', 'الكمية المتبقية']:
            if col in df_sales.columns:
                df_sales[col] = df_sales[col].apply(clean_val)
        
        df_sales['Total_Sales'] = df_sales['الكمية'] * df_sales['السعر']
        df_sales['Net_Profit'] = df_sales['Total_Sales'] - df_sales['س شراء'].fillna(0)
        return df_sales, branch

    data, branch = load_and_clean(uploaded_file)
    t_sales = data['Total_Sales'].sum()
    t_profit = data['Net_Profit'].sum()
    low_stock_list = data[data['الكمية المتبقية'] <= 5]

    # --- عرض مؤشرات الأداء بشكل احترافي ---
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; gap: 20px; margin-bottom: 40px;">
        <div class="metric-card" style="flex: 1;">
            <h2>💰 مبيعات اليوم</h2>
            <h1 style="color: #27ae60;">{t_sales:,.2f} <small style="font-size: 15px;">ج.م</small></h1>
        </div>
        <div class="metric-card profit" style="flex: 1;">
            <h2>📈 صافي الأرباح</h2>
            <h1 style="color: #2980b9;">{t_profit:,.2f} <small style="font-size: 15px;">ج.م</small></h1>
        </div>
        <div class="metric-card warning" style="flex: 1;">
            <h2>🚨 أصناف للنواقص</h2>
            <h1 style="color: #e74c3c;">{len(low_stock_list['الصنف'].unique())}</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- نظام التبويبات الجديد ---
    tab1, tab2, tab3 = st.tabs(["📊 التحليل البياني", "🛒 قائمة النواقص", "📝 استخراج التقارير"])

    with tab1:
        st.subheader(f"📍 ملخص الأداء: {branch}")
        c1, c2 = st.columns(2)
        with c1:
            top_p = data.groupby('الصنف')['Net_Profit'].sum().nlargest(10).reset_index()
            fig = px.bar(top_p, x='Net_Profit', y='الصنف', orientation='h', title="أعلى 10 أصناف ربحية", 
                         color='Net_Profit', color_continuous_scale='Greens', template="simple_white")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            top_q = data.groupby('الصنف')['الكمية'].sum().nlargest(10).reset_index()
            fig_pie = px.pie(top_q, values='الكمية', names='الصنف', title="توزيع حجم المبيعات (كمية)",
                             hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)

    with tab2:
        st.subheader("📦 بضاعة لازم تطلبها (أقل من 5 قطع)")
        if not low_stock_list.empty:
            st.dataframe(low_stock_list[['الصنف', 'الكمية المتبقية']].drop_duplicates().style.background_gradient(subset=['الكمية المتبقية'], cmap='Reds'), use_container_width=True)
        else:
            st.success("كل بضاعتك تمام، مفيش حاجة ناقصة حالياً!")

    with tab3:
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("اضغط على الزر أدناه لتحميل تقرير رسمي جاهز للطباعة بصيغة Word")
        word_file = create_word_report(data, t_sales, t_profit, branch)
        st.download_button(
            label="📥 تحميل تقرير زغلولة (Docx)",
            data=word_file,
            file_name=f"تقرير_زغلولة_{datetime.now().strftime('%d_%m')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    st.markdown("---")
    st.markdown("<center>تطوير المهندس محمد جمال | 2026</center>", unsafe_allow_html=True)

else:
    st.info("يا هندسة، ارفع ملف المبيعات من القائمة الجانبية عشان نبدأ التحليل.")
