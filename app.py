import streamlit as st
import pandas as pd
import plotly.express as px
from docx import Document
from io import BytesIO
from datetime import datetime
import re  # تعريف مكتبة المسح (عشان إيرور re اللي ظهر)

# 1. إعدادات الصفحة والستايل الاحترافي
st.set_page_config(page_title="Zaghloula Smart Dashboard", layout="wide", page_icon="☕")

st.markdown("""
<style>
    .main { background-color: #fcfcfc; }
    .main::before {
        content: "ZAGHLOULA";
        position: fixed; top: 50%; left: 50%;
        transform: translate(-50%, -50%) rotate(-30deg);
        font-size: 8vw; color: rgba(0,0,0,0.02);
        z-index: -1; font-weight: bold;
    }
    .metric-card {
        background: white; padding: 25px; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-top: 5px solid #27ae60; text-align: center;
    }
    .metric-card.profit { border-top: 5px solid #2980b9; }
    .metric-card.loss { border-top: 5px solid #e74c3c; }
    h2 { color: #2c3e50; font-size: 1.1rem; margin-bottom: 10px; }
    h1 { font-size: 2rem; margin: 0; color: #1e272e; }
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

# --- واجهة التطبيق ---
st.title("☕ نظام زغلولة للتحليل الذكي (النسخة النهائية)")
st.markdown("---")

uploaded_file = st.sidebar.file_uploader("(Day 1) ارفع ملف الداتا", type=['xls', 'csv', 'xlsx'])

if uploaded_file:
    try:
        # محاولة قراءة الملف بكل الطرق الممكنة (حل مشكلة No columns to parse)
        try:
            df = pd.read_excel(uploaded_file)
        except:
            uploaded_file.seek(0)
            try: df = pd.read_csv(uploaded_file, encoding='cp1256')
            except: 
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding='utf-8-sig')

        # تنظيف أسماء الأعمدة
        df.columns = [str(c).strip() for c in df.columns]

        # دالة تنظيف الأرقام من الرموز (×, *)
        def clean_val(x):
            if pd.isna(x): return 0
            val = re.sub(r'[^\d.]', '', str(x))
            try: return float(val)
            except: return 0

        # تحديد الأعمدة الأساسية (الاسم، الكمية، السعر، التكلفة)
        # هنستخدم الترتيب لو الأسماء مش واضحة
        col_item = 'الصنف' if 'الصنف' in df.columns else df.columns[2]
        col_qty = 'الكمية' if 'الكمية' in df.columns else df.columns[3]
        col_price = 'السعر' if 'السعر' in df.columns else df.columns[4]
        col_cost = 'سعر التكلفة' if 'سعر التكلفة' in df.columns else (df.columns[5] if len(df.columns) > 5 else None)

        df['الصنف'] = df[col_item].astype(str)
        df['Qty'] = df[col_qty].apply(clean_val)
        df['Price'] = df[col_price].apply(clean_val)
        
        if col_cost:
            df['Cost'] = df[col_cost].apply(clean_val)
        else:
            df['Cost'] = df['Price'] * 0.8  # افتراض تكلفة 80% لو العمود مش موجود

        # الحسابات
        df['Total_Sales'] = df['Qty'] * df['Price']
        df['Net_Profit'] = (df['Price'] - df['Cost']) * df['Qty']

        # فلترة البيانات الحقيقية فقط
        df_final = df[df['Total_Sales'] > 0].copy()
        df_final = df_final[~df_final['الصنف'].str.contains('اجمالى|وارد|فاتورة', na=False)]

        # عرض الكروت
        ts, tp = df_final['Total_Sales'].sum(), df_final['Net_Profit'].sum()
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="metric-card"><h2>💰 إجمالي المبيعات</h2><h1 style="color:#27ae60">{ts:,.2f}</h1></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card profit"><h2>📈 صافي الربح</h2><h1 style="color:#2980b9">{tp:,.2f}</h1></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card loss"><h2>📦 عدد الأصناف</h2><h1>{len(df_final)}</h1></div>', unsafe_allow_html=True)

        st.divider()
        
        tab1, tab2, tab3 = st.tabs(["📊 رسوم بيانية", "⚠️ مراجعة التسعير", "📝 التقرير"])
        
        with tab1:
            st.plotly_chart(px.bar(df_final.groupby('الصنف')['Net_Profit'].sum().nlargest(10).reset_index(), 
                                   x='Net_Profit', y='الصنف', orientation='h', title="أعلى 10 أصناف ربحية"))
        
        with tab2:
            loss_items = df_final[df_final['Price'] < df_final['Cost']]
            if not loss_items.empty:
                st.warning("انتبه! هذه الأصناف تُباع بأقل من تكلفتها:")
                st.dataframe(loss_items[['الصنف', 'Cost', 'Price', 'Net_Profit']])
            else:
                st.success("ممتاز! لا يوجد أصناف خاسرة.")

        with tab3:
            st.info("حمل التقرير الرسمي لمشاركته أو طباعته")
            word_file = create_word_report(df_final, ts, tp, "فرع زغلولة")
            st.download_button("📥 تحميل تقرير Docx", data=word_file, file_name="Zagh_Report.docx")

    except Exception as e:
        st.error(f"حصلت مشكلة في قراءة الملف: {e}")
else:
    st.info("يا هندسة ارفع ملف الداتا عشان نبدأ.")

st.markdown("<br><center>تطوير المهندس محمد جمال | 01029796096</center>", unsafe_allow_html=True)
