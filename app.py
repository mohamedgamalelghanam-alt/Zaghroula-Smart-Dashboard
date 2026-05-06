import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Zaghloula Dashboard", layout="wide")
st.title("📊 نظام زغلولة للتحليل الدقيق")

file = st.file_uploader("ارفع ملف مبيعات السبت", type=["xlsx", "xls", "csv"])

if file:
    try:
        # 1. قراءة الملف
        df = pd.read_excel(file) if file.name.endswith(('xlsx', 'xls')) else pd.read_csv(file, encoding='cp1256')

        # 2. تنظيف شامل لأسماء الأعمدة (شيل أي رموز غريبة أو مسافات)
        df.columns = [str(c).strip() for c in df.columns]

        # 3. تحديد الأعمدة "بالاسم" أو "بالمحتوى الرقمي"
        # بنحاول نلاقي العمود اللي فيه أرقام مبيعات وأرقام أرباح
        def fix_numeric_col(keywords):
            for col in df.columns:
                if any(k in col for k in keywords):
                    # التأكد إن العمود فيه أرقام مش نصوص (زي التاريخ أو الاسم)
                    converted = pd.to_numeric(df[col], errors='coerce')
                    if converted.notna().sum() > len(df) / 2: # لو أكتر من نص العمود أرقام يبقى هو ده
                        return col
            return None

        col_val = fix_numeric_col(['قيمة', 'صافي', 'قيمه'])
        col_profit = fix_numeric_col(['ربح', 'الربح'])
        col_name = next((c for c in df.columns if 'صنف' in c), df.columns[2])

        if col_val and col_profit:
            # 4. تنظيف الصفوف الوهمية (مثل صف "بيع")
            df = df.dropna(subset=[col_name])
            df = df[~df[col_name].astype(str).str.contains('بيع|إجمالي|اجمالى', na=False)]

            # تحويل القيم لأرقام حقيقية
            df[col_val] = pd.to_numeric(df[col_val], errors='coerce').fillna(0)
            df[col_profit] = pd.to_numeric(df[col_profit], errors='coerce').fillna(0)

            # 5. الحسابات النهائية
            total_sales = df[col_val].sum()
            total_profit = df[col_profit].sum()

            # العرض
            st.success("✅ تم ضبط الأعمدة وحساب الأرقام الحقيقية")
            c1, c2 = st.columns(2)
            c1.metric("💰 إجمالي المبيعات", f"{total_sales:,.2f} ج.م")
            c2.metric("📈 صافي الأرباح", f"{total_profit:,.2f} ج.م")

            # الرسم البياني
            top_10 = df.groupby(col_name)[col_profit].sum().sort_values(ascending=False).head(10).reset_index()
            fig = px.bar(top_10, x=col_profit, y=col_name, orientation='h', color=col_profit, title="أعلى الأصناف ربحية")
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.error("السيستم مش قادر يحدد أعمدة الأرقام. اتأكد إن أسماء الأعمدة (قيمة) و (إجمالي ربح) واضحة.")

    except Exception as e:
        st.error(f"خطأ في القراءة: {e}")
else:
    st.info("ارفع الملف يا هندسة عشان نصلح التشفير ده")
