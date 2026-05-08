import streamlit as st
import pandas as pd
import plotly.express as px

# 1. إعداد الصفحة بشكل احترافي
st.set_page_config(page_title="Zaghloula Smart Dashboard", layout="wide")

st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .card {
        padding: 20px; border-radius: 15px; background: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); text-align: center;
    }
    .card h2 { color: #2c3e50; font-size: 18px; margin-bottom: 10px; }
    .card h1 { color: #27ae60; font-size: 26px; }
</style>
""", unsafe_allow_html=True)

st.title("📊 نظام زغلولة للتحليل الذكي (النسخة النهائية)")

# 2. رفع الملف
uploaded_file = st.sidebar.file_uploader("ارفع ملف الداتا (Day 1)", type=['xls', 'csv', 'xlsx'])

if uploaded_file:
    try:
        # محاولة القراءة بكل الطرق لضمان فك تشفير اللغة العربية
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
        except:
            df = pd.read_csv(uploaded_file, encoding='cp1256')
        
        # تنظيف أولي للبيانات
        df = df.dropna(how='all').reset_index(drop=True)

        # 3. حل مشكلة "الرموز الغريبة" في الداتا الأولى
        # هنعتمد على ترتيب العواميد (Index) عشان نضمن الدقة
        # العمود 2: الصنف، العمود 3: الكمية، العمود 4: السعر، العمود 6: الربح (إن وجد)
        
        name_col = df.columns[2]
        qty_col = df.columns[3]
        price_col = df.columns[4]
        
        # دالة لتنظيف الأرقام من أي علامات (× أو * أو مسافات)
        def clean_val(x):
            if pd.isna(x): return 0
            val = str(x).replace('×', '').replace('*', '').replace(',', '').strip()
            try: return float(val)
            except: return 0

        # تطبيق التنظيف
        df['Qty_Clean'] = df[qty_col].apply(clean_val)
        df['Price_Clean'] = df[price_col].apply(clean_val)
        
        # 4. الحسبة المنضبطة (الريكويرمنتس)
        df['إجمالي_البيع'] = df['Qty_Clean'] * df['Price_Clean']
        
        # إذا كان هناك عمود للربح في الملف (غالباً رقم 6 في داتا زغلولة)
        if len(df.columns) > 6:
            profit_col = df.columns[6]
            df['صافي_الربح'] = df[profit_col].apply(clean_val)
        else:
            # افتراض نسبة ربح 25% لو العمود مش موجود
            df['صافي_الربح'] = df['إجمالي_البيع'] * 0.25

        # فلترة البيانات (إبعاد الوارد والإجماليات)
        df = df[df['إجمالي_البيع'] > 0]
        df = df[~df[name_col].astype(str).str.contains('وارد|اجمالى|بيع نقدي|إجمالي', na=False)]

        # 5. عرض النتائج النهائية في الكروت
        total_sales = df['إجمالي_البيع'].sum()
        total_profit = df['صافي_الربح'].sum()

        st.success("✅ تم تحليل البيانات بنجاح")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="card"><h2>💰 إجمالي المبيعات</h2><h1>{total_sales:,.2f} ج.م</h1></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="card"><h2>📈 صافي الأرباح</h2><h1>{total_profit:,.2f} ج.م</h1></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="card"><h2>📦 عدد الأصناف</h2><h1>{len(df)} صنف</h1></div>', unsafe_allow_html=True)

        st.divider()

        # 6. الرسم البياني (أفضل الأصناف)
        top_10 = df.groupby(name_col)['إجمالي_البيع'].sum().sort_values(ascending=False).head(10).reset_index()
        fig = px.bar(top_10, x='إجمالي_البيع', y=name_col, orientation='h', title="أعلى 10 أصناف مبيعاً", color='إجمالي_البيع', color_continuous_scale='Greens')
        st.plotly_chart(fig, use_container_width=True)

        # جدول المراجعة
        st.subheader("📝 مراجعة الأصناف")
        st.dataframe(df[[name_col, 'Qty_Clean', 'Price_Clean', 'إجمالي_البيع', 'صافي_الربح']].rename(columns={name_col: 'الصنف', 'Qty_Clean': 'الكمية', 'Price_Clean': 'سعر البيع'}))

    except Exception as e:
        st.error(f"حصلت مشكلة في قراءة الملف: {e}")

else:
    st.info("يا هندسة، ارفع ملف (Data Set Day 1) عشان نطلع الأرقام فوراً!")

# التوقيع
st.markdown("---")
st.markdown('<div style="text-align: center; color: gray;">تطوير المهندس محمد جمال | 01029796096</div>', unsafe_allow_html=True)
