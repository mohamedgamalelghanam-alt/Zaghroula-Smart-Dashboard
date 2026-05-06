import streamlit as st
import pandas as pd

st.set_page_config(page_title="Zaghloula Smart Dashboard", layout="wide")
st.title("📊 Zaghloula Smart Dashboard")

file = st.file_uploader("ارفع ملف مبيعات السبت", type=["xlsx", "xls", "csv"])

if file:
    try:
        # قراءة الملف
        try:
            df = pd.read_excel(file)
        except:
            df = pd.read_csv(file, encoding='cp1256')

        # تنظيف أسماء الأعمدة (أهم خطوة)
        df.columns = [str(c).strip() for c in df.columns]

        # التأكد من وجود الأعمدة المطلوبة
        if 'قيمة' in df.columns and 'إجمالي ربح' in df.columns:
            # تحويل الأرقام
            df['قيمة'] = pd.to_numeric(df['قيمة'], errors='coerce').fillna(0)
            df['إجمالي ربح'] = pd.to_numeric(df['إجمالي ربح'], errors='coerce').fillna(0)
            
            # حساب الإجماليات
            sales = df['قيمة'].sum()
            profit = df['إجمالي ربح'].sum()

            # العرض
            c1, c2 = st.columns(2)
            c1.metric("💰 إجمالي المبيعات", f"{sales:,.2f} ج.م")
            c2.metric("📈 صافي الأرباح", f"{profit:,.2f} ج.م")
            
            st.write("### عينة من البيانات:")
            st.dataframe(df[['صنف', 'قيمة', 'إجمالي ربح']].head(20))
        else:
            st.error(f"الأعمدة مش مظبوطة. الأعمدة اللي السيستم شايفها هي: {list(df.columns)}")
            
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
else:
    st.info("ارفع ملف مبيعات السبت عشان الداشبورد تشتغل")
