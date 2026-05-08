import streamlit as st
import pandas as pd
import plotly.express as px
from docx import Document
from io import BytesIO
from datetime import datetime
import re

# 1. إعدادات الصفحة والستايل المريح للعين
st.set_page_config(page_title="Zaghloula Smart Dashboard", layout="wide", page_icon="☕")

st.markdown("""
<style>
    .main { background-color: #ffffff; }
    /* علامة مائية هادئة جداً وغير مؤثرة على القراءة */
    .main::before {
        content: "ZAGHLOULA";
        position: fixed; top: 50%; left: 50%;
        transform: translate(-50%, -50%) rotate(-30deg);
        font-size: 10vw; color: rgba(0,0,0,0.01);
        z-index: -1; font-weight: bold;
    }
    .metric-card {
        background: #f9f9f9; padding: 20px; border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #eee; text-align: center;
    }
    h2 { color: #555; font-size: 1rem; }
    h1 { font-size: 1.8rem; color: #2c3e50; }
</style>
""", unsafe_allow_html=True)

# وظيفة إنشاء الوورد
def create_word_report(data, t_sales, t_profit):
    doc = Document()
    doc.add_heading('تقرير مبيعات زغلولة اليومي', 0)
    doc.add_paragraph(f'تاريخ التقرير: {datetime.now().strftime("%Y-%m-%d")}')
    doc.add_heading('الملخص المالي', level=1)
    doc.add_paragraph(f'المبيعات: {t_sales:,.2f} ج.م | الأرباح: {t_profit:,.2f} ج.م')
    table = doc.add_table(rows=1, cols=3); table.style = 'Table Grid'
    hdr = table.rows[0].cells; hdr[0].text, hdr[1].text, hdr[2].text = 'الصنف', 'المبيعات', 'الربح'
    for _, row in data.head(20).iterrows():
        c = table.add_row().cells
        c[0].text, c[1].text, c[2].text = str(row['الصنف']), f"{row['Total_Sales']:,.2f}", f"{row['Net_Profit']:,.2f}"
    target = BytesIO(); doc.save(target)
    return target.getvalue()

st.title("☕ داشبورد زغلولة (نسخة العمل اليومي)")

uploaded_file = st.sidebar.file_uploader("ارفع ملف الداتا", type=['xls', 'csv', 'xlsx'])

if uploaded_file:
    try:
        # قراءة الملف بكل الاحتمالات
        try: df = pd.read_excel(uploaded_file)
        except:
            uploaded_file.seek(0)
            try: df = pd.read_csv(uploaded_file, encoding='cp1256')
            except: 
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding='utf-8-sig')

        df.columns = [str(c).strip() for c in df.columns]

        def clean_val(x):
            if pd.isna(x): return 0
            val = re.sub(r'[^\d.]', '', str(x))
            try: return float(val)
            except: return 0

        # تحديد الأعمدة
        col_item = 'الصنف' if 'الصنف' in df.columns else df.columns[2]
        col_qty = 'الكمية' if 'الكمية' in df.columns else df.columns[3]
        col_price = 'السعر' if 'السعر' in df.columns else df.columns[4]
        col_cost = 'س شراء' if 'س شراء' in df.columns else (df.columns[5] if len(df.columns) > 5 else None)
        col_stock = 'الكمية المتبقية' if 'الكمية المتبقية' in df.columns else None

        df['الصنف'] = df[col_item].astype(str)
        df['Qty'] = df[col_qty].apply(clean_val)
        df['Price'] = df[col_price].apply(clean_val)
        df['Cost'] = df[col_cost].apply(clean_val) if col_cost else df['Price'] * 0.7
        df['Stock'] = df[col_stock].apply(clean_val) if col_stock else 10 # افتراض لو مش موجود

        df['Total_Sales'] = df['Qty'] * df['Price']
        df['Net_Profit'] = (df['Price'] - df['Cost']) * df['Qty']

        df_final = df[df['Total_Sales'] > 0].copy()
        df_final = df_final[~df_final['الصنف'].str.contains('اجمالى|وارد|فاتورة', na=False)]

        # عرض الكروت
        ts, tp = df_final['Total_Sales'].sum(), df_final['Net_Profit'].sum()
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="metric-card"><h2>💰 مبيعات اليوم</h2><h1>{ts:,.0f} ج.م</h1></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card"><h2>📈 صافي الربح</h2><h1 style="color:#2980b9">{tp:,.0f} ج.م</h1></div>', unsafe_allow_html=True)
        with c3:
            low_stock_count = len(df_final[df_final['Stock'] <= 5])
            st.markdown(f'<div class="metric-card"><h2>🚨 أصناف للنواقص</h2><h1 style="color:#e74c3c">{low_stock_count}</h1></div>', unsafe_allow_html=True)

        st.divider()
        
        tab1, tab2, tab3 = st.tabs(["📊 التحليل العام", "🛒 قائمة النواقص", "📝 التقارير"])
        
        with tab1:
            st.plotly_chart(px.bar(df_final.groupby('الصنف')['Total_Sales'].sum().nlargest(10).reset_index(), 
                                   x='Total_Sales', y='الصنف', orientation='h', title="أكثر 10 أصناف مبيعاً"))
        
        with tab2:
            st.subheader("📦 بضاعة لازم تطلبها (رصيد أقل من 5)")
            low_stock_items = df_final[df_final['Stock'] <= 5][['الصنف', 'Stock']].drop_duplicates()
            if not low_stock_items.empty:
                st.dataframe(low_stock_items.rename(columns={'Stock': 'الكمية المتبقية'}), use_container_width=True)
            else:
                st.success("كل بضاعتك تمام، مفيش حاجة ناقصة!")

        with tab3:
            st.download_button("📥 تحميل تقرير Word", data=create_word_report(df_final, ts, tp), file_name="Zagh_Report.docx")

    except Exception as e:
        st.error(f"خطأ في البيانات: {e}")
else:
    st.info("ارفع ملف المبيعات يا هندسة عشان نظهر لك النواقص والأرباح.")
