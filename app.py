import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Zaghloula Day 1 - Emergency", layout="wide")
st.title("📊 نظام زغلولة - تحليل الداتا الأولى (النسخة السريعة)")

uploaded_file = st.sidebar.file_uploader("ارفع ملف Day 1", type=["csv"])

if uploaded_file:
    try:
        # قراءة الملف بأكثر من طريقة لضمان فك التشفير
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
        except:
            df = pd.read_csv(uploaded_file, encoding='cp1256')

        # حذف الصفوف الفاضية تماماً
        df = df.dropna(how='all').reset_index(drop=True)

        # --- الحل الجذري: القراءة بالترتيب (Index) وليس بالاسم ---
        # بناءً على ملف "Day 1" اللي رفعته:
        # العمود رقم 2 هو الصنف
        # العمود رقم 3 هو الكمية
        # العمود رقم 4 هو السعر
        
        name_col = df.columns[2]
        qty_col = df.columns[3]
        price_col = df.columns[4]

        # تحويل الأرقام (تنظيف الداتا من أي رموز زي × أو *)
        def clean_number(val):
            if pd.isna(val): return 0
            val = str(val).replace(',', '').replace('×', '').replace('*', '').strip()
            try:
                return float(val)
            except:
                return 0

        df['Clean_Qty'] = df[qty_col].apply(clean_number)
        df['Clean_Price'] = df[price_col].apply(clean_number)
        
        # حساب المبيعات (كمية × سعر)
        df['Sales'] = df['Clean_Qty'] * df['Clean_Price']
        
        # حساب ربح تقديري (لو مفيش عمود ربح واضح، هنفترض نسبة 25% كمتوسط لمحلك)
        df['Profit'] = df['Sales'] * 0.25 

        # فلترة الصفوف اللي ملهاش لازمة
        df = df[df['Sales'] > 0]
        df = df[~df[name_col].astype(str).str.contains('وارد|إجمالي|اجمالى', na=False)]

        # الحسابات النهائية
        total_sales = df['Sales'].sum()
        total_profit = df['Profit'].sum()

        # العرض
        c1, c2 = st.columns(2)
        c1.metric("💰 إجمالي المبيعات (تقديري)", f"{total_sales:,.2f} ج.م")
        c2.metric("📈 صافي الأرباح (25% تقديري)", f"{total_profit:,.2f} ج.م")

        st.markdown("---")
        st.subheader("📋 مراجعة البيانات")
        st.write("الأصناف اللي تم قراءتها:")
        st.dataframe(df[[name_col, 'Clean_Qty', 'Clean_Price', 'Sales']].head(20))

    except Exception as e:
        st.error(f"حصلت مشكلة في قراءة الملف: {e}")
else:
    st.info("ارفع ملف Day 1 عشان نخلص يا هندسة!")

st.markdown("<center>تطوير المهندس محمد جمال</center>", unsafe_allow_html=True)
