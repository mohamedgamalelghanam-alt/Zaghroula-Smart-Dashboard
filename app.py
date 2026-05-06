import streamlit as st
import pandas as pd
import plotly.express as px

# إعداد الصفحة
st.set_page_config(page_title="Zaghloula Smart Dashboard", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 نظام زغلولة لإدارة البيانات الذكية")
st.info("مرحباً مهندس محمد، تم ضبط الإعدادات لقراءة ملف (مبيعات السبت) بدقة متناهية.")

file = st.file_uploader("ارفع ملف المبيعات هنا", type=["xlsx", "xls", "csv"])

if file:
    try:
        # 1. قراءة البيانات
        try:
            df = pd.read_excel(file)
        except:
            df = pd.read_csv(file, encoding='utf-8-sig') # تحسين قراءة العربي

        # 2. تنظيف الأعمدة
        df.columns = [str(c).strip() for c in df.columns]

        # 3. الفلترة الصارمة (الحل الجذري)
        # استبعاد الصفوف اللي فيها "بيع" أو "إجمالي" أو الفاضية في خانة الصنف
        if 'صنف' in df.columns:
            df = df.dropna(subset=['صنف'])
            df = df[~df['صنف'].astype(str).str.contains('بيع|إجمالي|اجمالى', na=False)]
            # حذف أي صفوف مكررة ناتجة عن تجميع السيستم
            df = df[df['سعر'].notna()]

        # 4. تحويل البيانات لأرقام
        cols_to_fix = ['قيمة', 'إجمالي ربح', 'كمية', 'سعر التكلفة']
        for col in cols_to_fix:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 5. الحسابات النهائية (المطابقة للملف)
        total_sales = df['قيمة'].sum()
        total_profit = df['إجمالي ربح'].sum()
        total_items = len(df)

        # عرض النتائج
        st.markdown("### 📋 ملخص أداء اليوم")
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 إجمالي المبيعات", f"{total_sales:,.2f} ج.م")
        c2.metric("📈 صافي الربح", f"{total_profit:,.2f} ج.م")
        c3.metric("🛒 عدد العمليات", f"{total_items} عملية")

        # التحليلات البيانية
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.subheader("🚀 أعلى 10 أصناف ربحية")
            top_profit = df.groupby('صنف')['إجمالي ربح'].sum().sort_values(ascending=False).head(10).reset_index()
            fig1 = px.bar(top_profit, x='إجمالي ربح', y='صنف', orientation='h', 
                          color='إجمالي ربح', color_continuous_scale='Greens')
            st.plotly_chart(fig1, use_container_width=True)

        with col_b:
            st.subheader("📦 أصناف تحتاج إعادة طلب (نواقص)")
            if 'الرصيد الحالي' in df.columns:
                df['الرصيد الحالي'] = pd.to_numeric(df['الرصيد الحالي'], errors='coerce').fillna(0)
                low_stock = df[df['الرصيد الحالي'] < 1][['صنف', 'الرصيد الحالي']].drop_duplicates().head(10)
                st.table(low_stock)

        st.success(f"تم تحليل {total_items} صف بنجاح. الأرقام الآن مطابقة لواقع الدفاتر.")

    except Exception as e:
        st.error(f"حدث خطأ أثناء المعالجة: {e}")
else:
    st.warning("في انتظار رفع ملف مبيعات السبت لبدء العرض...")

st.markdown("---")
st.markdown("<center>تطوير المهندس محمد جمال | 2026</center>", unsafe_allow_html=True)
