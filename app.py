import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# Set page configuration to wide layout and set title/icon
st.set_page_config(
    page_title="Bike Sharing Analysis Dashboard",
    page_icon="🚲",
    layout="wide"
)

# Custom CSS for modern styling and KPI cards
st.markdown("""
    <style>
        /* General layout improvements */
        .main {
            background-color: #f8f9fa;
        }
        
        /* Adjusting font sizes for comfortable viewing */
        html, body, [data-testid="stMarkdownContainer"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        /* Adjust header sizes to be ideal and comfortable */
        h1 {
            font-size: 1.8rem !important;
            font-weight: 700 !important;
            color: #1e293b !important;
            margin-bottom: 0.5rem !important;
        }
        h2 {
            font-size: 1.3rem !important;
            font-weight: 600 !important;
            color: #334155 !important;
        }
        h3, [data-testid="stMarkdownContainer"] h3 {
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            color: #475569 !important;
            margin-top: 1rem !important;
            margin-bottom: 0.5rem !important;
        }
        
        /* Custom metric card container */
        .kpi-container {
            display: flex;
            justify-content: space-between;
            gap: 20px;
            margin-bottom: 25px;
        }
        .kpi-card {
            flex: 1;
            background: white;
            padding: 16px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            border-left: 5px solid #66b3ff;
            text-align: center;
        }
        .kpi-card.registered {
            border-left-color: #4caf50;
        }
        .kpi-card.casual {
            border-left-color: #ff9800;
        }
        .kpi-title {
            font-size: 12px;
            color: #64748b;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }
        .kpi-value {
            font-size: 24px;
            font-weight: 700;
            color: #0f172a;
        }
    </style>
""", unsafe_allow_html=True)

# Helper function to load and clean data
@st.cache_data
def load_data():
    # Load raw data
    day_df = pd.read_csv("data/day.csv")
    hour_df = pd.read_csv("data/hour.csv")

    # Cleaning: Dropping workingday column as per original notebook logic
    day_df.drop("workingday", axis=1, inplace=True, errors='ignore')
    hour_df.drop("workingday", axis=1, inplace=True, errors='ignore')

    # Rename columns
    rename_cols_day = {
        "dteday": "date_day",
        "yr": "year",
        "mnth": "month",
        "weekday": "day_of_week",
        "weathersit": "weather_sit",
        "hum": "humidity",
        "cnt": "total_rental"
    }
    rename_cols_hour = {
        "dteday": "date_day",
        "yr": "year",
        "mnth": "month",
        "hr": "hour",
        "weekday": "day_of_week",
        "weathersit": "weather_sit",
        "hum": "humidity",
        "cnt": "total_rental"
    }
    day_df.rename(columns=rename_cols_day, inplace=True)
    hour_df.rename(columns=rename_cols_hour, inplace=True)

    # Convert date_day to datetime
    day_df["date_day"] = pd.to_datetime(day_df["date_day"])
    hour_df["date_day"] = pd.to_datetime(hour_df["date_day"])

    # Replace values with descriptions first
    column_season = {1: "Spring", 2: "Summer", 3: "Fall", 4: "Winter"}
    column_year = {0: 2011, 1: 2012}
    column_month = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }
    column_day_of_week = {
        0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat"
    }
    column_weather_sit = {
        1: "Clear", 2: "Mist", 3: "Light rain", 4: "Heavy Rain"
    }

    for df in [day_df, hour_df]:
        df["season"] = df["season"].replace(column_season)
        df["year"] = df["year"].replace(column_year)
        df["month"] = df["month"].replace(column_month)
        df["day_of_week"] = df["day_of_week"].replace(column_day_of_week)
        df["weather_sit"] = df["weather_sit"].replace(column_weather_sit)

    # Categorical conversions after replacements
    categorical_columns_day = ["season", "year", "month", "day_of_week", "weather_sit"]
    categorical_columns_hour = ["season", "year", "month", "hour", "day_of_week", "weather_sit"]

    for col in categorical_columns_day:
        day_df[col] = day_df[col].astype("category")
    for col in categorical_columns_hour:
        hour_df[col] = hour_df[col].astype("category")

    # Add category_day column matching the logic in notebook:
    # "if day_of_week <= 'Thu': return 'weekday' else: return 'weekend'"
    def category_day(day_of_week):
        dow_str = str(day_of_week)
        if dow_str <= "Thu":
            return "weekday"
        else:
            return "weekend"

    day_df["category_day"] = day_df["day_of_week"].apply(category_day)
    hour_df["category_day"] = hour_df["day_of_week"].apply(category_day)

    return day_df, hour_df

