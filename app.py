import streamlit as st
import pandas as pd
import plotly.express as px

# 1. إعداد الصفحة
st.set_page_config(page_title="📊 Zaghloula Smart Dashboard", layout="wide")

# 2. دالة المعالجة المحصنة ضد الإيرورات
@st.cache_data
def load_data(file):
    try:
        df = pd.read_excel(file)
    except:
        df = pd.read_csv(file, encoding='cp1256')

    # حذف الصفوف اللي بتبوظ الدنيا (زي صف كلمة بيع)
    if 'صنف' in df.columns:
        df = df.dropna(subset=['صنف'])
        df = df[df['صنف'].astype(str).str.contains('بيع') == False]
    
    # التأكد من تحويل الأرقام صح
    cols = ['كمية', 'سعر', 'قيمة', 'سعر التكلفة', 'الرصيد الحالي']
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # الحسبة بناءً على أعمدة ملف السبت
    if 'قيمة' in df.columns:
        df['Total_Sales'] = df['قيمة']
        # الحسبة: البيع - (الكمية × سعر التكلفة)
        df['Net_Profit'] = df['Total_Sales'] - (df['كمية'] * df['سعر التكلفة'])
    else:
        df['Total_Sales'] = 0
        df['Net_Profit'] = 0

    # تحديد الفرع
    branch = "الفرع الرئيسي"
    if 'الفرع' in df.columns: branch = df['الفرع'].iloc[0]

    return df, branch

# 3. واجهة المستخدم
st.title("📊 Zaghloula Smart Dashboard")

with st.sidebar:
    st.header("🛒 زغلولة")
    uploaded_file = st.file_uploader("ارفع ملف مبيعات السبت", type=["xlsx", "xls", "csv"])

if uploaded_file:
    # السطر 81 اللي كان بيضرب (تم إصلاحه)
    data, branch = load_data(uploaded_file)
    
    # الأرقام الرئيسية
    t_sales = data['Total_Sales'].sum()
    t_profit = data['Net_Profit'].sum()
    
    st.success(f"✅ تم تحميل البيانات بنجاح - {branch}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 إجمالي المبيعات", f"{t_sales:,.2f} ج.م")
    col2.metric("📈 صافي الأرباح", f"{t_profit:,.2f} ج.م")
    
    if 'الرصيد الحالي' in data.columns:
        low_stock = data[data['الرصيد الحالي'] <= 5]
        col3.metric("⚠️ نواقص المخزن", len(low_stock))

    # الرسوم البيانية
    tab1, tab2 = st.tabs(["📊 التحليل المالي", "📋 الدليل التشغيلي"])
    
    with tab1:
        top_10 = data.groupby('صنف')['Net_Profit'].sum().sort_values(ascending=False).head(10).reset_index()
        st.plotly_chart(px.bar(top_10, x='Net_Profit', y='صنف', orientation='h', title="أعلى 10 أصناف ربحية"))

    with tab2:
        st.markdown(f"""
        ### **دليل الاستخدام الرسمي (المهندس محمد جمال)**
        * **المعادلة:** يتم طرح التكلفة (الكمية × سعر التكلفة) من إجمالي القيمة.
        * **تنبيه:** تم تجاهل الصفوف غير المحاسبية لضمان دقة الـ {t_profit:,.2f} جنيه أرباح.
        """)

    # التوقيع
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: gray;'>تطوير المهندس محمد جمال | 01029796096</div>", unsafe_allow_html=True)
else:
    st.info("ارفع ملف (مبيعات السبت.xls.xlsx) عشان السيستم يشتغل.")
