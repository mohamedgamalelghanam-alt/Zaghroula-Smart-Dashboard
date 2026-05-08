import streamlit as st
import pandas as pd
import plotly.express as px
from docx import Document
from io import BytesIO
from datetime import datetime

# 1. إعدادات الصفحة والستايل (الخلفية والهايلايت)
st.set_page_config(page_title="داشبورد زغلولة الذكية", layout="wide")

st.markdown("""
<style>
    /* خلفية مائية بكلمة زغلولة */
    .main {
        background-color: #f8f9fa;
        background-image: url("https://www.transparenttextures.com/patterns/cubes.png");
    }
    .main::before {
        content: "ZAGHLOULA";
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) rotate(-30deg);
        font-size: 10vw;
        color: rgba(0, 0, 0, 0.03);
        z-index: -1;
        font-weight: bold;
    }
    .stMetric { background: white; padding: 15px; border-radius: 15px; shadow: 0 4px 6px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

# --- وظيفة إنشاء ملف الوورد ---
def create_word_report(data, t_sales, t_profit, branch):
    doc = Document()
    doc.add_heading(f'تقرير مبيعات زغلولة: {branch}', 0)
    doc.add_paragraph(f'تاريخ التقرير: {datetime.now().strftime("%Y-%m-%d")}')
    doc.add_heading('الملخص المالي', level=1)
    doc.add_paragraph(f'إجمالي المبيعات: {t_sales:,.2f} جنيه')
    doc.add_paragraph(f'صافي الربح: {t_profit:,.2f} جنيه')
    
    table = doc.add_table(rows=1, cols=3)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'الصنف'
    hdr_cells[1].text = 'المبيعات'
    hdr_cells[2].text = 'الربح'
    
    for _, row in data.head(20).iterrows():
        row_cells = table.add_row().cells
        row_cells[0].text = str(row['الصنف'])
        row_cells[1].text = f"{row['Total_Sales']:,.2f}"
        row_cells[2].text = f"{row['Net_Profit']:,.2f}"
        
    target = BytesIO()
    doc.save(target)
    return target.getvalue()

# --- واجهة الداشبورد ---
st.title("📊 نظام زغلولة لإدارة البيانات والتحليل")

# 2. سيكشن شرح الموقع (User Guide)
with st.expander("📘 دليل استخدام النظام - اقرأني أولاً"):
    st.markdown("""
    **أهلاً بك في نظام زغلولة الذكي! اتبع الخطوات التالية لتحليل بياناتك:**
    1. ارفع ملف المبيعات (CSV أو Excel) من القائمة الجانبية أو خانة الرفع.
    2. تأكد أن الملف يحتوي على أعمدة (الصنف، الكمية، السعر، س شراء).
    3. سيقوم النظام تلقائياً بتنظيف البيانات وحذف الكلمات الزائدة مثل 'وارد' أو 'اجمالي'.
    4. استخدم التبويبات بالأسفل لمتابعة المبيعات، النواقص، والأصناف التي تحتاج إعادة تسعير.
    5. يمكنك تحميل تقرير Word رسمي بضغطة زر واحدة.
    """)

uploaded_file = st.file_uploader("ارفع ملف مبيعات اليوم", type=['xls', 'csv', 'xlsx'])

if uploaded_file:
    @st.cache_data
    def load_and_clean(file):
        try:
            df = pd.read_csv(file, encoding='utf-8-sig')
        except:
            try:
                df = pd.read_csv(file, encoding='cp1256')
            except:
                df = pd.read_excel(file)
                
        df.columns = [str(c).strip() for c in df.columns]
        branch = df['الفرع'].dropna().iloc[0] if 'الفرع' in df.columns else "الفرع الرئيسي"
        
        # تنظيف البيانات
        df_sales = df.dropna(subset=['الصنف']).copy()
        df_sales = df_sales[~df_sales['الصنف'].astype(str).str.contains('اجمالى|وارد|بيع نقدي', na=False)]
        
        # تحويل الأرقام (معالجة علامة ×)
        for col in ['الكمية', 'السعر', 'س شراء', 'الكمية المتبقية']:
            if col in df_sales.columns:
                df_sales[col] = pd.to_numeric(df_sales[col].astype(str).str.replace('×', '').str.replace('x', '').str.strip(), errors='coerce').fillna(0)
        
        # الحسابات
        df_sales['Total_Sales'] = df_sales['الكمية'] * df_sales['السعر']
        # الربح = (سعر البيع - سعر التكلفة) * الكمية
        df_sales['Net_Profit'] = (df_sales['السعر'] - df_sales['س شراء']) * df_sales['الكمية']
        
        return df_sales, branch

    data, branch = load_and_clean(uploaded_file)

    # المؤشرات الرئيسية
    st.subheader(f"📍 فرع: {branch}")
    t_sales = data['Total_Sales'].sum()
    t_profit = data['Net_Profit'].sum()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 إجمالي المبيعات", f"{t_sales:,.2f} ج.م")
    col2.metric("📈 صافي الأرباح", f"{t_profit:,.2f} ج.م")
    low_stock = data[data['الكمية المتبقية'] <= 5]
    col3.metric("🚨 أصناف ناقصة", f"{len(low_stock['الصنف'].unique())}")

    # التبويبات (Tabs) لتنظيم العرض
    tab1, tab2, tab3 = st.tabs(["📊 التحليل العام", "⚠️ مراجعة التسعير (الخسارة)", "🛒 المخزن والنواقص"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            top_p = data.groupby('الصنف')['Net_Profit'].sum().sort_values(ascending=False).head(10)
            st.plotly_chart(px.bar(top_p, orientation='h', title="أعلى 10 أصناف ربحية", color_discrete_sequence=['#27ae60']), use_container_width=True)
        with c2:
            top_q = data.groupby('الصنف')['Total_Sales'].sum().sort_values(ascending=False).head(10)
            st.plotly_chart(px.pie(values=top_q.values, names=top_q.index, title="توزيع حجم المبيعات"), use_container_width=True)
        
        # تحميل الوورد
        word_file = create_word_report(data, t_sales, t_profit, branch)
        st.download_button("📝 تحميل التقرير الرسمي (Word)", data=word_file, file_name=f"تقرير_زغلولة.docx")

    with tab2:
        # 3. سيكشن الأصناف الخاسرة (إعادة التسعير)
        st.subheader("⚠️ أصناف تباع بأقل من سعر التكلفة")
        # الصنف خاسر لو سعر البيع أقل من س الشراء
        loss_items = data[data['السعر'] < data['س شراء']][['الصنف', 'س شراء', 'السعر', 'Net_Profit']].drop_duplicates()
        
        if not loss_items.empty:
            st.warning("هذه الأصناف تسبب خسارة مباشرة في كل قطعة مباعة. يرجى مراجعة الأسعار فوراً!")
            st.dataframe(loss_items.style.background_gradient(subset=['Net_Profit'], cmap='Reds'), use_container_width=True)
        else:
            st.success("ممتاز! جميع الأصناف مسعرة أعلى من سعر التكلفة.")

    with tab3:
        st.subheader("🛒 قائمة النواقص")
        st.dataframe(low_stock[['الصنف', 'الكمية المتبقية']].drop_duplicates(), use_container_width=True)

    # التوقيع
    st.markdown("---")
    st.markdown('<div style="text-align: center; color: #7f8c8d;">تطوير المهندس محمد جمال | 01029796096</div>', unsafe_allow_html=True)
else:
    st.info("يرجى رفع ملف المبيعات من الأعلى لبدء التحليل.")