# Load datasets
day_df, hour_df = load_data()

# ----------------- SIDEBAR FILTER -----------------
st.sidebar.image("https://images.unsplash.com/photo-1485965120184-e220f721d03e?auto=format&fit=crop&w=300&q=80", width="stretch")
st.sidebar.title("Dashboard Filter 🚲")

# Season selection
seasons_list = list(day_df["season"].unique())
selected_seasons = st.sidebar.multiselect(
    label="Pilih Musim (Season)",
    options=seasons_list,
    default=seasons_list
)

# Weather situation selection
weather_list = list(day_df["weather_sit"].unique())
selected_weather = st.sidebar.multiselect(
    label="Pilih Kondisi Cuaca",
    options=weather_list,
    default=weather_list
)

# Filter dynamically based on category selection to restrict date range limits
cat_filtered = day_df[
    day_df["season"].isin(selected_seasons) & 
    day_df["weather_sit"].isin(selected_weather)
]

if not cat_filtered.empty:
    min_date = cat_filtered["date_day"].min().date()
    max_date = cat_filtered["date_day"].max().date()
else:
    min_date = day_df["date_day"].min().date()
    max_date = day_df["date_day"].max().date()

# Date range selection
date_range = st.sidebar.date_input(
    label="Pilih Rentang Tanggal",
    min_value=min_date,
    max_value=max_date,
    value=[min_date, max_date]
)

if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

# Convert selection to datetime
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

# Apply filters to dataframes
main_day_df = day_df[
    (day_df["date_day"] >= start_date) & 
    (day_df["date_day"] <= end_date) & 
    (day_df["season"].isin(selected_seasons)) & 
    (day_df["weather_sit"].isin(selected_weather))
]

main_hour_df = hour_df[
    (hour_df["date_day"] >= start_date) & 
    (hour_df["date_day"] <= end_date) & 
    (hour_df["season"].isin(selected_seasons)) & 
    (hour_df["weather_sit"].isin(selected_weather))
]

# ----------------- MAIN CONTENT -----------------
st.title("🚲 Bike Sharing Interactive Dashboard")
st.markdown("Dashboard interaktif untuk menganalisis penyewaan sepeda berdasarkan faktor musim, waktu, dan hari.")

# Validate if data is available after filtering
if main_day_df.empty:
    st.warning("Tidak ada data yang cocok dengan filter yang dipilih.")
