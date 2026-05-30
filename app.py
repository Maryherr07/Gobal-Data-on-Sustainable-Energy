import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Global Sustainable Energy Dashboard",
    page_icon="🌍",
    layout="wide"
)

# -----------------------------
# 1. Load and clean data
# -----------------------------
@st.cache_data
def load_data():
    possible_paths = [
        Path(__file__).parent / "global-data-on-sustainable-energy.csv",
        Path("global-data-on-sustainable-energy.csv"),
        Path("/mnt/data/global-data-on-sustainable-energy.csv")
    ]

    for path in possible_paths:
        if path.exists():
            df = pd.read_csv(path)
            break
    else:
        st.error("CSV file not found. Place global-data-on-sustainable-energy.csv in the same folder as app.py.")
        st.stop()

    # Rename columns to shorter readable names
    rename_map = {
        "Entity": "Country",
        "Year": "Year",
        "Access to electricity (% of population)": "Electricity access (%)",
        "Access to clean fuels for cooking": "Clean fuels access (%)",
        "Renewable-electricity-generating-capacity-per-capita": "Renewable capacity per capita",
        "Financial flows to developing countries (US $)": "Financial flows (US$)",
        "Renewable energy share in the total final energy consumption (%)": "Renewable energy share (%)",
        "Electricity from fossil fuels (TWh)": "Fossil electricity (TWh)",
        "Electricity from nuclear (TWh)": "Nuclear electricity (TWh)",
        "Electricity from renewables (TWh)": "Renewable electricity (TWh)",
        "Low-carbon electricity (% electricity)": "Low-carbon electricity (%)",
        "Primary energy consumption per capita (kWh/person)": "Energy consumption per capita",
        "Energy intensity level of primary energy (MJ/$2017 PPP GDP)": "Energy intensity",
        "Value_co2_emissions_kt_by_country": "CO2 emissions (kt)",
        "Renewables (% equivalent primary energy)": "Renewables primary energy (%)",
        "gdp_growth": "GDP growth (%)",
        "gdp_per_capita": "GDP per capita",
        "Density\\n(P/Km2)": "Population density",
        "Land Area(Km2)": "Land area (km2)",
        "Latitude": "Latitude",
        "Longitude": "Longitude",
    }
    df = df.rename(columns=rename_map)

    # Clean numeric columns
    df["Population density"] = (
        df["Population density"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .replace("nan", np.nan)
    )
    df["Population density"] = pd.to_numeric(df["Population density"], errors="coerce")

    numeric_cols = [c for c in df.columns if c not in ["Country"]]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Derived variables
    df["Estimated population"] = df["Population density"] * df["Land area (km2)"]
    df["CO2 per capita estimate (t/person)"] = np.where(
        df["Estimated population"] > 0,
        (df["CO2 emissions (kt)"] * 1000) / df["Estimated population"],
        np.nan
    )

    df["Electricity generation total (TWh)"] = (
        df["Fossil electricity (TWh)"].fillna(0)
        + df["Nuclear electricity (TWh)"].fillna(0)
        + df["Renewable electricity (TWh)"].fillna(0)
    )

    df["Fossil electricity share (%)"] = np.where(
        df["Electricity generation total (TWh)"] > 0,
        df["Fossil electricity (TWh)"] / df["Electricity generation total (TWh)"] * 100,
        np.nan
    )

    # The 2020 CO2 values are mostly missing in this dataset, so CO2-based views should use 2019 by default.
    return df


df = load_data()

# -----------------------------
# 2. Sidebar controls
# -----------------------------
st.sidebar.title("Dashboard Controls")

years = sorted(df["Year"].dropna().unique())
selected_year = st.sidebar.slider(
    "Select year",
    int(min(years)),
    int(max(years)),
    2019
)

countries = sorted(df["Country"].dropna().unique())
default_countries = [c for c in ["China", "United States", "India", "Germany", "Brazil", "Norway"] if c in countries]
selected_countries = st.sidebar.multiselect(
    "Select countries for comparison",
    countries,
    default=default_countries
)

metric_options = [
    "Electricity access (%)",
    "Clean fuels access (%)",
    "Renewable capacity per capita",
    "Renewable energy share (%)",
    "Low-carbon electricity (%)",
    "Energy consumption per capita",
    "Energy intensity",
    "CO2 emissions (kt)",
    "CO2 per capita estimate (t/person)",
    "GDP per capita",
    "GDP growth (%)",
    "Financial flows (US$)"
]

map_metric = st.sidebar.selectbox(
    "Map metric",
    metric_options,
    index=metric_options.index("Low-carbon electricity (%)")
)

rank_metric = st.sidebar.selectbox(
    "Ranking metric",
    metric_options,
    index=metric_options.index("Renewable energy share (%)")
)

rank_direction = st.sidebar.radio(
    "Ranking direction",
    ["Top 15", "Bottom 15"],
    horizontal=True
)

trend_metric = st.sidebar.selectbox(
    "Country trend metric",
    metric_options,
    index=metric_options.index("Low-carbon electricity (%)")
)

st.sidebar.caption(
    "Note: CO₂ data for 2020 is mostly missing, so use 2019 for the most reliable CO₂ comparison."
)

year_df = df[df["Year"] == selected_year].copy()
country_df = df[df["Country"].isin(selected_countries)].copy()

# -----------------------------
# 3. Header and KPI row
# -----------------------------
st.title("🌍 Global Sustainable Energy Indicators Dashboard")
st.markdown(
    """
    This dashboard explores how energy access, renewable transition, economic development, 
    electricity generation and emissions vary across countries from 2000 to 2020.
    """
)

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

kpi1.metric(
    "Avg electricity access",
    f"{year_df['Electricity access (%)'].mean():.1f}%"
)
kpi2.metric(
    "Avg clean fuels access",
    f"{year_df['Clean fuels access (%)'].mean():.1f}%"
)
kpi3.metric(
    "Avg low-carbon electricity",
    f"{year_df['Low-carbon electricity (%)'].mean():.1f}%"
)
kpi4.metric(
    "Total renewable electricity",
    f"{year_df['Renewable electricity (TWh)'].sum():,.0f} TWh"
)
co2_total = year_df["CO2 emissions (kt)"].sum(min_count=1)
kpi5.metric(
    "Total CO₂ emissions",
    "No data" if pd.isna(co2_total) else f"{co2_total/1_000_000:.1f}bn kt"
)

st.divider()

# -----------------------------
# 4. Visualisation 1: Geographic map
# -----------------------------
st.subheader("1. Geographic distribution of selected energy indicator")

map_df = year_df.dropna(subset=["Latitude", "Longitude", map_metric])
fig_map = px.scatter_geo(
    map_df,
    lat="Latitude",
    lon="Longitude",
    color=map_metric,
    hover_name="Country",
    size=np.clip(map_df["Estimated population"].fillna(1), 1, None),
    size_max=28,
    projection="natural earth",
    color_continuous_scale="Viridis",
    title=f"{map_metric} by country in {selected_year}",
    hover_data={
        map_metric: ":.2f",
        "GDP per capita": ":,.0f",
        "Electricity access (%)": ":.1f",
        "Clean fuels access (%)": ":.1f",
        "Latitude": False,
        "Longitude": False,
    }
)
fig_map.update_layout(height=520, margin=dict(l=0, r=0, t=50, b=0))
st.plotly_chart(fig_map, use_container_width=True)

# -----------------------------
# 5. Visualisation 2 + 3: Global trend and generation mix
# -----------------------------
left, right = st.columns(2)

with left:
    st.subheader("2. Global average trend over time")

    trend_metrics = st.multiselect(
        "Choose indicators for global trend",
        metric_options,
        default=["Electricity access (%)", "Clean fuels access (%)", "Low-carbon electricity (%)"],
        key="global_trend_metrics"
    )

    if trend_metrics:
        global_trend = df.groupby("Year", as_index=False)[trend_metrics].mean(numeric_only=True)
        trend_long = global_trend.melt("Year", var_name="Indicator", value_name="Average value")
        fig_trend = px.line(
            trend_long,
            x="Year",
            y="Average value",
            color="Indicator",
            markers=True,
            title="Average country-level indicator values, 2000–2020"
        )
        fig_trend.update_layout(height=430)
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Select at least one metric to display the trend.")

with right:
    st.subheader("3. Electricity generation mix over time")

    if selected_countries:
        mix_source = country_df
        mix_title = "Selected countries"
    else:
        mix_source = df
        mix_title = "All countries"

    mix = mix_source.groupby("Year", as_index=False)[
        ["Fossil electricity (TWh)", "Nuclear electricity (TWh)", "Renewable electricity (TWh)"]
    ].sum(numeric_only=True)

    mix_long = mix.melt(
        "Year",
        var_name="Source",
        value_name="Electricity generation (TWh)"
    )

    fig_mix = px.area(
        mix_long,
        x="Year",
        y="Electricity generation (TWh)",
        color="Source",
        title=f"Electricity generation by source: {mix_title}"
    )
    fig_mix.update_layout(height=430)
    st.plotly_chart(fig_mix, use_container_width=True)

# -----------------------------
# 6. Visualisation 4 + 5: Country trend and ranking
# -----------------------------
left, right = st.columns(2)

with left:
    st.subheader("4. Country drill-down trend")

    if selected_countries:
        line_df = country_df.dropna(subset=[trend_metric])
        fig_country = px.line(
            line_df,
            x="Year",
            y=trend_metric,
            color="Country",
            markers=True,
            title=f"{trend_metric} for selected countries"
        )
        fig_country.update_layout(height=430)
        st.plotly_chart(fig_country, use_container_width=True)
    else:
        st.info("Select at least one country in the sidebar for the country trend.")

with right:
    st.subheader("5. Country ranking")

    ranking_df = year_df.dropna(subset=[rank_metric]).copy()
    if rank_direction == "Top 15":
        ranking_df = ranking_df.nlargest(15, rank_metric).sort_values(rank_metric, ascending=True)
    else:
        ranking_df = ranking_df.nsmallest(15, rank_metric).sort_values(rank_metric, ascending=False)

    fig_rank = px.bar(
        ranking_df,
        x=rank_metric,
        y="Country",
        orientation="h",
        title=f"{rank_direction} countries by {rank_metric} in {selected_year}",
        hover_data={
            "GDP per capita": ":,.0f",
            "Electricity access (%)": ":.1f",
            "Low-carbon electricity (%)": ":.1f",
        }
    )
    fig_rank.update_layout(height=430, yaxis_title="")
    st.plotly_chart(fig_rank, use_container_width=True)

# -----------------------------
# 7. Visualisation 6 + 7: Relationship views
# -----------------------------
left, right = st.columns(2)

with left:
    st.subheader("6. Energy use, income and emissions relationship")

    scatter_df = year_df.dropna(subset=["GDP per capita", "Energy consumption per capita"]).copy()

    fig_scatter = px.scatter(
        scatter_df,
        x="GDP per capita",
        y="Energy consumption per capita",
        color="Low-carbon electricity (%)",
        size=np.clip(scatter_df["Estimated population"].fillna(1), 1, None),
        hover_name="Country",
        size_max=35,
        log_x=True,
        title=f"GDP per capita vs energy consumption per capita in {selected_year}",
        color_continuous_scale="Viridis",
        hover_data={
            "CO2 emissions (kt)": ":,.0f",
            "Renewable energy share (%)": ":.1f",
            "Clean fuels access (%)": ":.1f",
        }
    )
    fig_scatter.update_layout(height=450)
    st.plotly_chart(fig_scatter, use_container_width=True)

with right:
    st.subheader("7. Energy access inequality")

    access_df = year_df.dropna(subset=["Electricity access (%)", "Clean fuels access (%)"]).copy()

    fig_access = px.scatter(
        access_df,
        x="Electricity access (%)",
        y="Clean fuels access (%)",
        color="Renewable energy share (%)",
        size=np.clip(access_df["Estimated population"].fillna(1), 1, None),
        hover_name="Country",
        size_max=35,
        title=f"Electricity access vs clean fuels access in {selected_year}",
        color_continuous_scale="Plasma",
        hover_data={
            "GDP per capita": ":,.0f",
            "Low-carbon electricity (%)": ":.1f",
            "Energy intensity": ":.2f",
        }
    )
    fig_access.update_xaxes(range=[0, 105])
    fig_access.update_yaxes(range=[0, 105])
    fig_access.update_layout(height=450)
    st.plotly_chart(fig_access, use_container_width=True)

# -----------------------------
# 8. Visualisation 8: Correlation heatmap
# -----------------------------
st.subheader("8. Correlation between sustainable energy indicators")

corr_metrics = [
    "Electricity access (%)",
    "Clean fuels access (%)",
    "Renewable capacity per capita",
    "Renewable energy share (%)",
    "Low-carbon electricity (%)",
    "Energy consumption per capita",
    "Energy intensity",
    "CO2 emissions (kt)",
    "GDP per capita",
    "GDP growth (%)"
]

corr_df = year_df[corr_metrics].corr(numeric_only=True)

fig_corr = px.imshow(
    corr_df,
    text_auto=".2f",
    aspect="auto",
    color_continuous_scale="RdBu_r",
    zmin=-1,
    zmax=1,
    title=f"Correlation matrix for selected year: {selected_year}"
)
fig_corr.update_layout(height=650)
st.plotly_chart(fig_corr, use_container_width=True)

# -----------------------------
# 9. Data table and notes
# -----------------------------
with st.expander("View filtered data table"):
    display_cols = [
        "Country", "Year", "Electricity access (%)", "Clean fuels access (%)",
        "Renewable energy share (%)", "Low-carbon electricity (%)",
        "Fossil electricity (TWh)", "Nuclear electricity (TWh)",
        "Renewable electricity (TWh)", "Energy consumption per capita",
        "Energy intensity", "CO2 emissions (kt)", "GDP per capita"
    ]
    st.dataframe(year_df[display_cols], use_container_width=True)

with st.expander("Data preparation notes"):
    st.markdown(
        """
        - Column names were shortened to improve readability in the interface.
        - Population density was converted from text to numeric values.
        - Estimated population was calculated from population density × land area and used only for bubble sizing.
        - CO₂ per capita is estimated from CO₂ emissions and estimated population, so it should be interpreted carefully.
        - Missing values were not replaced with artificial values; charts drop missing values only for the variables being plotted.
        - The 2020 CO₂ column is mostly missing in the source data, so 2019 is the recommended year for CO₂-based analysis.
        """
    )
