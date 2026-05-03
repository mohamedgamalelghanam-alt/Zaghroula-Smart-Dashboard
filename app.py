import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from fpdf import FPDF
import base64

# إعدادات الصفحة الاحترافية
st.set_page_config(page_title="Zaghroula Business Intelligence", layout="wide", page_icon="📊")

# --- تحسين المظهر (Custom CSS) ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    h1 { color: #1E3A8A; font-family: 'Arial'; }
    </style>
    """, unsafe_allow_html=True)

# --- دالة إنشاء الـ PDF ---
def create_pdf(data, branch_name, sales, profit, low_stock_list):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    
    # العنوان
    pdf.cell(190, 10, f"Daily Performance Report - {branch_name}", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(190, 10, f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
    pdf.ln(10)
    
    # ملخص الأرقام
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(95, 10, f"Total Sales: {sales:,.2f} EGP", border=1)
    pdf.cell(95, 10, f"Net Profit: {profit:,.2f} EGP", border=1, ln=True)
    pdf.ln(10)
    
    # جدول النواقص (لو وجد)
    if not low_stock_list.empty:
        pdf.set_text_color(255, 0, 0)
        pdf.cell(190, 10, "Inventory Alerts (Low Stock):", ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", '', 10)
        for index, row in low_stock_list.iterrows():
            pdf.cell(190, 8, f"- {row['الصنف']}: Remaining ({row['الكمية المتبقية']})", ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- الجزء الرئيسي للبرنامج ---
st.title("🛡️ Zaghroula BI Dashboard")

uploaded_file = st.file_uploader("📥 Upload Daily Transaction File", type=['xls', 'csv'])

if uploaded_file:
    # وظيفة التنظيف
    @st.cache_data
    def load_data(file):
        try: df = pd.read_csv(file, encoding='cp1256')
        except: df = pd.read_excel(file)
        
        branch = df['الفرع'].dropna().iloc[0] if 'الفرع' in df.columns else "Main Branch"
        df_sales = df.dropna(subset=['رقم الفاتورة']).copy()
        df_sales = df_sales[~df_sales['الصنف'].str.contains('اجمالى|وارد', na=False)]
        
        for col in ['الكمية', 'السعر', 'س شراء', 'الكمية المتبقية']:
            df_sales[col] = pd.to_numeric(df_sales[col].astype(str).str.replace('×', '').str.replace('x', '').str.strip(), errors='coerce')
        
        df_sales['Net_Profit'] = (df_sales['الكمية'] * df_sales['السعر']) - df_sales['س شراء']
        df_sales['Total_Sales'] = df_sales['الكمية'] * df_sales['السعر']
        return df_sales, branch

    data, branch = load_data(uploaded_file)

    # الهيدر الاحترافي
    st.subheader(f"📍 Location: {branch}")
    
    # كروت المؤشرات
    m1, m2, m3, m4 = st.columns(4)
    total_sales = data['Total_Sales'].sum()
    total_profit = data['Net_Profit'].sum()
    low_stock = data[data['الكمية المتبقية'] <= 5].drop_duplicates(subset=['الصنف'])
    
    m1.metric("Revenue", f"{total_sales:,.0f} EGP")
    m2.metric("Net Profit", f"{total_profit:,.0f} EGP", delta=f"{(total_profit/total_sales)*100:.1f}% Margin")
    m3.metric("Items Sold", len(data))
    m4.metric("Low Stock Alerts", len(low_stock))

    st.markdown("---")

    # الرسوم البيانية
    col_left, col_right = st.columns([6, 4])
    
    with col_left:
        top_items = data.groupby('الصنف')['Net_Profit'].sum().sort_values(ascending=False).head(10)
        fig = px.bar(top_items, x=top_items.values, y=top_items.index, orientation='h', 
                     title="Top 10 Profitable Items", color=top_items.values, color_continuous_scale='Viridis')
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        # زرار تحميل الـ PDF الاحترافي
        st.markdown("### 📄 Export Report")
        pdf_data = create_pdf(data, branch, total_sales, total_profit, low_stock)
        st.download_button(
            label="Download Official PDF Report",
            data=pdf_data,
            file_name=f"Zaghroula_Report_{branch}_{datetime.now().strftime('%Y-%m-%d')}.pdf",
            mime="application/pdf"
        )
        
        if not low_stock.empty:
            st.error("⚠️ Immediate Stock Refill Required")
            st.table(low_stock[['الصنف', 'الكمية المتبقية']].head(10))
