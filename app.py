import streamlit as st
import pandas as pd
import plotly.express as px

# 1. إعداد الصفحة والعناوين الفخمة
st.set_page_config(page_title="📊 Zaghloula Smart Dashboard", layout="wide")

# 2. دالة معالجة البيانات (المحرك الرئيسي)
@st.cache_data
def load_data(file):
    try:
        # قراءة الملف سواء كان Excel أو CSV
        df = pd.read_excel(file)
    except:
        df = pd.read_csv(file, encoding='cp1256')

    # تنظيف البيانات من الصفوف غير المحاسبية
    if 'صنف' in df.columns:
        df = df.dropna(subset=['صنف'])
        # استبعاد الصفوف اللي فيها كلمة "بيع" أو "اجمالى"
        df = df[~df['صنف'].astype(str).str.contains('بيع|اجمالى|إجمالي', na=False)]
    
    # تحويل الأعمدة الرقمية لضمان عدم حدوث إيرور في الحسابات
    numeric_cols = ['كمية', 'سعر', 'قيمة', 'سعر التكلفة', 'الرصيد الحالي']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # الحسبة المعتمدة لصافي الربح
    if 'قيمة' in df.columns and 'سعر التكلفة' in df.columns:
        df['Total_Sales'] = df['قيمة']
        df['Net_Profit'] = df['Total_Sales'] - (df['كمية'] * df['سعر التكلفة'])
    else:
        df['Total_Sales'] = 0
        df['Net_Profit'] = 0

    # تحديد الفرع تلقائياً
    branch = "الفرع الرئيسي"
    if 'الفرع' in df.columns: branch = df['الفرع'].dropna().iloc[0]

    return df, branch

# 3. واجهة المستخدم
st.title("📊 Zaghloula Smart Dashboard")

with st.sidebar:
    st.header("🛒 نظام زغلولة")
    uploaded_file = st.file_uploader("ارفع ملف المبيعات (مبيعات السبت)", type=["xlsx", "xls", "csv"])

if uploaded_file:
    # استدعاء الدالة (الحل النهائي للإيرور)
    data, branch = load_data(uploaded_file)
    
    # الأرقام الكلية
    t_sales = data['Total_Sales'].sum()
    t_profit = data['Net_Profit'].sum()
    
    st.success(f"✅ تم تحليل البيانات بنجاح لـ {branch}")
    
    # كروت العرض
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"### 💰 إجمالي المبيعات\n## {t_sales:,.2f} ج.م")
    with col2:
        st.markdown(f"### 📈 صافي الأرباح\n## {t_profit:,.2f} ج.م")
    with col3:
        if 'الرصيد الحالي' in data.columns:
            low_stock = data[data['الرصيد الحالي'] <= 5]
            st.markdown(f"### ⚠️ نواقص المخزن\n## {len(low_stock)}")

    # عرض البيانات والرسوم
    tab1, tab2 = st.tabs(["📊 التحليل المالي", "📘 دليل الاستخدام الرسمي"])
    
    with tab1:
        if not data.empty:
            # أعلى الأصناف ربحية
            top_profit = data.groupby('صنف')['Net_Profit'].sum().sort_values(ascending=False).head(10).reset_index()
            fig = px.bar(top_profit, x='Net_Profit', y='صنف', orientation='h', 
                         title="مؤشر أعلى 10 أصناف ربحية", color='Net_Profit', color_continuous_scale='Greens')
            st.plotly_chart(fig, use_container_width=True)
            
            # جدول لمراجعة الأصناف الخاسرة أو ضعيفة الربح
            st.subheader("⚠️ أصناف تحتاج مراجعة (ربح منخفض أو خسارة)")
            low_margin = data[data['Net_Profit'] <= (data['Total_Sales'] * 0.05)]
            st.dataframe(low_margin[['صنف', 'كمية', 'Total_Sales', 'Net_Profit']], use_container_width=True)

    with tab2:
        st.header("📘 الدليل التشغيلي للنظام")
        st.markdown(f"""
        **تم تطوير هذا النظام بواسطة المهندس محمد جمال لفرع زغلولة.**
        
        * **المعادلة الحسابية:** صافي الربح = [إجمالي القيمة] - ([الكمية المباعة] × [سعر التكلفة]).
        * **التوافق:** الكود متوافق مع ملفات السيستم بصيغة Excel و CSV.
        * **الدقة:** يتم استبعاد أي صفوف غير محاسبية تلقائياً لضمان دقة إجمالي الأرباح ({t_profit:,.2f} ج.م).
        """)

    # التوقيع الرسمي (البسيط والشيك)
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: gray; font-size: 14px;'>تطوير المهندس محمد جمال | 01029796096</div>", unsafe_allow_html=True)
else:
    st.info("في انتظار رفع ملف المبيعات لبدء التحليل...")
