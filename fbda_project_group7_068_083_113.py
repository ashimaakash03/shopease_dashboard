writefile streamlit_app.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy import stats

# Load and Read the complete dataset
data_url= "https://docs.google.com/spreadsheets/d/1K6Rimz_lrrFRqLxup8UirZQYO-6mQryA3U-kpxFg3R4/edit?gid=1394848685#gid=1394848685"
data_url_enhanced= data_url.replace("edit?gid=1394848685#gid=1394848685", "export?format=csv")
df=pd.read_csv(data_url_enhanced)

# Create a sample of 3001 records from 10020 rows
gr7_068_083_113_df= df.sample(n=3001, random_state=6883113)

# Data Cleaning
gr7_068_083_113_df_clean = gr7_068_083_113_df.copy()

# --- 1. Helper Functions ---
def sensitize_gender(val):
    if pd.isna(val):
        return np.nan
    val_str = str(val).strip().lower()
    if val_str in ['m', 'male']:
        return 'Male'
    elif val_str in ['f', 'female']:
        return 'Female'
    else:
        return val_str.title()

def sensitize_discount(val):
    if pd.isna(val):
        return 0.0
    str_val = str(val).strip().replace('%', '')
    try:
        float_discount = float(str_val)
        return float_discount / 100 if float_discount > 1.0 else float_discount
    except ValueError:
        return 0.0

def sensitize_age(val):
    if pd.isna(val) or val not in range(18, 80):
        return np.nan
    return int(val)

def sensitize_text(val):
    if pd.isna(val) or str(val).strip().lower() in ['nan', 'none', '']:
        return np.nan
    return str(val).strip().title()

# --- 2. Date Standardization ---
gr7_068_083_113_df_clean['OrderDate'] = pd.to_datetime(
    gr7_068_083_113_df_clean['OrderDate'],
    errors='coerce',
    format='mixed'
)

gr7_068_083_113_df_clean['DeliveryDate'] = pd.to_datetime(
    gr7_068_083_113_df_clean['DeliveryDate'],
    errors='coerce',
    format='mixed'
)

# --- 3. Apply Categorical & Text Cleaning ---
gr7_068_083_113_df_clean['Gender'] = gr7_068_083_113_df_clean['Gender'].apply(sensitize_gender)
gr7_068_083_113_df_clean['Discount'] = gr7_068_083_113_df_clean['Discount'].apply(sensitize_discount)
gr7_068_083_113_df_clean['CustomerAge'] = gr7_068_083_113_df_clean['CustomerAge'].apply(sensitize_age)

gr7_068_083_113_df_clean['City'] = gr7_068_083_113_df_clean['City'].apply(sensitize_text)
gr7_068_083_113_df_clean['Category'] = gr7_068_083_113_df_clean['Category'].apply(sensitize_text)
gr7_068_083_113_df_clean['Product'] = gr7_068_083_113_df_clean['Product'].apply(sensitize_text)
gr7_068_083_113_df_clean['PaymentMethod'] = gr7_068_083_113_df_clean['PaymentMethod'].apply(sensitize_text)
gr7_068_083_113_df_clean['OrderStatus'] = gr7_068_083_113_df_clean['OrderStatus'].apply(sensitize_text).replace({'Canceled': 'Cancelled'})

# --- 4. Numeric Cleaning & Price Anomaly Fixes ---
gr7_068_083_113_df_clean['Quantity'] = gr7_068_083_113_df_clean['Quantity'].abs()
gr7_068_083_113_df_clean['UnitPrice'] = gr7_068_083_113_df_clean['UnitPrice'].abs()

gr7_068_083_113_df_clean['Rating'] = np.where(gr7_068_083_113_df_clean['Rating'].between(1, 5), gr7_068_083_113_df_clean['Rating'], np.nan)
gr7_068_083_113_df_clean['TotalAmount'] = (gr7_068_083_113_df_clean['Quantity'] * gr7_068_083_113_df_clean['UnitPrice'] * (1 - gr7_068_083_113_df_clean['Discount'])).abs()

# Filter out rows where UnitPrice or TotalAmount are negative (after abs() it means they were originally NaN or otherwise invalid)
gr7_068_083_113_df_clean = gr7_068_083_113_df_clean[
    (gr7_068_083_113_df_clean['UnitPrice'] >= 0) &
    (gr7_068_083_113_df_clean['TotalAmount'] >= 0)]

# Strating to build the dashboard
st.set_page_config(page_title="ShopEase Analytical Dashboard", layout="wide")

st.title("🛍️ Analytical Dashboard: ShopEase Orders")
st.markdown("---")

# --- SIDEBAR FILTERS ---
st.sidebar.header("🔍 Dynamic Filters")

valid_dates = gr7_068_083_113_df_clean['OrderDate'].dropna()
min_date = valid_dates.min().date()
max_date = valid_dates.max().date()

