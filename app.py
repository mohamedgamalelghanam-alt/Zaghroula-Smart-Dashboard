import streamlit as st
import pandas as pd
import plotly.express as px

# 1. إعداد الصفحة بشكل احترافي
st.set_config_page(page_title="📊 Zaghloula Smart Dashboard", layout="wide")

# 2. دالة معالجة البيانات وتحليلها
@st.cache_data
def analyze_data(file):
    try:
        df = pd.read_excel(file)
    except:
        df = pd.read_csv(file, encoding='cp1256')

    # تنظيف البيانات
    df.columns = [str(c).strip() for c in df.columns]
    if 'صنف' in df.columns:
        df = df.dropna(subset=['صنف'])
        df = df[~df['صنف'].astype(str).str.contains('بيع|إجمالي|اجمالى', na=False)]

    # تحويل الأرقام
    cols = ['كمية', 'قيمة', 'سعر التكلفة', 'الرصيد الحالي', 'إجمالي ربح']
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    # الحسابات الذكية
    # إذا كان عمود 'إجمالي ربح' موجود نعتمد عليه، وإلا نحسبه يدوياً
    if 'إجمالي ربح' in df.columns and df['إجمالي ربح'].sum() != 0:
        df['Net_Profit'] = df['إجمالي ربح']
    else:
        df['Net_Profit'] = df['قيمة'] - (df['كمية'] * df['سعر التكلفة'])
    
    df['Total_Sales'] = df['قيمة']
    
    return df

# 3. الواجهة الرئيسية
st.title("📊 Zaghloula Smart Dashboard")
st.markdown("---")

uploaded_file = st.sidebar.file_uploader("ارفع ملف مبيعات السبت أو أي يوم آخر", type=["xlsx", "xls", "csv"])

if uploaded_file:
    df = analyze_data(uploaded_file)
    
    # --- قسم الأرقام الرئيسية (Key Metrics) ---
    t_sales = df['Total_Sales'].sum()
    t_profit = df['Net_Profit'].sum()
    margin = (t_profit / t_sales * 100) if t_sales > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💰 إجمالي دخل الدرج", f"{t_sales:,.2f} ج.م")
    with col2:
        st.metric("📈 صافي الربح الحقيقي", f"{t_profit:,.2f} ج.م")
    with col3:
        st.metric("🎯 متوسط هامش الربح", f"{margin:.1f}%")

    st.markdown("---")

    # --- قسم التحليل الذكي (Insights) ---
    tab1, tab2, tab3 = st.tabs(["🚀 الأعلى ربحية", "📦 رادار النواقص", "📋 تقرير اليوم"])

    with tab1:
        st.subheader("الأصناف 'الجوكر' (أعلى 10 أصناف مكسباً)")
        top_10 = df.groupby('صنف')['Net_Profit'].sum().sort_values(ascending=False).head(10).reset_index()
        fig = px.bar(top_10, x='Net_Profit', y='صنف', orientation='h', 
                     color='Net_Profit', color_continuous_scale='Greens',
                     labels={'Net_Profit': 'صافي الربح', 'صنف': 'اسم الصنف'})
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("⚠️ أصناف محتاجة توريد (الرصيد أقل من 1 كيلو/قطعة)")
        if 'الرصيد الحالي' in df.columns:
            low_stock = df[df['الرصيد الحالي'] < 1][['صنف', 'الرصيد الحالي']].sort_values(by='الرصيد الحالي')
            st.table(low_stock)
        else:
            st.info("عمود الرصيد غير متوفر في هذا الملف.")

    with tab3:
        st.subheader("📝 ملخص أداء اليوم")
        st.write(f"اليوم تم تسجيل **{len(df)}** عملية بيع.")
        
        # تحليل فئات المنتجات (لو الاسم فيه بن، عطارة، إلخ)
        df['Category'] = df['صنف'].apply(lambda x: 'بن' if 'بن' in str(x) else ('عطارة' if 'عطاره' in str(x) else 'أخرى'))
        cat_analysis = df.groupby('Category')['Net_Profit'].sum().reset_index()
        
        st.write("توزيع الأرباح حسب الفئة:")
        st.plotly_chart(px.pie(cat_analysis, values='Net_Profit', names='Category', hole=0.4))

    # التوقيع
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: gray;'>تطوير المهندس محمد جمال | 01029796096</div>", unsafe_allow_html=True)

else:
    st.info("يا هندسة ارفع ملف السبت عشان أوريك التحليل اللي عملناه دلوقتى ظهر إزاي!")

            # 6. الحسابات النهائية
            total_sales = df[val_col].sum()
            total_profit = df[profit_col].sum()

            # العرض
            c1, c2 = st.columns(2)
            c1.metric("💰 إجمالي المبيعات", f"{total_sales:,.2f} ج.م")
            c2.metric("📈 صافي الأرباح", f"{total_profit:,.2f} ج.م")

            st.write("### مراجعة البيانات المرفوعة:")
            st.dataframe(df[[name_col, val_col, profit_col]].head(10))
            
        else:
            st.error(f"السيستم مش لاقي الأعمدة المطلوبة. الأعمدة اللي موجودة هي: {list(df.columns)}")

    except Exception as e:
        st.error(f"حصلت مشكلة وأنا بقرأ الملف: {e}")

st.markdown("---")
st.markdown("<center>تطوير المهندس محمد جمال | 01029796096</center>", unsafe_allow_html=True)
        st.dataframe(df.head())
    else:
        st.error("السيستم مش لاقي أعمدة (قيمة) أو (سعر التكلفة). تأكد من الملف!")
    # تنقية البيانات
    if col_name:
        df = df.dropna(subset=[col_name])
        df = df[~df[col_name].astype(str).str.contains('بيع|اجمالى|إجمالي', na=False)]

    # تحويل الأرقام
    for c in [col_qty, col_val, col_cost]:
        if c:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    # الحسابات (بناءً على الأعمدة اللي لقاها)
    if col_val and col_cost and col_qty:
        df['Total_Sales'] = df[col_val]
        # لو سعر التكلفة هو سعر الكيلو الواحد:
        df['Net_Profit'] = df['Total_Sales'] - (df[col_qty] * df[col_cost])
    else:
        df['Total_Sales'] = 0
        df['Net_Profit'] = 0

    return df, col_name

# الواجهة
st.title("📊 Zaghloula Smart Dashboard")

uploaded_file = st.sidebar.file_uploader("ارفع ملف المبيعات", type=["xlsx", "xls", "csv"])

if uploaded_file:
    data, col_name = load_data(uploaded_file)
    
    t_sales = data['Total_Sales'].sum()
    t_profit = data['Net_Profit'].sum()

    if t_sales == 0:
        st.warning("⚠️ الداتا اتقرت بس الحسابات طالعة صفر. اتأكد إن الأعمدة في الملف اسمها (صنف، كمية، قيمة، سعر التكلفة)")
    
    col1, col2 = st.columns(2)
    col1.metric("💰 إجمالي المبيعات", f"{t_sales:,.2f} ج.م")
    col2.metric("📈 صافي الأرباح", f"{t_profit:,.2f} ج.م")

    if not data.empty and col_name:
        top_10 = data.groupby(col_name)['Net_Profit'].sum().sort_values(ascending=False).head(10).reset_index()
        st.plotly_chart(px.bar(top_10, x='Net_Profit', y=col_name, orientation='h', title="أعلى الأصناف ربحية"))
    
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: gray;'>تطوير المهندس محمد جمال | 01029796096</div>", unsafe_allow_html=True)
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
