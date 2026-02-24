import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Page Configuration
st.set_page_config(page_title="Ultimate Mobile Analyzer 2026", layout="wide")

# 2. Advanced Data Loading
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("dashboard_ready_data.csv")
    except FileNotFoundError:
        st.error("Dataset not found. Please ensure 'dashboard_ready_data.csv' is in the directory.")
        return pd.DataFrame()

    # Numeric conversion logic
    numeric_cols = [
        'Overall_Rating', 'Design_Rating', 'Display_Rating', 'Performance_Rating', 
        'Camera_Rating', 'Battery_Rating', 'Price_Clean', 'Main_Camera_MP', 
        'Min_RAM_GB', 'Min_Storage_GB', 'Battery_mAh'
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'[^\d.]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Text cleaning logic
    text_cols = ['Phone_Name', 'Brand', 'Chipset', 'OS', 'URL']
    for col in text_cols:
        if col not in df.columns:
            df[col] = 'Unknown'
        df['Brand'] = df['Brand'].replace(['', 'N/A', 'n/a', 'nan', '0', None], 'Missing Data')
    
    return df

df = load_data()

# 3. Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Market Overview", "Specs Analytics", "Phone Finder"])

COLORS = px.colors.qualitative.Prism

# PAGE 1: MARKET OVERVIEW
if page == "Market Overview":
    st.title("Market Overview")
    st.markdown("A comprehensive analysis of brand dominance and quality.")
    
    brand_counts = df['Brand'].value_counts()
    if len(brand_counts) > 1 and brand_counts.index[0] == 'Missing Data':
        v_leader, v_val = brand_counts.index[1], brand_counts.values[1]
    else:
        v_leader = brand_counts.index[0] if not brand_counts.empty else "N/A"
        v_val = brand_counts.values[0] if not brand_counts.empty else 0

    clean_df = df[~df['Brand'].isin(['Missing Data', 'N/A', 'Unknown'])]
    brand_stats = clean_df.groupby('Brand').agg({'Overall_Rating': 'mean', 'Phone_Name': 'count'})
    top_brands = brand_stats[brand_stats['Phone_Name'] >= 3]
    
    q_leader = top_brands['Overall_Rating'].idxmax() if not top_brands.empty else v_leader
    q_val = top_brands['Overall_Rating'].max() if not top_brands.empty else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Devices", len(df))
    m2.metric("Avg Price", f"{int(df[df['Price_Clean']>0]['Price_Clean'].mean()):,} BDT")
    m3.metric("Volume Leader", v_leader, f"{v_val} Models")
    m4.metric("Quality Leader", q_leader, f"{q_val:.1f} ★")

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Market Share (%)")
        st.plotly_chart(px.pie(clean_df, names='Brand', hole=0.4, color_discrete_sequence=COLORS), use_container_width=True)
    with c2:
        st.subheader("Average Brand Ratings")
        ratings = clean_df.groupby('Brand')['Overall_Rating'].mean().reset_index().sort_values('Overall_Rating')
        st.plotly_chart(px.bar(ratings, y='Brand', x='Overall_Rating', orientation='h', color='Overall_Rating', color_continuous_scale='RdYlGn'), use_container_width=True)

# PAGE 2: SPECS ANALYTICS
elif page == "Specs Analytics":
    st.title("Specs Analytics")
    
    valid_brands = [b for b in df['Brand'].unique() if b != 'Missing Data']
    selected = st.sidebar.multiselect("Compare Brands:", df['Brand'].unique(), default=valid_brands[:5])
    f_df = df[df['Brand'].isin(selected)]

    if not f_df.empty:
        st.subheader("3D Hardware Cube (RAM vs Storage vs Price)")
        st.plotly_chart(px.scatter_3d(f_df[f_df['Price_Clean']>0], x='Min_RAM_GB', y='Min_Storage_GB', z='Price_Clean', 
                                     color='Brand', size='Battery_mAh', hover_name='Phone_Name', height=700), use_container_width=True)

        st.divider()

        st.subheader("Detailed Comparison")
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.box(f_df[f_df['Price_Clean']>0], x="Brand", y="Price_Clean", color="Brand", title="Price Distribution"), use_container_width=True)
        with c2:
            st.plotly_chart(px.scatter(f_df, x="Main_Camera_MP", y="Price_Clean", color="Brand", hover_name="Phone_Name", title="Camera Performance vs Price"), use_container_width=True)
    else:
        st.warning("Please select at least one brand from the sidebar.")

# PAGE 3: PHONE FINDER & SECURE SEARCH
elif page == "Phone Finder":
    st.title("Smart Finder")
    
    display_df = df.copy()
    display_df['Price_Display'] = display_df['Price_Clean'].apply(
        lambda x: "Coming Soon" if x == 0 else f"{int(x):,} BDT"
    )

    with st.form("finder_form"):
        sc1, sc2, sc3 = st.columns(3)
        budget = sc1.number_input("Max Budget (0 for Coming Soon):", value=50000)
        ram = sc2.slider("Min RAM (GB):", 2, 24, 8)
        storage = sc3.slider("Min Storage (GB):", 32, 1024, 128)
        
        sc4, sc5 = st.columns(2)
        brand = sc4.selectbox("Preferred Brand:", ["Any"] + [b for b in df['Brand'].unique() if b != 'Missing Data'])
        keyword = sc5.text_input("Model Keyword (e.g. Pro, Ultra, Snapdragon):")
        submit = st.form_submit_button("Find Matches")

    if submit:
        mask = (df['Min_RAM_GB'] >= ram) & (df['Min_Storage_GB'] >= storage)
        if budget == 0:
            mask &= (df['Price_Clean'] == 0)
        else:
            mask &= (df['Price_Clean'] <= budget) & (df['Price_Clean'] > 0)
        
        if brand != "Any": mask &= (df['Brand'] == brand)
        if keyword: mask &= (df['Phone_Name'].str.contains(keyword, case=False) | df['Chipset'].str.contains(keyword, case=False))
        
        res = display_df[mask].sort_values(by='Overall_Rating', ascending=False).head(15)
        if not res.empty:
            st.success(f"Found {len(res)} matching models")
            st.dataframe(res[['Brand', 'Phone_Name', 'Price_Display', 'Min_RAM_GB', 'Min_Storage_GB', 'Overall_Rating', 'URL']], use_container_width=True)
        else:
            st.warning("No matches found for the selected criteria.")

    st.divider()
    st.subheader("Secure Database Search")
    query = st.text_input("Enter phone name or any feature (e.g. 5G, OLED, 108MP):")
    
    if query:
        search_mask = display_df.apply(lambda row: row.astype(str).str.contains(query, case=False).any(), axis=1)
        search_results = display_df[search_mask].head(10)
        
        if not search_results.empty:
            st.write(f"Showing top {len(search_results)} matching results:")
            st.dataframe(search_results, use_container_width=True, hide_index=True)
        else:
            st.warning("No specific matches found for your search.")
    else:
        st.info("The database is secured. Please enter a keyword in the search box above to view details.")
