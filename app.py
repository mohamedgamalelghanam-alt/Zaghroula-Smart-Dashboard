import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="داشبورد زغلولة الذكية", layout="wide")

# --- وظيفة إنشاء الـ PDF الاحترافي (حل مشكلة اليونيكود) ---
def create_pdf(data, total_sales, total_profit, branch_name):
    pdf = FPDF()
    pdf.add_page()
    
    # تنظيف اسم الفرع من أي حروف غير مدعومة لتجنب الـ Error
    try:
        # بنحاول نخلي الاسم إنجليزي لو أمكن أو نكتب "Zaghroula" كبديل
        clean_branch = "Zaghroula Branch" if "زغلولة" in branch_name else branch_name
        # إزالة أي حروف يونيكود قد تسبب مشكلة في التشفير الافتراضي
        clean_branch = clean_branch.encode('ascii', 'ignore').decode('ascii')
        if not clean_branch.strip(): clean_branch = "Main Branch"
    except:
        clean_branch = "Daily Report"

    # الهيدر
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "Zaghroula Daily Sales Report", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(190, 10, f"Branch: {clean_branch}", ln=True, align='C')
    pdf.cell(190, 10, f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
    pdf.ln(10)
    
    # كروت الأرقام
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(95, 12, f"Total Sales: {total_sales:,.2f} EGP", border=1, fill=True)
    pdf.cell(95, 12, f"Net Profit: {total_profit:,.2f} EGP", border=1, fill=True, ln=True)
    pdf.ln(10)
    
    # جدول البيانات (أول 20 صنف)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(30, 10, "ID", border=1)
    pdf.cell(80, 10, "Sales (EGP)", border=1)
    pdf.cell(80, 10, "Profit (EGP)", border=1, ln=True)
    
    pdf.set_font("Arial", '', 10)
    for i, row in data.head(20).iterrows():
        pdf.cell(30, 8, f"{i+1}", border=1)
        pdf.cell(80, 8, f"{row['Total_Sales']:,.2f}", border=1)
        pdf.cell(80, 8, f"{row['Net_Profit']:,.2f}", border=1, ln=True)
        
    return pdf.output()

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
            
        # استخراج اسم الفرع
        branch = df['الفرع'].dropna().iloc[0] if 'الفرع' in df.columns else "الفرع الرئيسي"
        
        df_sales = df.dropna(subset=['رقم الفاتورة']).copy()
        df_sales = df_sales[~df_sales['الصنف'].str.contains('اجمالى|وارد', na=False)]
        
        for col in ['الكمية', 'السعر', 'س شراء', 'الكمية المتبقية']:
            df_sales[col] = pd.to_numeric(df_sales[col].astype(str).str.replace('×', '').str.replace('x', '').str.strip(), errors='coerce')
        
        df_sales['س شراء'] = df_sales['س شراء'].fillna(0)
        df_sales['Total_Sales'] = df_sales['الكمية'] * df_sales['السعر']
        df_sales['Net_Profit'] = df_sales['Total_Sales'] - df_sales['س شراء']
        return df_sales, branch

    data, branch = load_and_clean(uploaded_file)

    # 3. عرض المؤشرات الرئيسية (نفس الـ UI المفضل ليك)
    st.subheader(f"📍 فرع: {branch}")
    col1, col2, col3 = st.columns(3)
    t_sales = data['Total_Sales'].sum()
    t_profit = data['Net_Profit'].sum()
    
    col1.metric("💰 إجمالي المبيعات", f"{t_sales:,.2f} ج.م")
    col2.metric("📈 صافي الأرباح", f"{t_profit:,.2f} ج.م")
    
    low_stock = data[data['الكمية المتبقية'] <= 5]
    col3.metric("🚨 أصناف ناقصة", f"{len(low_stock['الصنف'].unique())}")

    # --- سيكشن تحميل التقرير (PDF) ---
    st.markdown("### 📥 تحميل التقارير")
    try:
        pdf_bytes = create_pdf(data, t_sales, t_profit, branch)
        st.download_button(
            label="📄 تحميل التقرير بصيغة PDF",
            data=pdf_bytes,
            file_name=f"Zaghroula_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"حدث خطأ أثناء إنشاء PDF: {e}")

    # 4. الرسوم البيانية
    st.markdown("### 🔝 تحليل الأصناف")
    c1, c2 = st.columns(2)
    
    with c1:
        top_profit = data.groupby('الصنف')['Net_Profit'].sum().sort_values(ascending=False).head(10)
        fig_profit = px.bar(top_profit, x=top_profit.values, y=top_profit.index, orientation='h', 
                             title="أعلى 10 أصناف ربحية", labels={'x':'الربح', 'y':'الصنف'})
        st.plotly_chart(fig_profit, use_container_width=True)

    with c2:
        top_qty = data.groupby('الصنف')['الكمية'].sum().sort_values(ascending=False).head(10)
        fig_qty = px.pie(values=top_qty.values, names=top_qty.index, title="توزيع الكميات المباعة")
        st.plotly_chart(fig_qty, use_container_width=True)

    # 5. جدول النواقص
    st.markdown("### 🛒 قائمة المشتريات المطلوبة (النواقص)")
    if not low_stock.empty:
        st.warning("الأصناف دي قربت تخلص من المحل:")
        st.dataframe(low_stock[['الصنف', 'الكمية المتبقية']].drop_duplicates(), use_container_width=True)
    else:
        st.success("المخزن تمام، مفيش نواقص!")
