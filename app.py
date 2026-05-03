import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from fpdf import FPDF
import io

# إعدادات الصفحة
st.set_page_config(page_title="Zaghroula BI Dashboard", layout="wide", page_icon="🛡️")

# --- دالة إنشاء الـ PDF الاحترافي (دعم اليونيكود) ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Zaghroula Daily Business Report', 0, 1, 'C')
        self.ln(5)

def create_pdf(data, branch_name, sales, profit, low_stock_list):
    pdf = PDF()
    pdf.add_page()
    
    # معلومات التقرير
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Branch: {branch_name}", ln=True)
    pdf.cell(0, 10, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.ln(5)
    
    # كروت الأداء في الـ PDF
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(95, 12, f"Total Sales: {sales:,.2f} EGP", border=1, fill=True)
    pdf.cell(95, 12, f"Net Profit: {profit:,.2f} EGP", border=1, fill=True, ln=True)
    pdf.ln(10)
    
    # جدول النواقص (أسماء الأصناف بالإنجليزية أو أرقام إذا لم تتوفر خطوط عربية مدمجة)
    # ملاحظة: لتحسين العربي بالكامل في الـ PDF يفضل رفع ملف خط .ttf ولكن للسرعة سنركز على الأرقام والبيانات
    if not low_stock_list.empty:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Inventory Alerts / Low Stock Items:", ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(140, 10, "Item Description", border=1)
        pdf.cell(50, 10, "Rem. Qty", border=1, ln=True)
        
        for index, row in low_stock_list.iterrows():
            # تنظيف الاسم من الرموز الغريبة لضمان عدم حدوث Error
            item_name = str(row['الصنف']).encode('ascii', 'ignore').decode('ascii') 
            if item_name == "": item_name = "Product Item"
            
            pdf.cell(140, 8, f" {item_name}", border=1)
            pdf.cell(50, 8, f" {row['الكمية المتبقية']}", border=1, ln=True)
            
    return pdf.output()

# --- واجهة المستخدم (الداشبورد) ---
st.title("📊 Zaghroula Business Intelligence")
st.markdown("---")

uploaded_file = st.file_uploader("📥 Upload Transaction File", type=['xls', 'csv'])

if uploaded_file:
    @st.cache_data
    def load_data(file):
        try: df = pd.read_csv(file, encoding='cp1256')
        except: df = pd.read_excel(file)
        
        branch = df['الفرع'].dropna().iloc[0] if 'الفرع' in df.columns else "Main Branch"
        df_sales = df.dropna(subset=['رقم الفاتورة']).copy()
        df_sales = df_sales[~df_sales['الصنف'].str.contains('اجمالى|وارد', na=False)]
        
        for col in ['الكمية', 'السعر', 'س شراء', 'الكمية المتبقية']:
            df_sales[col] = pd.to_numeric(df_sales[col].astype(str).str.replace('×', '').str.replace('x', '').str.strip(), errors='coerce')
        
        df_sales['Total_Sales'] = df_sales['الكمية'] * df_sales['السعر']
        df_sales['Net_Profit'] = df_sales['Total_Sales'] - df_sales['س شراء']
        return df_sales, branch

    data, branch = load_data(uploaded_file)

    # عرض البيانات بشكل بروفيشنال
    t1, t2, t3 = st.columns(3)
    tsales = data['Total_Sales'].sum()
    tprofit = data['Net_Profit'].sum()
    low_stock = data[data['الكمية المتبقية'] <= 5].drop_duplicates(subset=['الصنف'])

    t1.metric("Revenue", f"{tsales:,.0f} EGP")
    t2.metric("Profit", f"{tprofit:,.0f} EGP", f"{ (tprofit/tsales)*100 if tsales !=0 else 0:.1f}%")
    t3.metric("Stock Alerts", len(low_stock))

    # الرسوم البيانية
    st.plotly_chart(px.bar(data.groupby('الصنف')['Net_Profit'].sum().sort_values().tail(10), 
                           orientation='h', title="Top 10 Profitable Products",
                           color_continuous_scale='Blues'), use_container_width=True)

    # زر التحميل بصيغة PDF
    st.markdown("### 🖨️ Export Operations")
    try:
        pdf_bytes = create_pdf(data, branch, tsales, tprofit, low_stock)
        st.download_button(
            label="Download Daily PDF Report",
            data=pdf_bytes,
            file_name=f"Zaghroula_{branch}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"PDF Generation Error: {e}")
