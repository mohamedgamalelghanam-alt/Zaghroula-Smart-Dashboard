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
    doc.add_paragraph(f'صافي الأرباح: {t_profit:,.2f} جنيه')
    
    doc.add_heading('أعلى الأصناف ربحية', level=1)
    table = doc.add_table(rows=1, cols=3)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'الصنف'
    hdr_cells[1].text = 'المبيعات'
    hdr_cells[2].text = 'صافي الربح'
    
    for _, row in data.head(15).iterrows():
        row_cells = table.add_row().cells
        row_cells[0].text = str(row['الصنف'])
        row_cells[1].text = f"{row['Total_Sales']:,.2f}"
        row_cells[2].text = f"{row['Net_Profit']:,.2f}"
        
    target = BytesIO()
    doc.save(target)
    return target.getvalue()

# --- واجهة المستخدم ---
st.title("📊 نظام تحليل مبيعات زغلولة الذكي")

# --- سكشن دليل الاستخدام (User Guide) ---
with st.expander("📖 دليل استخدام الداشبورد - اقرأني إذا كنت تحتاج مساعدة"):
    st.markdown("""
    ### كيف يعمل النظام؟
    1. **رفع الملف:** قم برفع ملف الإكسيل المستخرج من نظام المبيعات (بصيغة `xls` أو `csv`).
    2. **المعالجة الذكية:** يقوم النظام تلقائياً بتنظيف البيانات، وحساب الأرباح بناءً على (سعر البيع - سعر الشراء) مضروباً في الكمية.
    3. **المؤشرات:** 
        * **إجمالي المبيعات:** مجموع الفلوس اللي دخلت الدرج.
        * **صافي الأرباح:** الفائدة الحقيقية بعد خصم تكلفة البضاعة.
        * **الأصناف الناقصة:** تنبيه للأصناف التي رصيدها أقل من 5 قطع.
    4. **التقارير:** يمكنك تحميل تقرير Word رسمي لطباعته أو حفظه.
    """)

st.markdown("---")

uploaded_file = st.file_uploader("📥 ارفع ملف مبيعات اليوم", type=['xls', 'csv'])

if uploaded_file:
    @st.cache_data
    def load_and_clean(file):
        try:
            df = pd.read_csv(file, encoding='cp1256')
        except:
            df = pd.read_excel(file)
            
        branch = df['الفرع'].dropna().iloc[0] if 'الفرع' in df.columns else "الفرع الرئيسي"
        
        # تنظيف البيانات
        df_sales = df.dropna(subset=['رقم الفاتورة']).copy()
        df_sales = df_sales[~df_sales['الصنف'].str.contains('اجمالى|وارد', na=False)]
        
        # تحويل الأعمدة لأرقام
        for col in ['الكمية', 'السعر', 'س شراء', 'الكمية المتبقية']:
            df_sales[col] = pd.to_numeric(df_sales[col].astype(str).str.replace('×', '').str.replace('x', '').str.strip(), errors='coerce')
        
        df_sales['س شراء'] = df_sales['س شراء'].fillna(0)
        
        # --- حل مشكلة الربح (الزيتونة هنا) ---
        df_sales['Total_Sales'] = df_sales['الكمية'] * df_sales['السعر']
        # الربح = (سعر البيع - سعر الشراء) * الكمية
        df_sales['Net_Profit'] = (df_sales['السعر'] - df_sales['س شراء']) * df_sales['الكمية']
        
        return df_sales, branch

    data, branch = load_and_clean(uploaded_file)

    # عرض المؤشرات
    st.subheader(f"📍 فرع: {branch}")
    m1, m2, m3 = st.columns(3)
    t_sales = data['Total_Sales'].sum()
    t_profit = data['Net_Profit'].sum()
    
    m1.metric("💰 إجمالي المبيعات", f"{t_sales:,.2f} ج.م")
    m2.metric("📈 صافي الأرباح", f"{t_profit:,.2f} ج.م", delta=f"{((t_profit/t_sales)*100) if t_sales !=0 else 0:.1f}% هامش ربح")
    
    low_stock = data[data['الكمية المتبقية'] <= 5].drop_duplicates(subset=['الصنف'])
    m3.metric("🚨 أصناف قربت تخلص", f"{len(low_stock)}")

    # التحليلات البيانية
    st.markdown("### 📊 تحليل الأداء")
    c1, c2 = st.columns([6, 4])
    
    with c1:
        top_p = data.groupby('الصنف')['Net_Profit'].sum().sort_values(ascending=False).head(10)
        fig_p = px.bar(top_p, orientation='h', title="أعلى 10 أصناف تحقيقاً للربح", 
                       labels={'value':'الربح بالجنيه', 'الصنف':''}, color_continuous_scale='Viridis')
        st.plotly_chart(fig_p, use_container_width=True)
        
    with c2:
        st.markdown("#### 📝 تحميل التقرير")
        word_file = create_word_report(data.sort_values(by='Net_Profit', ascending=False), t_sales, t_profit, branch)
        st.download_button(
            label="📝 تحميل التقرير الرسمي (Word)",
            data=word_file,
            file_name=f"Zaghroula_Report_{datetime.now().strftime('%Y%m%d')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        if not low_stock.empty:
            st.error("⚠️ قائمة النواقص")
            st.dataframe(low_stock[['الصنف', 'الكمية المتبقية']], hide_index=True)

    st.markdown("---")
    st.caption("تم التطوير بواسطة محمد جمال - AI Engineer")
