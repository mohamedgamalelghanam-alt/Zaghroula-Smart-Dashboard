import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="Zaghloula Smart Dashboard", layout="wide")

st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .card {
        padding: 20px; border-radius: 15px; background: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); text-align: center;
    }
    .card h2 { color: #2c3e50; font-size: 18px; }
    .card h1 { color: #27ae60; font-size: 26px; }
</style>
""", unsafe_allow_html=True)

st.title("📊 داشبورد زغلولة (Day 1 - المصفاة)")

uploaded_file = st.sidebar.file_uploader("ارفع ملف Day 1", type=['csv', 'xlsx'])

if uploaded_file:
    try:
        # 1. القراءة بأمان
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
        except:
            df = pd.read_csv(uploaded_file, encoding='cp1256')
        
        df = df.dropna(how='all').reset_index(drop=True)

        # 2. تنظيف الأرقام (الزيتونة هنا)
        def extract_number(value):
            if pd.isna(value): return 0
            # بيمسح أي حاجة مش رقم أو علامة عشرية (بيمسح × و * والمسافات)
            clean_val = re.sub(r'[^\d.]', '', str(value))
            try:
                return float(clean_val)
            except:
                return 0

        # تحديد الأعمدة بالترتيب (2: صنف، 3: كمية، 4: سعر)
        name_col = df.columns[2]
        qty_col = df.columns[3]
        price_col = df.columns[4]

        df['Qty_Fixed'] = df[qty_col].apply(extract_number)
        df['Price_Fixed'] = df[price_col].apply(extract_number)
        
        # 3. الحسابات
        df['Sales'] = df['Qty_Fixed'] * df['Price_Fixed']
        # لو مفيش عمود ربح، هنحسب 20% كنسبة ربح افتراضية لليوم ده
        df['Profit'] = df['Sales'] * 0.20 

        # فلترة الصفوف الفاضية والوهمية
        df = df[df['Sales'] > 0]
        df = df[~df[name_col].astype(str).str.contains('وارد|إجمالي|اجمالى|????', na=False)]

        # 4. العرض
        total_sales = df['Sales'].sum()
        total_profit = df['Profit'].sum()

        st.success("✅ تم تنظيف البيانات وحساب المبيعات الحقيقية")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="card"><h2>💰 إجمالي المبيعات</h2><h1>{total_sales:,.2f} ج.م</h1></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="card"><h2>📈 صافي الأرباح (تقديري)</h2><h1>{total_profit:,.2f} ج.م</h1></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="card"><h2>📦 الأصناف المباعة</h2><h1>{len(df)}</h1></div>', unsafe_allow_html=True)

        st.divider()
        
        # الرسم البياني
        top_10 = df.groupby(name_col)['Sales'].sum().sort_values(ascending=False).head(10).reset_index()
        fig = px.bar(top_10, x='Sales', y=name_col, orientation='h', title="أعلى 10 أصناف مبيعاً", color='Sales', color_continuous_scale='Reds')
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📝 تفاصيل البيانات (بعد التنظيف)")
        st.dataframe(df[[name_col, 'Qty_Fixed', 'Price_Fixed', 'Sales']].rename(columns={name_col: 'الصنف', 'Qty_Fixed': 'الكمية', 'Price_Fixed': 'السعر'}))

    except Exception as e:
        st.error(f"خطأ: {e}")
else:
    st.info("ارفع الملف يا هندسة عشان نخلص!")

st.markdown("---")
st.markdown('<div style="text-align: center; color: gray;">تطوير المهندس محمد جمال | 01029796096</div>', unsafe_allow_html=True)
