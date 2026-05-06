import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Zaghloula Dashboard", layout="wide")
st.title("📊 Zaghloula Smart Dashboard")

file = st.file_uploader("ارفع ملف مبيعات السبت", type=["xlsx", "xls", "csv"])

if file:
    try:
        # 1. قراءة الملف
        try:
            df = pd.read_excel(file)
        except:
            df = pd.read_csv(file, encoding='cp1256')

        # 2. تنظيف أسماء الأعمدة من أي مسافات
        df.columns = [str(c).strip() for c in df.columns]

        # 3. فلترة البيانات (أهم خطوة للوصول للرقم الحقيقي)
        # هنشيل أي صف فيه كلمة "بيع" أو "اجمالى" أو "إجمالي" أو خلايا فاضية في اسم الصنف
        if 'صنف' in df.columns:
            df = df.dropna(subset=['صنف'])
            df = df[~df['صنف'].astype(str).str.contains('بيع|اجمالى|إجمالي', na=False)]

        # 4. تحويل الأعمدة لأرقام حقيقية
        for c in ['قيمة', 'إجمالي ربح', 'كمية']:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

        # 5. الحسابات النهائية
        sales = df['قيمة'].sum()
        profit = df['إجمالي ربح'].sum()

        # العرض الفخم
        st.success("✅ تم تنقية البيانات وحساب الأرباح الحقيقية")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("💰 إجمالي المبيعات (الدرج)", f"{sales:,.2f} ج.م")
        with c2:
            st.metric("📈 صافي الأرباح (الفكّة)", f"{profit:,.2f} ج.م")

        # رسم بياني لأعلى الأصناف ربحاً عشان تتأكد إن الأرقام منطقية
        st.subheader("🚀 أكتر 10 أصناف كسبتك النهاردة")
        top_10 = df.groupby('صنف')['إجمالي ربح'].sum().sort_values(ascending=False).head(10).reset_index()
        fig = px.bar(top_10, x='إجمالي ربح', y='صنف', orientation='h', color='إجمالي ربح', color_continuous_scale='Viridis')
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"حدث خطأ: {e}")
else:
    st.info("ارفع ملف السبت يا هندسة عشان نطلع الأرقام الصح")
