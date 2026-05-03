import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------
# إعداد الصفحة
# ---------------------------------------------------
st.set_page_config(
    page_title="📊 Zaghloula Smart Dashboard",
    layout="wide"
)

# ---------------------------------------------------
# دالة معالجة الملف (المصلحة تماماً)
# ---------------------------------------------------
@st.cache_data
def load_data(file):
    try:
        # محاولة القراءة كإكسيل
        df = pd.read_excel(file)
    except:
        # محاولة القراءة كـ CSV بترميز العربي
        df = pd.read_csv(file, encoding='cp1256')

    # تنظيف البيانات
    if 'صنف' in df.columns:
        df = df.dropna(subset=['صنف'])
        df = df[df['صنف'] != 'بيع']
    
    # تحديد الفرع (اختياري)
    branch_name = "الفرع الرئيسي"
    if 'الفرع' in df.columns:
        branch_name = df['الفرع'].dropna().iloc[0]
    elif 'المخزن' in df.columns:
        branch_name = df['المخزن'].dropna().iloc[0]

    # تحويل الأعمدة لأرقام
    cols_to_fix = ['كمية', 'سعر', 'قيمة', 'سعر التكلفة', 'الرصيد الحالي']
    for col in cols_to_fix:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # الحسابات الأساسية بناءً على ملف السبت
    if 'قيمة' in df.columns:
        df['Total_Sales'] = df['قيمة']
        if 'سعر التكلفة' in df.columns and 'كمية' in df.columns:
            df['Net_Profit'] = df['Total_Sales'] - (df['كمية'] * df['سعر التكلفة'])
        else:
            df['Net_Profit'] = 0
    
    return df, branch_name # بنرجع القيمتين عشان السطر 81 ميزعلش

# ---------------------------------------------------
# الواجهة
# ---------------------------------------------------
st.title("📊 Zaghloula Smart Dashboard")

with st.sidebar:
    st.markdown("### 🛒 زغلولة")
    uploaded_file = st.file_uploader("ارفع ملف المبيعات", type=["xlsx", "xls", "csv"])

if uploaded_file:
    # السطر 81 اللي كان فيه المشكلة
    data, branch = load_data(uploaded_file)
    
    # حسابات إجمالية
    total_sales = data['Total_Sales'].sum() if 'Total_Sales' in data.columns else 0
    total_profit = data['Net_Profit'].sum() if 'Net_Profit' in data.columns else 0
    
    # العرض العلوي
    st.info(f"📍 عرض بيانات: {branch}")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("💰 إجمالي المبيعات", f"{total_sales:,.2f} ج.م")
    with c2:
        st.metric("📈 صافي الأرباح", f"{total_profit:,.2f} ج.م")
    with c3:
        low_stock = data[data['الرصيد الحالي'] <= 5] if 'الرصيد الحالي' in data.columns else []
        st.metric("⚠️ نواقص المخزن", f"{len(low_stock)}")

    # التابات
    t1, t2, t3 = st.tabs(["📊 التحليل", "📦 المخزن", "📘 الدليل"])

    with t1:
        if 'صنف' in data.columns:
            top_10 = data.groupby('صنف')['Net_Profit'].sum().sort_values(ascending=False).head(10).reset_index()
            st.plotly_chart(px.bar(top_10, x='Net_Profit', y='صنف', orientation='h', title="أعلى 10 أصناف ربحية"))

    with t2:
        if 'الرصيد الحالي' in data.columns:
            st.subheader("الأصناف التي قاربت على النفاد")
            st.dataframe(data[data['الرصيد الحالي'] <= 5][['صنف', 'الرصيد الحالي']], use_container_width=True)

    with t3:
        st.markdown("### دليل التشغيل الرسمي")
        st.write("تم ضبط النظام ليتوافق مع أعمدة السيستم الحالية: صنف، قيمة، سعر التكلفة.")

    st.markdown("---")
    st.markdown("<div style='text-align: center; color: gray;'>تطوير المهندس محمد جمال | 01029796096</div>", unsafe_allow_html=True)
