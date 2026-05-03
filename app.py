import streamlit as st
import pandas as pd
import plotly.express as px
from docx import Document
from io import BytesIO
from datetime import datetime

# ---------------------------------------------------
# إعداد الصفحة والعنوان
# ---------------------------------------------------
st.set_page_config(
    page_title="📊 Zaghloula Smart Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------
# التنسيق (CSS)
# ---------------------------------------------------
st.markdown("""
<style>
.main { background-color: #f8f9fa; }
.card {
    padding: 20px;
    border-radius: 15px;
    background: white;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    text-align: center;
}
.card h2 { color: #2c3e50; font-size: 18px; margin-bottom: 10px; }
.card h1 { color: #27ae60; font-size: 26px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# وظيفة معالجة الملف
# ---------------------------------------------------
@st.cache_data
def load_data(file):
    try:
        df = pd.read_csv(file, encoding='cp1256')
    except:
        try:
            df = pd.read_excel(file)
        except:
            df = pd.read_csv(file, encoding='utf-8', errors='ignore')

    df = df.copy()
    branch = "الفرع الرئيسي"
    if "الفرع" in df.columns: branch = df["الفرع"].dropna().iloc[0]
    elif "المخزن" in df.columns: branch = df["المخزن"].dropna().iloc[0]

    unwanted = ["وارد", "اجمالى", "إجمالي", "بيع نقدي"]
    df = df.dropna(subset=['الصنف'])
    df = df[~df['الصنف'].astype(str).str.contains("|".join(unwanted), na=False)]

    cols = ["الكمية", "السعر", "س شراء", "الكمية المتبقية"]
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df['Total_Sales'] = df['الكمية'] * df['السعر']
    df['Net_Profit'] = df['Total_Sales'] - df['س شراء']
    df['Margin'] = (df['Net_Profit'] / df['س شراء'].replace(0, 1)) * 100

    return df, branch

# ---------------------------------------------------
# Sidebar
# ---------------------------------------------------
with st.sidebar:
    st.markdown("## 🛒 زغلولة")
    uploaded_file = st.file_uploader("ارفع ملف المبيعات", type=["csv", "xls", "xlsx"])

# ---------------------------------------------------
# Main App
# ---------------------------------------------------
st.title("📊 Zaghloula Smart Dashboard")

if uploaded_file:
    data, branch = load_data(uploaded_file)
    selected = st.selectbox("تصفية البيانات حسب الصنف", ["الكل"] + sorted(list(data["الصنف"].unique())))
    f_data = data.copy()
    if selected != "الكل":
        f_data = f_data[f_data["الصنف"] == selected]

    t_sales = f_data["Total_Sales"].sum()
    t_profit = f_data["Net_Profit"].sum()
    low_stock = f_data[f_data["الكمية المتبقية"] <= 5]
    at_loss = f_data[f_data['Net_Profit'] < 0]
    low_margin = f_data[(f_data['Net_Profit'] >= 0) & (f_data['Margin'] < 5)]

    t1, t2, t3 = st.tabs(["📈 التحليل المالي", "📦 الرقابة والمخزون", "📘 وثيقة دليل الاستخدام"])

    with t1:
        st.info(f"📍 بيانات الفرع الحالي: {branch}")
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="card"><h2>إجمالي قيمة المبيعات</h2><h1>{t_sales:,.2f} ج.م</h1></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="card"><h2>صافي الأرباح التشغيلية</h2><h1>{t_profit:,.2f} ج.م</h1></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="card"><h2>تنبيهات نقص المخزون</h2><h1>{len(low_stock)}</h1></div>', unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            top = f_data.groupby("الصنف")["Net_Profit"].sum().sort_values(ascending=False).head(10).reset_index()
            st.plotly_chart(px.bar(top, x="Net_Profit", y="الصنف", orientation='h', title="مؤشر أعلى 10 أصناف ربحية"), use_container_width=True)
        with col_b:
            st.plotly_chart(px.treemap(f_data, path=["الصنف"], values="Total_Sales", title="الهيكل النسبي للمبيعات"), use_container_width=True)

    with t2:
        st.subheader("⚠️ الأصناف الخاضعة للمراجعة")
        col_1, col_2 = st.columns(2)
        with col_1:
            st.error(f"❌ أصناف تحقق خسارة رأس مالية ({len(at_loss)})")
            st.dataframe(at_loss[['الصنف', 'Net_Profit']], use_container_width=True)
        with col_2:
            st.warning(f"📉 أصناف ذات هامش ربح منخفض < 5% ({len(low_margin)})")
            st.dataframe(low_margin[['الصنف', 'Net_Profit']], use_container_width=True)
        
        st.subheader("📦 حالة المخزن (النواقص)")
        st.dataframe(low_stock[['الصنف', 'الكمية المتبقية']], use_container_width=True)

    # --- دليل الاستخدام الرسمي ---
    with t3:
        st.header("📘 الدليل التشغيلي للنظام")
        st.markdown("""
        ### **1. مقدمة عن النظام**
        يعمل نظام **Zaghloula Smart Dashboard** كأداة تحليلية متقدمة تهدف إلى تحويل سجلات البيع الخام إلى مؤشرات أداء مالية دقيقة، لمساعدة الإدارة في اتخاذ قرارات مبنية على البيانات.

        ### **2. معالجة البيانات (Data Processing)**
        *   **التنقية الآلية:** يقوم النظام باستبعاد العمليات غير التشغيلية (مثل حركات الوارد أو الإجماليات اليدوية) لضمان دقة النتائج.
        *   **التوافقية:** النظام مهيأ للتعامل مع ملفات السيستم بترميز (CP1256) لضمان قراءة اللغة العربية بشكل سليم دون أخطاء برمجية.

        ### **3. المنهجية الحسابية**
        *   **إجمالي المبيعات:** يتم حسابه بناءً على (الكمية المباعة × سعر البيع الفعلي).
        *   **صافي الربح:** يتم استخراجه بطرح (سعر الشراء الكلي) من (إجمالي المبيعات) لكل صنف على حدة.
        *   **تحليل الهوامش:** يقوم النظام برصد الأصناف التي يقل هامش ربحها عن **5%** لتنبيه الإدارة بضرورة مراجعة سياسة التسعير.

        ### **4. الرقابة على المخزون**
        يعتمد النظام معياراً حسابياً لرصد النواقص، حيث يتم إدراج أي صنف تقل كميته المتبقية عن **5 وحدات** ضمن قائمة التنبيهات الفورية.

        ---
        *تم تطوير هذا المستند البرمجي لضمان أعلى معايير الدقة والشفافية في العرض المالي.*
        """)

    st.markdown("---")
    st.markdown("<div style='text-align: center; color: gray; font-size: 14px;'>تطوير المهندس محمد جمال | 01029796096</div>", unsafe_allow_html=True)

else:
    st.info("يرجى رفع ملف البيانات لبدء عملية التحليل المالي.")