date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)
categories = st.sidebar.multiselect("Select Category", options=gr7_068_083_113_df_clean['Category'].dropna().unique(), default=gr7_068_083_113_df_clean['Category'].dropna().unique())
cities = st.sidebar.multiselect("Select City", options=gr7_068_083_113_df_clean['City'].dropna().unique(), default=gr7_068_083_113_df_clean['City'].dropna().unique())
statuses = st.sidebar.multiselect("Select Order Status", options=gr7_068_083_113_df_clean['OrderStatus'].dropna().unique(), default=gr7_068_083_113_df_clean['OrderStatus'].dropna().unique())
payment_methods = st.sidebar.multiselect("Select Payment Methods", options=gr7_068_083_113_df_clean['PaymentMethod'].dropna().unique(), default=gr7_068_083_113_df_clean['PaymentMethod'].dropna().unique())

# --- FILTER DATA ---
filtered_df = gr7_068_083_113_df_clean[
    (gr7_068_083_113_df_clean['Category'].isin(categories)) &
    (gr7_068_083_113_df_clean['City'].isin(cities)) &
    (gr7_068_083_113_df_clean['OrderStatus'].isin(statuses)) &
    (gr7_068_083_113_df_clean['PaymentMethod'].isin(payment_methods))
]

if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (filtered_df['OrderDate'].dt.date >= start_date) &
        (filtered_df['OrderDate'].dt.date <= end_date)
    ]

st.sidebar.write(f"Showing **{len(filtered_df)}** of **{len(gr7_068_083_113_df_clean)}** records")

# --- KPI METRICS ---
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Sales Revenue", f"${filtered_df['TotalAmount'].sum():,.2f}")
kpi2.metric("Total Orders", f"{len(filtered_df):,}")
kpi3.metric("Avg Order Value", f"${filtered_df['TotalAmount'].mean():,.2f}")
kpi4.metric("Avg Customer Rating", f"{filtered_df['Rating'].mean():.2f} ⭐")

st.markdown("---")

# --- SECTION 1: NON-CATEGORICAL DESCRIPTIVE STATS ---
st.header("📊 1. Non-Categorical Data: Descriptive Statistics")
num_cols = ['CustomerAge', 'Quantity', 'UnitPrice', 'Discount', 'Rating', 'TotalAmount']

stats_dict = {}
for col in num_cols:
    series = filtered_df[col].dropna()
    if len(series) > 0:
        stats_dict[col] = {
            "Count": len(series),
            "Mean": series.mean(),
            "Median": series.median(),
            "Mode": series.mode().iloc[0] if not series.mode().empty else np.nan,
            "Std Dev": series.std(),
            "Min": series.min(),
            "Max": series.max(),
            "Range": series.max() - series.min(),
            "Skewness": series.skew(),
            "Kurtosis": series.kurtosis(),
            "25th Pct": series.quantile(0.25),
            "75th Pct": series.quantile(0.75),
        }

stats_df = pd.DataFrame(stats_dict).T
st.dataframe(stats_df.style.format("{:.2f}"))

st.markdown("---")

# --- SECTION 2: CATEGORICAL DATA STATS ---
st.header("🏷️ 2. Categorical Data Statistics")
cat_col_choice = st.selectbox("Select Categorical Feature to Analyze:", ['Category', 'City', 'Gender', 'PaymentMethod', 'OrderStatus'])

cat_series = filtered_df[cat_col_choice].dropna()
cat_counts = cat_series.value_counts().reset_index()
cat_counts.columns = [cat_col_choice, 'Frequency']
cat_counts['Relative Frequency (%)'] = (cat_counts['Frequency'] / len(cat_series) * 100).round(2)

col_table, col_chart = st.columns([1, 1])
with col_table:
    st.subheader(f"Frequency Breakdown: {cat_col_choice}")
    st.dataframe(cat_counts)
    if len(cat_counts) > 0:
        highest_cat = cat_counts.iloc[0]
        lowest_cat = cat_counts.iloc[-1]
        st.info(f"**Highest:** {highest_cat[cat_col_choice]} ({highest_cat['Frequency']} orders, {highest_cat['Relative Frequency (%)']}%)")
        st.warning(f"**Lowest:** {lowest_cat[cat_col_choice]} ({lowest_cat['Frequency']} orders, {lowest_cat['Relative Frequency (%)']}%)")

with col_chart:
    st.subheader("Distribution Chart")
    fig_bar = px.bar(cat_counts, x=cat_col_choice, y='Frequency', text='Relative Frequency (%)', color=cat_col_choice, title=f"Order Distribution by {cat_col_choice}")
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# --- SECTION 3: VISUALIZATIONS ---
st.header("📈 3. Interactive Visual Explorations")
tab1, tab2, tab3, tab4 = st.tabs(["Distributions", "Category Comparisons", "Correlation Heatmap", "Scatter Analysis"])

with tab1:
  dist_var = st.selectbox(
      "Select Numerical Feature:",
      ["TotalAmount", "CustomerAge", "UnitPrice", "Discount", "Rating"],
  )

  fig_hist = px.histogram(
      filtered_df,
      x=dist_var,
      nbins=30,
      marginal="box",
      title=f"Distribution of {dist_var}",
  )

  # Prevent negative axis ranges
  fig_hist.update_xaxes(rangemode="nonnegative")

  # Apply xbins ONLY to the histogram trace (ignoring the box marginal trace)
  fig_hist.update_traces(
      selector=dict(type="histogram"), xbins=dict(start=0)
  )

  st.plotly_chart(fig_hist, use_container_width=True)

