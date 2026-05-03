import streamlit as st
import pandas as pd

st.title("📊 داشبورد زغلولة (النسخة النهائية)")

# رفع الملف
uploaded_file = st.file_uploader("ارفع الملف اللي طالع من السيستم", type=['xls', 'csv', 'xlsx'])

if uploaded_file:
    # محاولة القراءة بكل الطرق الممكنة (عشان الملف بتاعك خداع)
    try:
        # بنجرب نقرأه كـ CSV أولاً بترميز العربي
        df = pd.read_csv(uploaded_file, encoding='cp1256')
    except:
        # لو منفعش بنقرأه كإكسيل عادي
        df = pd.read_excel(uploaded_file)

    # 1. تنظيف البيانات من "الوارد" و "الاجمالى" وأي صف ملوش لازمة
    # لازم نحذف الصفوف اللي فيها "وارد" أو "اجمالى" في عمود الصنف
    df = df.dropna(subset=['الصنف', 'الكمية', 'السعر', 'س شراء'])
    df = df[~df['الصنف'].str.contains('وارد|اجمالى|بيع نقدي', na=False)]

    # 2. تحويل البيانات لأرقام
    for col in ['الكمية', 'السعر', 'س شراء']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 3. الحسبة المنضبطة (الزيتونة)
    df['إجمالي_البيع'] = df['الكمية'] * df['السعر']
    df['صافي_الربح'] = df['إجمالي_البيع'] - df['س شراء']

    # 4. النتائج النهائية
    total_sales = df['إجمالي_البيع'].sum()
    total_profit = df['صافي_الربح'].sum()

    st.success(f"تم تحليل البيانات لفرع: {df['الفرع'].iloc[0] if 'الفرع' in df.columns else 'الرئيسي'}")
    
    col1, col2 = st.columns(2)
    col1.metric("💰 إجمالي المبيعات", f"{total_sales:,.2f} ج.م")
    col2.metric("📈 صافي الأرباح", f"{total_profit:,.2f} ج.م")

    st.divider()
    st.subheader("📝 مراجعة سريعة للأصناف")
    st.dataframe(df[['الصنف', 'الكمية', 'السعر', 'س شراء', 'صافي_الربح']])
