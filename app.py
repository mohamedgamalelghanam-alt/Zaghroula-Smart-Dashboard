import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ---------------------------------------------------
# إعداد الصفحة
# ---------------------------------------------------
st.set_page_config(
    page_title="📊 Zaghloula Smart Dashboard",
    layout="wide"
)

# ---------------------------------------------------
# دالة معالجة الملف (المعدلة لملف السبت)
# ---------------------------------------------------
@st.cache_data
def load_data(file):
    try:
        # الملف ده طلع إكسيل حقيقي
        df = pd.read_excel(file)
    except:
        df = pd.read_csv(file, encoding='cp1256')

    # تنظيف الصفوف الفارغة أو اللي فيها كلمة "بيع" كعنوان
    df = df.dropna(subset=['صنف'])
    df = df[df['صنف'] != 'بيع']

    # تحويل الأعمدة لأرقام
    cols_to_fix = ['كمية', 'سعر', 'قيمة', 'سعر التكلفة', 'الرصيد الحالي']
    for col in cols_to_fix:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # --- الحسبة المعتمدة ---
    # إجمالي المبيعات = القيمة الجاهزة في الملف
    df['Total_Sales'] = df['قيمة']
    
    # صافي الربح = القيمة - (الكمية * سعر التكلفة)
    # ملحوظة: سعر التكلفة هنا هو سعر شراء "القطعة/الكيلو" الواحد
    df['Net_Profit'] = df['Total_Sales'] - (df['كمية'] * df['سعر التكلفة'])
    
    # نسبة الربح
    df['Margin'] = (df['Net_Profit'] / (df['كمية'] * df['سعر التكلفة']).replace(0, 1)) * 100

    return df

# ---------------------------------------------------
# الواجهة
# ---------------------------------------------------
st.title("📊 Zaghloula Smart Dashboard")

uploaded_file = st.file_uploader("ارفع ملف (مبيعات السبت)", type=["xlsx", "xls", "csv"])

if uploaded_file:
    df = load_data(uploaded_file)
    
    # حسابات إجمالية
    total_sales = df['Total_Sales'].sum()
    total_profit = df['Net_Profit'].sum()
    low_stock_count = len(df[df['الرصيد الحالي'] <= 5])

    # العرض
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("💰 إجمالي المبيعات", f"{total_sales:,.2f} ج.م")
    with c2:
        st.metric("📈 صافي الأرباح", f"{total_profit:,.2f} ج.م")
    with c3:
        st.metric("⚠️ نواقص المخزن", f"{low_stock_count}")

    # تابات التفاصيل
    t1, t2, t3 = st.tabs(["📊 تحليل الأصناف", "📦 حالة المخزن", "📘 الدليل"])

    with t1:
        st.subheader("أعلى 10 أصناف ربحية")
        top_10 = df.groupby('صنف')['Net_Profit'].sum().sort_values(ascending=False).head(10).reset_index()
        st.plotly_chart(px.bar(top_10, x='Net_Profit', y='صنف', orientation='h'))

    with t2:
        st.subheader("الأصناف التي قاربت على النفاد")
        st.dataframe(df[df['الرصيد الحالي'] <= 5][['صنف', 'الرصيد الحالي']], use_container_width=True)

    with t3:
        st.markdown(f"""
        ### **توثيق النظام - المهندس محمد جمال**
        *   **مصدر البيانات:** ملف `{uploaded_file.name}`.
        *   **آلية الحساب:** يتم خصم التكلفة (كمية × سعر تكلفة) من إجمالي قيمة البيع.
        *   **التحديث:** الكود مهيأ لقراءة أعمدة 'صنف'، 'قيمة'، و'سعر التكلفة' مباشرة.
        """)

    st.markdown("---")
    st.markdown("<div style='text-align: center; color: gray;'>تطوير المهندس محمد جمال | 01029796096</div>", unsafe_allow_html=True)
