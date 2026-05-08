import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="ZAGHLOULA DASHBOARD", layout="wide")

# ستايل احترافي مع خلفية مائية
st.markdown("""
<style>
    .main { background-color: #fcfcfc; }
    .main::before {
        content: "ZAGHLOULA";
        position: fixed; top: 50%; left: 50%;
        transform: translate(-50%, -50%) rotate(-30deg);
        font-size: 10vw; color: rgba(0,0,0,0.02);
        z-index: -1; font-weight: bold;
    }
    .metric-card {
        background: white; padding: 20px; border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05); text-align: center;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚀 لوحة تحكم زغلولة - معالجة البيانات المعقدة")

uploaded_file = st.sidebar.file_uploader("ارفع ملف الداتا الأولى", type=['csv', 'xlsx', 'xls'])

if uploaded_file:
    try:
        # محاولة قراءة الملف بكل التشفيرات الممكنة
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
        except:
            try:
                df = pd.read_csv(uploaded_file, encoding='cp1256')
            except:
                df = pd.read_excel(uploaded_file)

        # 1. تنظيف أسماء الأعمدة (حتى لو رموز)
        df.columns = [str(c).strip() for c in df.columns]

        # 2. دالة "القناص" لاستخراج الرقم الصافي من وسط الرموز (×، *، ج.م)
        def force_numeric(value):
            if pd.isna(value): return 0
            # مسح أي حاجة مش رقم أو نقطة عشرية
            clean = re.sub(r'[^\d.]', '', str(value))
            try:
                return float(clean)
            except:
                return 0

        # 3. تحديد الأعمدة بالترتيب (Index) عشان نهرب من مشكلة اللغة
        # في ملفك: العمود 3 هو الكمية، العمود 4 هو السعر، العمود 2 هو الصنف
        idx_name = 2
        idx_qty = 3
        idx_price = 4
        
        # إنشاء أعمدة جديدة نظيفة
        df['item_name'] = df.iloc[:, idx_name].astype(str)
        df['qty_clean'] = df.iloc[:, idx_qty].apply(force_numeric)
        df['price_clean'] = df.iloc[:, idx_price].apply(force_numeric)
        
        # 4. الحسابات
        df['total_sales'] = df['qty_clean'] * df['price_clean']
        # لو مفيش عمود تكلفة واضح، هنثبت نسبة ربح 20% لبيانات اليوم الأول
        df['net_profit'] = df['total_sales'] * 0.20

        # 5. فلترة الصفوف الوهمية (العناوين المتكررة في الملف)
        final_df = df[df['total_sales'] > 0].copy()
        final_df = final_df[~final_df['item_name'].str.contains('اجمالي|وارد|فاتورة|????', na=False)]

        # --- العرض ---
        t_s = final_df['total_sales'].sum()
        t_p = final_df['net_profit'].sum()

        st.success("✅ تم اختراق الملف وقراءة البيانات بنجاح!")
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="metric-card"><h4>إجمالي المبيعات</h4><h2 style="color:green">{t_s:,.2f}</h2></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card"><h4>صافي الربح (20%)</h4><h2 style="color:blue">{t_p:,.2f}</h2></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card"><h4>أصناف تم بيعها</h4><h2>{len(final_df)}</h2></div>', unsafe_allow_html=True)

        st.divider()

        # رسم بياني لأكثر الأصناف مبيعاً
        top_items = final_df.groupby('item_name')['total_sales'].sum().nlargest(10).reset_index()
        fig = px.bar(top_items, x='total_sales', y='item_name', orientation='h', title="أعلى 10 أصناف مبيعاً")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📋 معاينة البيانات بعد التنظيف")
        st.dataframe(final_df[['item_name', 'qty_clean', 'price_clean', 'total_sales']].rename(columns={
            'item_name': 'الصنف', 'qty_clean': 'الكمية', 'price_clean': 'السعر', 'total_sales': 'الإجمالي'
        }))

    except Exception as e:
        st.error(f"يا هندسة الملف ده فيه حاجة غلط في هيكله: {e}")
else:
    st.info("ارفع ملف Day 1 يا هندسة عشان نكسر النحس ده ونطلّع الداتا!")
