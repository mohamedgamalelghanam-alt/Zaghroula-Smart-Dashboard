import streamlit as st
import pandas as pd
try:
    import plotly.express as px
except ImportError:
    st.error("جاري تحميل المكتبات... يرجى الانتظار دقيقة وعمل ريفريش.")

st.set_page_config(page_title="Zaghloula Dashboard", layout="wide")
st.title("📊 Zaghloula Smart Dashboard")

file = st.file_uploader("ارفع ملف مبيعات السبت", type=["xlsx", "xls", "csv"])

if file:
    try:
        # قراءة الملف
        try:
            df = pd.read_excel(file)
        except:
            df = pd.read_csv(file, encoding='cp1256')

        # تنظيف أسماء الأعمدة
        df.columns = [str(c).strip() for c in df.columns]

        if 'قيمة' in df.columns and 'إجمالي ربح' in df.columns:
            # تحويل الأرقام
            df['قيمة'] = pd.to_numeric(df['قيمة'], errors='coerce').fillna(0)
            df['إجمالي ربح'] = pd.to_numeric(df['إجمالي ربح'], errors='coerce').fillna(0)
            
            sales = df['قيمة'].sum()
            profit = df['إجمالي ربح'].sum()

            c1, c2 = st.columns(2)
            c1.metric("💰 إجمالي المبيعات", f"{sales:,.2f} ج.م")
            c2.metric("📈 صافي الأرباح", f"{profit:,.2f} ج.م")
            
            # رسم بياني بسيط لو plotly اشتغلت
            if 'صنف' in df.columns:
                top = df.groupby('صنف')['إجمالي ربح'].sum().sort_values(ascending=False).head(10).reset_index()
                fig = px.bar(top, x='إجمالي ربح', y='صنف', orientation='h', title="أعلى 10 أصناف ربحية")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"الأعمدة ناقصة. الموجود: {list(df.columns)}")
    except Exception as e:
        st.error(f"خطأ: {e}")