with tab2:
    fig_box = px.box(filtered_df, x='Category', y='TotalAmount', color='Category', points="outliers", title="Total Amount Distribution across Categories")
    st.plotly_chart(fig_box, use_container_width=True)

with tab3:
    st.subheader("Measures of Correlation Matrix")
    corr_vars = filtered_df[['CustomerAge', 'Quantity', 'UnitPrice', 'Discount', 'Rating', 'TotalAmount']].dropna()
    corr_type = st.radio("Correlation Metric:", ["Pearson", "Spearman"], horizontal=True)
    corr_matrix = corr_vars.corr(method=corr_type.lower())
    fig_corr = px.imshow(corr_matrix, text_auto=".2f", aspect="auto", color_continuous_scale="Blues", title=f"{corr_type} Correlation Matrix")
    st.plotly_chart(fig_corr, use_container_width=True)

with tab4:
    fig_scatter = px.scatter(filtered_df, x='UnitPrice', y='TotalAmount', color='Category', size='Quantity', hover_data=['Product', 'City'], title="UnitPrice vs. TotalAmount")
    st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")

# --- SECTION 4: INFERENTIAL STATISTICS & HYPOTHESIS TESTING ---
st.header("🔬 4. Inferential Statistics & Hypothesis Testing")

inf_tab1, inf_tab2, inf_tab3 = st.tabs(["Normality Testing", "Mean / Median Comparison", "Chi-Square Independence Test"])

with inf_tab1:
    st.subheader("Test of Normality (Shapiro-Wilk)")
    norm_var = st.selectbox("Select Metric for Normality Testing:", ['TotalAmount', 'UnitPrice', 'CustomerAge', 'Rating'])
    norm_series = filtered_df[norm_var].dropna()

    if len(norm_series) > 3:
        # Shapiro-Wilk (capped at 500 samples per SciPy recommendation)
        shapiro_stat, shapiro_p = stats.shapiro(norm_series[:500])

        norm_results = pd.DataFrame({
            "Statistical Test": ["Shapiro-Wilk (N=500)"],
            "Test Statistic": [shapiro_stat],
            "p-value": [shapiro_p],
            "Conclusion (α = 0.05)": [
                "Reject H0 (Non-Normal)" if shapiro_p < 0.05 else "Fail to Reject H0 (Normal)"
            ]
        })
        st.dataframe(norm_results.style.format({"Test Statistic": "{:.4f}", "p-value": "{:.4e}"}))

        st.markdown("**Null Hypothesis (H0):** The data is drawn from a normal distribution.")
        st.markdown("**Alternate Hypothesis (H1):** The data is NOT drawn from a normal distribution.")
        st.markdown(f"**Obtained p-value:** {shapiro_p:.4e}")
        st.markdown("If the p-value is less than the significance level (e.g., 0.05), we reject the null hypothesis and conclude that the data is not normally distributed.")

with inf_tab2:
    st.subheader("Comparison of Sales Revenue across Product Categories")
    col_param = st.columns(1)

    # Prepare category arrays
    cat_groups = [group['TotalAmount'].dropna().values for name, group in filtered_df.groupby('Category') if len(group) > 0]

    if len(cat_groups) > 1:
        # Parametric One-Way ANOVA
        f_stat, f_p = stats.f_oneway(*cat_groups)

        with col_param[0]:
            st.write("### 1. One-Way ANOVA (Parametric)")
            st.metric("F-Statistic", f"{f_stat:.4f}")
            st.metric("p-value", f"{f_p:.4e}")
            if f_p < 0.05:
                st.success("Significant difference in mean TotalAmount across categories.")
            else:
                st.info("No significant difference in mean TotalAmount across categories.")

            st.markdown("**Null Hypothesis (H0):** The mean total amount is the same across all product categories.")
            st.markdown("**Alternate Hypothesis (H1):** The mean total amount is different for at least one product category.")
            st.markdown(f"**Obtained p-value:** {f_p:.4e}")
            st.markdown("If the p-value is less than the significance level (e.g., 0.05), we reject the null hypothesis and conclude that there is a significant difference in mean total amount across categories.")

with inf_tab3:
    st.subheader("Chi-Square Test of Independence")
    st.write("Testing association between Payment Method and Order Status.")

    contingency = pd.crosstab(filtered_df['PaymentMethod'], filtered_df['OrderStatus'])
    st.write("#### Contingency Table:")
    st.dataframe(contingency)

    if contingency.size > 0:
        chi2, chi2_p, dof, _ = stats.chi2_contingency(contingency)
        c1, c2, c3 = st.columns(3)
        c1.metric("Chi-Square Statistic", f"{chi2:.4f}")
        c2.metric("Degrees of Freedom", f"{dof}")
        c3.metric("p-value", f"{chi2_p:.4f}")

        if chi2_p < 0.05:
            st.success("Reject H0: Payment Method and Order Status are dependent.")
        else:
            st.info("Fail to Reject H0: Payment Method and Order Status are independent.")

st.markdown("---")