else:
    # 1. KPI Cards Row
    total_rentals = main_day_df["total_rental"].sum()
    total_registered = main_day_df["registered"].sum()
    total_casual = main_day_df["casual"].sum()

    st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-card">
                <div class="kpi-title">Total Rentals</div>
                <div class="kpi-value">{total_rentals:,}</div>
            </div>
            <div class="kpi-card registered">
                <div class="kpi-title">Registered Users</div>
                <div class="kpi-value">{total_registered:,}</div>
            </div>
            <div class="kpi-card casual">
                <div class="kpi-title">Casual Users</div>
                <div class="kpi-value">{total_casual:,}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 2. Tabs or layout sections for visualisations
    tab1, tab2, tab3 = st.tabs(["📊 Analisis Musim", "⏰ Analisis Waktu", "📅 Analisis Hari"])

    # Tab 1: Season analysis
    with tab1:
        st.subheader("Pertanyaan 1: Diantara musim semi dan musim gugur, dimusim apa penyewaan paling banyak?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Perbandingan Musim Gugur (Fall) vs Musim Semi (Spring)")
            spring_fall_df = main_day_df[main_day_df['season'].isin(["Spring", "Fall"])].copy()
            
            if not spring_fall_df.empty:
                spring_fall_grouped = spring_fall_df.groupby("season", observed=True)["total_rental"].sum().reset_index()
                spring_fall_grouped["season"] = pd.Categorical(spring_fall_grouped["season"], categories=["Fall", "Spring"], ordered=True)
                spring_fall_grouped = spring_fall_grouped.sort_values(by="season")

                fig = px.bar(
                    spring_fall_grouped,
                    x="season",
                    y="total_rental",
                    color="season",
                    color_discrete_map={"Fall": "lightskyblue", "Spring": "lightgray"},
                    title="Jumlah Total Rental Berdasarkan Season Spring dan Fall",
                    labels={"season": "Season", "total_rental": "Total Rental"}
                )
                fig.update_layout(
                    showlegend=False,
                    title_font_size=13,
                    margin=dict(l=40, r=40, t=50, b=40),
                    height=350
                )
                fig.update_traces(
                    hovertemplate="<b>%{x}</b><br>Total Rental: %{y:,}<extra></extra>"
                )
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Musim Spring atau Fall tidak terpilih dalam filter.")

        with col2:
            st.markdown("### Total Rental untuk Seluruh Musim")
            season_rentals = main_day_df.groupby(by="season", observed=True).total_rental.sum().reset_index()
            season_rentals["season"] = pd.Categorical(
                season_rentals["season"], 
                categories=["Fall", "Summer", "Winter", "Spring"], 
                ordered=True
            )
            season_rentals = season_rentals.sort_values("season")

            fig = px.bar(
                season_rentals,
                x="season",
                y="total_rental",
                color="season",
                color_discrete_map={
                    "Fall": "lightskyblue",
                    "Summer": "lightgray",
                    "Winter": "lightgray",
                    "Spring": "lightgray"
                },
                title="Jumlah Total Rental Berdasarkan Seluruh Season",
                labels={"season": "Season", "total_rental": "Total Rental"}
            )
            fig.update_layout(
                showlegend=False,
                title_font_size=13,
                margin=dict(l=40, r=40, t=50, b=40),
                height=350
            )
            fig.update_traces(
                hovertemplate="<b>%{x}</b><br>Total Rental: %{y:,}<extra></extra>"
            )
            st.plotly_chart(fig, width="stretch")

    # Tab 2: Time analysis
    with tab2:
        st.subheader("Pertanyaan 2: Pada waktu kapan yang paling banyak melakukan registered?")
        st.markdown("### Distribusi Total Registered Rental Berdasarkan Jam")
        
        if not main_hour_df.empty:
            hour_registered = main_hour_df.groupby('hour', observed=True)['registered'].sum().reset_index()
            if not hour_registered.empty:
                peak_hour = hour_registered.loc[hour_registered['registered'].idxmax(), 'hour']
                
                fig = px.bar(
                    hour_registered,
                    x="hour",
                    y="registered",
                    title=f"Total Registered Berdasarkan Jam (Highlight Puncak Jam {peak_hour}:00)",
                    labels={"hour": "Jam (Hour)", "registered": "Jumlah Registered"}
                )
                plotly_colors = ["lightskyblue" if hr == peak_hour else "lightgray" for hr in hour_registered["hour"]]
                fig.update_traces(
                    marker_color=plotly_colors,
                    hovertemplate="<b>Jam %{x}:00</b><br>Registered: %{y:,}<extra></extra>"
                )
                fig.update_layout(
                    title_font_size=13,
                    margin=dict(l=40, r=40, t=50, b=40),
                    height=380
                )
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Tidak ada data jam tersedia.")
        else:
            st.info("Pilih rentang filter yang memuat data per jam.")

    # Tab 3: Day category analysis
    with tab3:
        st.subheader("Pertanyaan 3: Apakah peminjaman sepeda lebih tinggi pada hari kerja dibanding dengan akhir pekan?")
        st.markdown("### Persentase Total Penyewaan Berdasarkan Kategori Hari")
        
        category_rental = main_day_df.groupby('category_day', observed=True)['total_rental'].sum().reset_index()
        
        if not category_rental.empty:
            fig = px.pie(
                category_rental,
                values='total_rental',
                names='category_day',
                title='Banyaknya Total Penyewaan Berdasarkan Kategori Hari (Weekday/Weekend)',
                color_discrete_sequence=['#66b3ff', '#ff9999']
            )
            fig.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate="<b>%{label}</b><br>Total Rental: %{value:,}<br>Persentase: %{percent}<extra></extra>"
            )
            fig.update_layout(
                title_font_size=13,
                margin=dict(l=40, r=40, t=50, b=40),
                height=380
            )
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Tidak ada data kategori hari.")

    # 3. Raw Data Section
    st.markdown("---")
    with st.expander("🔍 Lihat Detail Data Terfilter"):
        st.dataframe(main_day_df)
