import streamlit as st
import pandas as pd

st.set_page_config(page_title="📊 Zaghloula Dashboard", layout="wide")

st.title("📊 Zaghloula Smart Dashboard")

file = st.file_uploader("ارفع ملف المبيعات", type=["xlsx", "xls", "csv"])

if file:
    try:
        # 1. قراءة الملف
        try:
            df = pd.read_excel(file)
        except:
            df = pd.read_csv(file, encoding='cp1256')

        # 2. تنظيف أسماء الأعمدة (شيل المسافات)
        df.columns = [str(c).strip() for c in df.columns]

        # 3. تحديد الأعمدة بذكاء (عشان لو الاسم اتغير)
        # بندور على أي عمود فيه كلمة 'قيمة' أو 'صافي' للبيع
        val_col = next((c for c in df.columns if 'قيمة' in c or 'صافي' in c), None)
        # بندور على أي عمود فيه كلمة 'ربح'
        profit_col = next((c for c in df.columns if 'ربح' in c), None)
        # بندور على صنف
        name_col = next((c for c in df.columns if 'صنف' in c), None)

        if val_col and profit_col:
            # 4. تحويل الداتا لأرقام (إجباري) وشيل أي نصوص
            df[val_col] = pd.to_numeric(df[val_col], errors='coerce').fillna(0)
            df[profit_col] = pd.to_numeric(df[profit_col], errors='coerce').fillna(0)

            # 5. تنظيف الصفوف (شيل صف "بيع" أو "إجمالي")
            df = df.dropna(subset=[name_col])
            df = df[~df[name_col].astype(str).str.contains('بيع|إجمالي|اجمالى', na=False)]

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
