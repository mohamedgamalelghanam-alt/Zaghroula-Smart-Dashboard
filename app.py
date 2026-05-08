import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Zaghloula - Day 1 Analysis", layout="wide")
st.title("📊 نظام زغلولة - تحليل الداتا الشامل (Day 1)")

uploaded_file = st.sidebar.file_uploader("ارفع ملف Data Set Day 1", type=["csv", "xlsx"])

if uploaded_file:
    try:
        # 1. قراءة الملف مع معالجة اللغة العربية
        df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
    except:
        df = pd.read_csv(uploaded_file, encoding='cp1256')

    # 2. تنظيف الأعمدة (الملف ده أسماء أعمدته كتير جداً)
    df.columns = [str(c).strip() for c in df.columns]

    # 3. تحديد الأعمدة الأساسية بناءً على محتوى ملفك (Day 1)
    # المبيعات غالباً في العمود رقم 3 أو 4 (حسب الملف)
    # إحنا هندور على الأعمدة اللي فيها قيم عددية
    
    # تحويل كل الأعمدة الممكنة لأرقام عشان نعرف نشتغل
    numeric_df = df.apply(pd.to_numeric, errors='coerce').fillna(0)
    
    # في ملف Day 1: 
    # العمود "قيمة" هو رقم 5 والربح رقم 6 (بناءً على المعاينة)
    sales_col = df.columns[5] # القيمة
    profit_col = df.columns[6] # إجمالي ربح
    name_col = df.columns[2] # الصنف

    # تنظيف الصفوف الوهمية
    df = df.dropna(subset=[name_col])
    df = df[~df[name_col].astype(str).str.contains('بيع|إجمالي|اجمالى', na=False)]

    # تحويل القيم المختارة لأرقام
    df['Actual_Sales'] = pd.to_numeric(df[sales_col], errors='coerce').fillna(0)
    df['Actual_Profit'] = pd.to_numeric(df[profit_col], errors='coerce').fillna(0)

    # 4. الحسابات
    total_sales = df['Actual_Sales'].sum()
    total_profit = df['Actual_Profit'].sum()

    # 5. العرض
    st.markdown("### 📈 خلاصة داتا اليوم الأول")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("💰 إجمالي المبيعات", f"{total_sales:,.2f} ج.م")
    with c2:
        st.metric("📈 صافي الأرباح", f"{total_profit:,.2f} ج.م")
    with c3:
        margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
        st.metric("🎯 هامش الربح", f"{margin:.1f}%")

    st.markdown("---")
    
    # رسم بياني لأفضل الأصناف
    col_left, col_right = st.columns(2)
    with col_left:
        top_10 = df.groupby(name_col)['Actual_Profit'].sum().sort_values(ascending=False).head(10).reset_index()
        fig = px.bar(top_10, x='Actual_Profit', y=name_col, orientation='h', 
                     title="أعلى 10 أصناف ربحية", color='Actual_Profit', color_continuous_scale='Reds')
        st.plotly_chart(fig, use_container_width=True)
        
    with col_right:
        st.write("### 📋 عينة البيانات المحللة")
        st.dataframe(df[[name_col, 'Actual_Sales', 'Actual_Profit']].head(10))

    st.markdown("---")
    st.markdown("<center>تطوير المهندس محمد جمال | 2026</center>", unsafe_allow_html=True)

else:
    st.warning("يا هندسة، ارفع ملف (Data Set Day 1) اللي معاك دلوقتي عشان ننجز!")
