import streamlit as st
import pandas as pd
import plotly.express as px
from docx import Document
from io import BytesIO
from datetime import datetime

# ---------------------------------------------------
# إعداد الصفحة والعنوان الجديد
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
# وظيفة معالجة الملف (حل مشكلة الإيرور)
# ---------------------------------------------------
@st.cache_data
def load_data(file):
    # هنا حل كسم الإيرور: بنجرب كل الطرق عشان نفتح الملف الخداع ده
    try:
        # المحاولة الأولى: قراءة كـ CSV بترميز العربي (ده اللي بينفع مع ملفات السيستم دي)
        df = pd.read_csv(file, encoding='cp1256')
    except:
        try:
            # المحاولة الثانية: قراءة كإكسيل عادي
            df = pd.read_excel(file)
        except:
            # المحاولة الثالثة: CSV بترميز تاني لو الأول فشل
            df = pd.read_csv(file, encoding='utf-8', errors='ignore')

    df = df.copy()
    
    # تحديد الفرع من المخزن أو الفرع
    branch = "الفرع الرئيسي"
    if "الفرع" in df.columns: branch = df["الفرع"].dropna().iloc[0]
    elif "المخزن" in df.columns: branch = df["المخزن"].dropna().iloc[0]

    # تنظيف الصفوف اللي بتبوظ الحسابات (وارد واجمالى)
    unwanted = ["وارد", "اجمالى", "إجمالي", "بيع نقدي"]
    df = df.dropna(subset=['الصنف'])
    df = df[~df['الصنف'].astype(str).str.contains("|".join(unwanted), na=False)]

    # تحويل الأعمدة لأرقام عشان الجمع والطرح
    cols = ["الكمية", "السعر", "س شراء", "الكمية المتبقية"]
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # --- الحسبة الصح اللي بتطلع الـ 800 جنيه ---
    df['Total_Sales'] = df['الكمية'] * df['السعر']
    df['Net_Profit'] = df['Total_Sales'] - df['س شراء']
    
    # نسبة الربح عشان السكشن الجديد
    df['Margin'] = (df['Net_Profit'] / df['س شراء'].replace(0, 1)) * 100

    return df, branch

# ---------------------------------------------------
# الواجهة الجانبية (Sidebar)
# ---------------------------------------------------
with st.sidebar:
    st.markdown("## 🛒 زغلولة")
    uploaded_file = st.file_uploader("ارفع ملف المبيعات هنا", type=["csv", "xls", "xlsx"])

# ---------------------------------------------------
# التطبيق الرئيسي
# ---------------------------------------------------
st.title("📊 Zaghloula Smart Dashboard")

if uploaded_file:
    data, branch = load_data(uploaded_file)
    
    # الفلترة
    selected = st.selectbox("اختر صنف معين للمراجعة", ["الكل"] + sorted(list(data["الصنف"].unique())))
    f_data = data.copy()
    if selected != "الكل":
        f_data = f_data[f_data["الصنف"] == selected]

    # الحسابات
    t_sales = f_data["Total_Sales"].sum()
    t_profit = f_data["Net_Profit"].sum()
    low_stock = f_data[f_data["الكمية المتبقية"] <= 5]
    
    # سكشن المراجعة (الخسارة والربح البسيط)
    at_loss = f_data[f_data['Net_Profit'] < 0]
    low_margin = f_data[(f_data['Net_Profit'] >= 0) & (f_data['Margin'] < 5)]

    # التابات
    t1, t2, t3 = st.tabs(["📈 الملخص", "📦 المخزن والمراجعة", "📋 دليل الاستخدام"])

    with t1:
        st.info(f"📍 يتم الآن عرض بيانات: {branch}")
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="card"><h2>إجمالي المبيعات</h2><h1>{t_sales:,.2f} ج.م</h1></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="card"><h2>صافي الأرباح</h2><h1>{t_profit:,.2f} ج.م</h1></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="card"><h2>نواقص المخزن</h2><h1>{len(low_stock)}</h1></div>', unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            top = f_data.groupby("الصنف")["Net_Profit"].sum().sort_values(ascending=False).head(10).reset_index()
            st.plotly_chart(px.bar(top, x="Net_Profit", y="الصنف", orientation='h', title="أعلى 10 أصناف ربحية"), use_container_width=True)
        with col_b:
            st.plotly_chart(px.treemap(f_data, path=["الصنف"], values="Total_Sales", title="توزيع المبيعات"), use_container_width=True)

    with t2:
        st.subheader("⚠️ أصناف تحتاج مراجعة فورية")
        col_1, col_2 = st.columns(2)
        with col_1:
            st.error(f"❌ أصناف بخسارة ({len(at_loss)})")
            st.dataframe(at_loss[['الصنف', 'Net_Profit']], use_container_width=True)
        with col_2:
            st.warning(f"📉 ربح ضعيف أقل من 5% ({len(low_margin)})")
            st.dataframe(low_margin[['الصنف', 'Net_Profit']], use_container_width=True)
        
        st.subheader("📦 النواقص (أقل من 5 قطع/كيلو)")
        st.dataframe(low_stock[['الصنف', 'الكمية المتبقية']], use_container_width=True)

    with t3:
        st.write("ارفع ملف الإكسيل أو الـ CSV اللي طالع من السيستم والبرنامج هيقوم بالباقي.")

    # التوقيع البسيط الشيك
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: gray; font-size: 14px;'>تطوير المهندس محمد جمال | 01029796096</div>", unsafe_allow_html=True)

else:
    st.info("مستني ترفع الملف عشان نبدأ يا هندسة..")
