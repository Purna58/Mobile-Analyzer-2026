import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Page Configuration (2026 Premium Style)
st.set_page_config(page_title="Ultimate Mobile Analyzer 2026", layout="wide")

# 2. Advanced Data Loading & Full Column Mapping
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("dashboard_ready_data.csv")
    except FileNotFoundError:
        st.error("CSV ফাইলটি পাওয়া যায়নি! নিশ্চিত কর 'dashboard_ready_data.csv' ফাইলটি একই ফোল্ডারে আছে।")
        return pd.DataFrame()

    # Numeric Columns
    numeric_cols = [
        'Overall_Rating', 'Design_Rating', 'Display_Rating', 'Performance_Rating', 
        'Camera_Rating', 'Battery_Rating', 'Price_Clean', 'Main_Camera_MP', 
        'PDAF_MP', 'AF_MP', 'Ultrawide_MP', 'Macro_MP', 'Telephoto_MP', 
        'Min_RAM_GB', 'Min_Storage_GB', 'Weight_g', 'Size_Inches', 'Battery_mAh'
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'[^\d.]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0

    # Clean text columns
    text_cols = ['Phone_Name', 'Brand', 'Chipset', 'OS', 'GPU', 'Battery_Full', 'URL', 'NFC']
    for col in text_cols:
        if col not in df.columns:
            df[col] = 'Unknown'
        # ব্র্যান্ড যদি N/A বা empty থাকে তবে তাকে 'Missing' হিসেবে মার্ক করা
        df['Brand'] = df['Brand'].replace(['', 'N/A', 'n/a', 'nan', '0'], 'Missing Data')
    
    df = df.fillna('N/A')
    if 'Model' not in df.columns:
        df['Model'] = df['Phone_Name']
        
    return df

df = load_data()

# 3. Sidebar Navigation
st.sidebar.title("🚀 Navigation Menu")
page = st.sidebar.radio("Select Page:", ["Market Overview", "Specs Analytics", "Phone Finder & Suggestion"])

# Custom Color Palette
COLORS = px.colors.qualitative.Prism

# =========================================================
# ... (আগের কোডের ওপরের অংশ অপরিবর্তিত থাকবে)

# =========================================================
# PAGE 1: MARKET OVERVIEW
# =========================================================
if page == "Market Overview":
    st.title("📊 Market Overview")
    st.markdown("ব্র্যান্ডের দাপট এবং কোয়ালিটি এনালাইসিসের পূর্ণাঙ্গ চিত্র।")
    
    # --- Logic for Smart Top Brand (Picking the 2nd best if 1st is N/A) ---
    brand_counts = df['Brand'].value_counts()
    
    # এখানে লজিক: যদি সবচেয়ে বেশি 'Missing Data' থাকে, তবে ২য়টা নিবে। 
    # আর যদি ডাটা ক্লিন থাকে তবে ১মটাই নিবে।
    if len(brand_counts) > 1:
        if brand_counts.index[0] == 'Missing Data' or brand_counts.index[0] == 'N/A':
            volume_leader = brand_counts.index[1]
            volume_val = brand_counts.values[1]
        else:
            volume_leader = brand_counts.index[0]
            volume_val = brand_counts.values[0]
    else:
        volume_leader = brand_counts.index[0] if not brand_counts.empty else "No Data"
        volume_val = brand_counts.values[0] if not brand_counts.empty else 0

    # ২. Quality Leader (Missing Data বাদ দিয়ে সর্বোচ্চ রেটিং)
    clean_brand_df = df[~df['Brand'].isin(['Missing Data', 'N/A', 'Unknown'])]
    brand_ratings = clean_brand_df.groupby('Brand').agg({'Overall_Rating': 'mean', 'Phone_Name': 'count'})
    quality_brands = brand_ratings[brand_ratings['Phone_Name'] >= 3] # অন্তত ৩টি ফোন আছে এমন ব্র্যান্ড
    
    if not quality_brands.empty:
        top_quality_brand = quality_brands['Overall_Rating'].idxmax()
        top_rating_val = quality_brands['Overall_Rating'].max()
    else:
        top_quality_brand = volume_leader
        top_rating_val = clean_brand_df['Overall_Rating'].mean() if not clean_brand_df.empty else 0

    # KPI Cards
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Devices", len(df))
    avg_price = df[df['Price_Clean'] > 0]['Price_Clean'].mean()
    m2.metric("Avg Market Price", f"{int(avg_price):,} BDT")
    
    # এখানে ২য় পজিশনের লিডারকে দেখানো হচ্ছে
    m3.metric("Market Leader (Volume)", volume_leader, f"{volume_val} Models")
    m4.metric("Quality Leader (Rating)", top_quality_brand, f"{top_rating_val:.1f} ★")

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Market Share by Brand (%)")
        # পাই চার্ট থেকেও Missing Data সরিয়ে দিচ্ছি যাতে দেখতে সুন্দর লাগে
        fig_pie = px.pie(clean_brand_df, names='Brand', hole=0.4, color_discrete_sequence=COLORS)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with c2:
        st.subheader("Brand Quality Analysis (Avg Rating)")
        avg_rating_df = clean_brand_df.groupby('Brand')['Overall_Rating'].mean().reset_index().sort_values('Overall_Rating', ascending=True)
        fig_bar = px.bar(avg_rating_df, y='Brand', x='Overall_Rating', orientation='h', 
                         color='Overall_Rating', color_continuous_scale='RdYlGn')
        st.plotly_chart(fig_bar, use_container_width=True)

# ... (বাকি কোড আগের মতোই থাকবে)

# =========================================================
# PAGE 2: SPECS ANALYTICS
# =========================================================
elif page == "Specs Analytics":
    st.title("🔬 Detailed Specs Analytics")
    
    # Missing Data বাদ দিয়ে ডিফল্ট সিলেকশন
    available_brands = [b for b in df['Brand'].unique() if b != 'Missing Data']
    selected_brands = st.sidebar.multiselect("Select Brands to Compare:", df['Brand'].unique(), default=available_brands[:5])
    f_df = df[df['Brand'].isin(selected_brands)]

    # 1. 3D Hardware Analysis
    st.subheader("1. The 3D Hardware Cube (RAM vs Storage vs Price)")
    fig_3d = px.scatter_3d(f_df[f_df['Price_Clean'] > 0], x='Min_RAM_GB', y='Min_Storage_GB', z='Price_Clean',
                           color='Brand', size='Battery_mAh', hover_name='Phone_Name',
                           color_discrete_sequence=COLORS, opacity=0.8, height=700)
    st.plotly_chart(fig_3d, use_container_width=True)

    st.divider()

    # 2. Multi-Rating Comparison
    st.subheader("2. Detailed Rating Breakdown")
    rating_data = f_df.sort_values('Overall_Rating', ascending=False).head(15)
    fig_ratings = px.bar(rating_data, x='Phone_Name', 
                         y=['Design_Rating', 'Display_Rating', 'Camera_Rating', 'Battery_Rating'],
                         barmode='group', color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_ratings, use_container_width=True)

    c_col1, c_col2 = st.columns(2)
    with c_col1:
        st.subheader("3. Price Consistency (Box Plot)")
        fig_box = px.box(f_df[f_df['Price_Clean'] > 0], x="Brand", y="Price_Clean", color="Brand")
        st.plotly_chart(fig_box, use_container_width=True)
        
    with c_col2:
        st.subheader("4. Main Camera MP vs Price")
        fig_cam = px.scatter(f_df[f_df['Price_Clean'] > 0], x="Main_Camera_MP", y="Price_Clean", color="Brand",
                             size="Overall_Rating", hover_name="Phone_Name")
        st.plotly_chart(fig_cam, use_container_width=True)

# =========================================================
# PAGE 3: PHONE FINDER & SUGGESTION
# =========================================================
elif page == "Phone Finder & Suggestion":
    st.title("🤖 Smart Finder & Search Engine")
    
    display_df = df.copy()
    display_df['Price_Display'] = display_df['Price_Clean'].apply(lambda x: "Coming Soon" if x == 0 else f"{int(x):,} BDT")

    with st.form("suggestion_form"):
        sc1, sc2, sc3 = st.columns(3)
        budget = sc1.number_input("Maximum Budget (0 for Coming Soon):", value=50000, step=5000)
        min_ram = sc2.slider("Minimum RAM (GB):", 2, 24, 8)
        min_storage = sc3.slider("Minimum Storage (GB):", 32, 1024, 128)
        
        sc4, sc5 = st.columns(2)
        pref_brand = sc4.selectbox("Preferred Brand:", ["Any"] + [b for b in df['Brand'].unique() if b != 'Missing Data'])
        model_keyword = sc5.text_input("Specific keyword (e.g. 'Pro', 'Snapdragon'):")
        
        submit_btn = st.form_submit_button("Find Best Match")

    if submit_btn:
        if budget == 0:
            mask = (df['Price_Clean'] == 0) & (df['Min_RAM_GB'] >= min_ram)
        else:
            mask = (df['Price_Clean'] <= budget) & (df['Price_Clean'] > 0) & (df['Min_RAM_GB'] >= min_ram) & (df['Min_Storage_GB'] >= min_storage)
        
        if pref_brand != "Any": mask &= (df['Brand'] == pref_brand)
        if model_keyword: mask &= (df['Phone_Name'].str.contains(model_keyword, case=False) | df['Chipset'].str.contains(model_keyword, case=False))
        
        results = display_df[mask].sort_values(by=['Overall_Rating'], ascending=False).head(15)
        
        if not results.empty:
            st.success(f"Found {len(results)} matches for you!")
            st.dataframe(results[['Brand', 'Phone_Name', 'Price_Display', 'Min_RAM_GB', 'Min_Storage_GB', 'Battery_mAh', 'Overall_Rating', 'URL']], 
                         use_container_width=True)
        else:
            st.warning("No phones found. Try relaxing your filters.")

    st.divider()
    st.subheader("🔍 Full Advanced Search")
    search_q = st.text_input("Search anything (NFC, GPU, OS, etc.):")
    
    if search_q:
        search_mask = display_df.apply(lambda row: row.astype(str).str.contains(search_q, case=False, na=False).any(), axis=1)
        st.dataframe(display_df[search_mask], use_container_width=True)
    else:
        st.dataframe(display_df.head(50), use_container_width=True)