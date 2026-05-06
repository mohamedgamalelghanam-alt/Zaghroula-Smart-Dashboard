import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Zaghloula Smart Dashboard", layout="wide")
st.title("📊 نظام زغلولة للتحليل الذكي")

file = st.file_uploader("ارفع ملف مبيعات السبت", type=["xlsx", "xls", "csv"])

if file:
    try:
        # 1. قراءة الملف بأفضل وسيلة ممكنة
        try:
            df = pd.read_excel(file)
        except:
            df = pd.read_csv(file, encoding='cp1256')

        # 2. تنقية الصفوف (حذف صف "بيع" والصفوف الفاضية)
        # بنمسح أول صفين لو فيهم رموز أو كلمات مش مفهومة
        df = df.dropna(how='all').reset_index(drop=True)
        
        # 3. الوصول للأعمدة عن طريق "الترتيب" (Index) لضمان الدقة
        # عمود الصنف غالباً رقم 2، القيمة رقم 5، الربح رقم 6 (حسب ملفك)
        # بنعمل تنظيف لأسماء الأعمدة برضه احتياطي
        df.columns = [str(c).strip() for c in df.columns]
        
        # دالة ذكية لإيجاد الأعمدة حتى لو الأسماء مشوهة
        def find_col(keywords):
            for i, col in enumerate(df.columns):
                if any(key in col for key in keywords):
                    return col
            return None

        c_name = find_col(['صنف', 'الصنف']) or df.columns[2]
        c_val = find_col(['قيمة', 'القيمة', 'صافي']) or df.columns[5]
        c_profit = find_col(['ربح', 'الربح']) or df.columns[6]

        # 4. تحويل البيانات لأرقام وفلترة الصفوف الوهمية
        df[c_val] = pd.to_numeric(df[c_val], errors='coerce').fillna(0)
        df[c_profit] = pd.to_numeric(df[c_profit], errors='coerce').fillna(0)
        
        # فلترة: أي صف ربحه وصافي مبيعاته صفر (صفوف وهمية) نمسحه
        df = df[(df[c_val] > 0) | (df[c_profit] > 0)]
        df = df[~df[c_name].astype(str).str.contains('بيع|إجمالي|اجمالى', na=False)]

        # 5. النتائج اللي بنستناها
        total_sales = df[c_val].sum()
        total_profit = df[c_profit].sum()

        st.success("✅ تم تحليل البيانات بنجاح")
        col1, col2 = st.columns(2)
        col1.metric("💰 إجمالي مبيعات السبت", f"{total_sales:,.2f} ج.م")
        col2.metric("📈 صافي أرباح السبت", f"{total_profit:,.2f} ج.م")

        # الرسم البياني
        st.subheader("🚀 أعلى 10 أصناف مكسباً")
        top_10 = df.groupby(c_name)[c_profit].sum().sort_values(ascending=False).head(10).reset_index()
        fig = px.bar(top_10, x=c_profit, y=c_name, orientation='h', color=c_profit, color_continuous_scale='Greens')
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"حدث خطأ بسيط، برجاء التأكد من الملف: {e}")
else:
    st.info("يا هندسة ارفع الملف عشان الأرقام الحقيقية تظهر")
