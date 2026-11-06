
import streamlit as st
import pandas as pd
import plotly.express as px
import ast
import json
import re

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="IMDb Movie Analytics Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. CUSTOM CSS
# ==========================================

st.markdown("""
<style>
.stApp {
    background: #101827;
    color: white;
}

[data-testid="stSidebar"] {
    background: #182337;
    border-right: 1px solid #35445c;
}

[data-testid="stSidebar"] * {
    color: white;
}

.main .block-container {
    padding: 1rem 1.2rem;
    max-width: 1600px;
}

.dashboard-banner {
    background: linear-gradient(
        100deg, #17243b, #263d60, #111827
    );
    padding: 25px;
    border-radius: 10px;
    text-align: center;
    border: 1px solid #35445c;
    margin-bottom: 15px;
}

.dashboard-banner h1 {
    color: white;
    font-size: 30px;
    margin-bottom: 5px;
}

.dashboard-banner p {
    color: #d6deed;
    margin: 0;
}

.kpi {
    padding: 17px;
    border-radius: 10px;
    color: white;
    text-align: center;
    min-height: 100px;
}

.kpi h4 {
    font-size: 14px;
    margin: 0;
}

.kpi h2 {
    font-size: 27px;
    margin-top: 8px;
}

.blue { background: #1768b3; }
.green { background: #1c9b65; }
.purple { background: #743bb8; }
.orange { background: #f1840b; }

[data-testid="stMetric"] {
    background: #1c2940;
    padding: 12px;
    border-radius: 8px;
}

.stTabs [data-baseweb="tab"] {
    color: white;
}

hr {
    border-color: #35445c;
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# 3. LOAD DATASET
# ==========================================

@st.cache_data
def load_data():
    return pd.read_csv("movies.csv")

try:
    df = load_data()
    df = df.dropna(how="all").copy()

except Exception as e:
    st.error(f"Dataset loading error: {e}")
    st.stop()

if df.empty:
    st.error("Your movies.csv file is empty.")
    st.stop()


# ==========================================
# 4. FIND DATASET COLUMNS
# ==========================================

def find_col(names):

    normalized = {
        re.sub(r"[^a-z0-9]", "", str(c).lower()): c
        for c in df.columns
    }

    for name in names:
        key = re.sub(r"[^a-z0-9]", "", name.lower())

        if key in normalized:
            return normalized[key]

    return None


title_col = find_col([
    "primaryTitle", "title", "originalTitle"
])

rating_col = find_col([
    "averageRating", "imdbRating", "rating"
])

votes_col = find_col([
    "numVotes", "votes", "numberOfVotes"
])

genre_col = find_col([
    "genres", "genre", "interests"
])

country_col = find_col([
    "countriesOfOrigin", "country", "countries"
])

gross_col = find_col([
    "grossWorldwide", "worldwideGross",
    "worldwide_gross", "gross"
])

year_col = find_col([
    "startYear", "year", "releaseYear"
])

description_col = find_col([
    "description", "plot"
])

image_col = find_col([
    "primaryImage", "image", "poster"
])


# ==========================================
# 5. DATA CLEANING
# ==========================================

def split_values(value):

    if isinstance(value, (list, tuple)):
        return [str(x).strip() for x in value] or ["Other"]

    if pd.isna(value):
        return ["Other"]

    value = str(value).strip()

    if not value:
        return ["Other"]

    # Handle JSON or Python list strings
    try:
        parsed = json.loads(value)

        if isinstance(parsed, list):
            return [str(x).strip() for x in parsed] or ["Other"]

    except (ValueError, TypeError):
        pass

    try:
        parsed = ast.literal_eval(value)

        if isinstance(parsed, (list, tuple)):
            return [str(x).strip() for x in parsed] or ["Other"]

    except (ValueError, SyntaxError):
        pass

    # Handle normal comma-separated values
    return [
        x.strip().strip("'\"[]")
        for x in value.split(",")
        if x.strip().strip("'\"[]")
    ] or ["Other"]


def numeric_column(column):

    if not column:
        return pd.Series(float("nan"), index=df.index)

    return pd.to_numeric(
        df[column].astype(str).str.replace(
            r"[^0-9.\-]", "", regex=True
        ),
        errors="coerce"
    )


work = df.copy()

work["_title"] = (
    work[title_col].fillna("Unknown").astype(str)
    if title_col else "Unknown"
)

work["_rating"] = numeric_column(rating_col)
work["_votes"] = numeric_column(votes_col)
work["_gross"] = numeric_column(gross_col)
work["_year"] = numeric_column(year_col)

work["_genre"] = (
    work[genre_col].fillna("Other").astype(str)
    if genre_col else "Other"
)

work["_country"] = (
    work[country_col].fillna("Unknown").astype(str)
    if country_col else "Unknown"
)

work["_genres_list"] = work["_genre"].apply(split_values)
work["_countries_list"] = work["_country"].apply(split_values)


# ==========================================
# 6. SIDEBAR
# ==========================================

st.sidebar.markdown("""
# 🟨 IMDb

## Movie Analytics Dashboard

---
""")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "🎬 Movie Explorer",
        "🔍 Movie Search",
        "📊 Dataset Information"
    ]
)

st.sidebar.markdown("---")

st.sidebar.markdown("### Dataset Information")

st.sidebar.write("**Top 250 Movies on IMDb**")
st.sidebar.write(f"Rows: {len(work)}")
st.sidebar.write(f"Columns: {len(df.columns)}")

st.sidebar.info(
    "Explore movie titles, genres, ratings, "
    "votes and available movie information."
)


# ==========================================
# 7. HEADER
# ==========================================

st.markdown("""
<div class="dashboard-banner">

<h1>🎬 IMDb Movie Analytics Dashboard</h1>

<p>Explore. Analyze. Discover.</p>

</div>
""", unsafe_allow_html=True)


# ==========================================
# 8. KPI CARDS
# ==========================================

total_movies = len(work)

avg_rating = work["_rating"].mean()
highest_rating = work["_rating"].max()
total_votes = work["_votes"].sum()


def show_kpi(col, title, value, css):

    col.markdown(
        f"""
        <div class="kpi {css}">
            <h4>{title}</h4>
            <h2>{value}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )


k1, k2, k3, k4 = st.columns(4)

show_kpi(k1, "🎬 Total Movies",
         f"{total_movies:,}", "blue")

show_kpi(
    k2,
    "⭐ Average IMDb Rating",
    f"{avg_rating:.2f}" if pd.notna(avg_rating) else "N/A",
    "green"
)

show_kpi(
    k3,
    "🏆 Highest Rating",
    f"{highest_rating:.1f}" if pd.notna(highest_rating) else "N/A",
    "purple"
)

show_kpi(
    k4,
    "👥 Total Votes",
    f"{total_votes:,.0f}" if pd.notna(total_votes) else "N/A",
    "orange"
)

st.markdown("---")


# ==========================================
# 9. DASHBOARD CHARTS
# ==========================================

if page == "🏠 Dashboard":

    tab1, tab2, tab3 = st.tabs([
        "📊 Genre Analysis",
        "⭐ Rating Analysis",
        "💰 Gross Collection"
    ])

    # -------- GENRE CHART --------

    with tab1:

        left, right = st.columns(2)

        with left:

            st.markdown("### 📊 Movies by Genre")

            genre_data = work.explode("_genres_list")

            genre_counts = (
                genre_data["_genres_list"]
                .value_counts()
                .head(10)
                .reset_index()
            )

            genre_counts.columns = ["Genre", "Movies"]

            fig = px.bar(
                genre_counts,
                x="Genre",
                y="Movies",
                color="Genre",
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Bold
            )

            fig.update_layout(
                height=320,
                showlegend=False,
                margin=dict(t=20, b=20),
                plot_bgcolor="#101827",
                paper_bgcolor="#101827"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        # -------- COUNTRY CHART --------

        with right:

            st.markdown("### 🌍 Movies by Country")

            # FIXED COUNTRY EXPLODE ERROR

            country_data = work.copy()

            country_data["_country_list"] = (
                country_data["_country"].apply(split_values)
            )

            country_data = country_data.explode(
                "_country_list"
            )

            country_counts = (
                country_data["_country_list"]
                .value_counts()
                .head(10)
                .reset_index()
            )

            country_counts.columns = [
                "Country", "Movies"
            ]

            fig = px.bar(
                country_counts,
                x="Movies",
                y="Country",
                orientation="h",
                color="Movies",
                template="plotly_dark"
            )

            fig.update_layout(
                height=320,
                margin=dict(t=20, b=20),
                plot_bgcolor="#101827",
                paper_bgcolor="#101827"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    # -------- RATING CHARTS --------

    with tab2:

        left, right = st.columns(2)

        with left:

            st.markdown("### ⭐ IMDb Rating Distribution")

            rating_data = work.dropna(
                subset=["_rating"]
            )

            if not rating_data.empty:

                fig = px.histogram(
                    rating_data,
                    x="_rating",
                    nbins=15,
                    color_discrete_sequence=["#2588e8"],
                    template="plotly_dark"
                )

                fig.update_layout(
                    height=330,
                    xaxis_title="IMDb Rating",
                    yaxis_title="Count",
                    plot_bgcolor="#101827",
                    paper_bgcolor="#101827"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            else:
                st.warning("IMDb rating data is unavailable.")

        with right:

            st.markdown("### 📈 Rating vs Number of Votes")

            scatter_data = work.dropna(
                subset=["_rating", "_votes"]
            )

            if not scatter_data.empty:

                fig = px.scatter(
                    scatter_data,
                    x="_rating",
                    y="_votes",
                    hover_name="_title",
                    color="_rating",
                    template="plotly_dark"
                )

                fig.update_layout(
                    height=330,
                    plot_bgcolor="#101827",
                    paper_bgcolor="#101827"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            else:
                st.warning(
                    "Rating or votes data is unavailable."
                )

    # -------- GROSS COLLECTION --------

    with tab3:

        st.markdown(
            "### 🏆 Top 10 Movies by Worldwide Gross"
        )

        gross_data = work.dropna(
            subset=["_gross"]
        )

        if not gross_data.empty:

            top_gross = gross_data.nlargest(
                10, "_gross"
            ).sort_values("_gross")

            fig = px.bar(
                top_gross,
                x="_gross",
                y="_title",
                orientation="h",
                color="_gross",
                template="plotly_dark",
                labels={
                    "_gross": "Worldwide Gross",
                    "_title": "Movie"
                }
            )

            fig.update_layout(
                height=430,
                plot_bgcolor="#101827",
                paper_bgcolor="#101827"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:
            st.warning(
                "Worldwide gross information is not available "
                "in your dataset."
            )

    st.success(
        "Dashboard loaded successfully! "
        "Enjoy exploring IMDb movies."
    )


    # ======================================
    # 10. INTERACTIVE MOVIE EXPLORER
    # ======================================

    st.markdown("---")

    left, right = st.columns(
        [1.7, 0.8]
    )

    with left:

        st.markdown("## 🎬 Interactive Movie Explorer")

        c1, c2, c3 = st.columns(3)

        genres = sorted(
            set(
                g
                for items in work["_genres_list"]
                for g in items
            )
        )

        countries = sorted(
            set(
                c
                for items in work["_countries_list"]
                for c in items
            )
        )

        selected_genre = c1.selectbox(
            "Genre",
            ["All"] + genres
        )

        selected_country = c2.selectbox(
            "Country",
            ["All"] + countries
        )

        valid_ratings = work["_rating"].dropna()

        if not valid_ratings.empty:

            rating_min = float(valid_ratings.min())
            rating_max = float(valid_ratings.max())

            if rating_min == rating_max:
                rating_min = max(0.0, rating_min - 0.1)
                rating_max = min(10.0, rating_max + 0.1)

            selected_rating = c3.slider(
                "Minimum IMDb Rating",
                rating_min,
                rating_max,
                rating_min
            )

        else:
            selected_rating = 0.0
            c3.info("Ratings unavailable")

        search_title = st.text_input(
            "Search Title",
            placeholder="Enter movie title..."
        )

        filtered = work.copy()

        if selected_genre != "All":

            filtered = filtered[
                filtered["_genres_list"].apply(
                    lambda x: selected_genre in x
                )
            ]

        if selected_country != "All":

            filtered = filtered[
                filtered["_countries_list"].apply(
                    lambda x: selected_country in x
                )
            ]

        filtered = filtered[
            filtered["_rating"].isna()
            | (filtered["_rating"] >= selected_rating)
        ]

        if search_title:

            filtered = filtered[
                filtered["_title"].str.contains(
                    search_title,
                    case=False,
                    na=False
                )
            ]

        st.info(
            f"Filtered Movies: {len(filtered)}"
        )

        display_cols = [
            c for c in [
                title_col,
                genre_col,
                country_col,
                rating_col,
                votes_col,
                gross_col,
                year_col
            ]
            if c is not None
        ]

        if display_cols:

            st.dataframe(
                filtered[display_cols],
                use_container_width=True,
                hide_index=True
            )

    # ======================================
    # 11. MOVIE SEARCH
    # ======================================

    with right:

        st.markdown("## 🔍 Movie Search")

        movie_search = st.text_input(
            "Movie Title",
            placeholder="Enter movie title..."
        )

        search_genre = st.selectbox(
            "Preferred Genre",
            ["All"] + genres,
            key="search_genre"
        )

        search_rating = st.slider(
            "Minimum IMDb Rating",
            0.0,
            10.0,
            7.0,
            key="search_rating"
        )

        if st.button(
            "🔍 Search Movie",
            use_container_width=True
        ):

            results = work.copy()

            if movie_search:

                results = results[
                    results["_title"].str.contains(
                        movie_search,
                        case=False,
                        na=False
                    )
                ]

            if search_genre != "All":

                results = results[
                    results["_genres_list"].apply(
                        lambda x: search_genre in x
                    )
                ]

            results = results[
                results["_rating"].isna()
                | (results["_rating"] >= search_rating)
            ]

            st.write(
                f"Found {len(results)} movies"
            )

            for _, movie in results.head(5).iterrows():

                st.markdown(
                    f"**🎬 {movie['_title']}**"
                )

                st.write(
                    f"Genre: {movie['_genre']}"
                )

                st.write(
                    f"Rating: {movie['_rating']}"
                )

                if description_col:
                    st.caption(
                        str(movie[description_col])
                    )

                if image_col:

                    image_url = movie[image_col]

                    if (
                        isinstance(image_url, str)
                        and image_url.startswith("http")
                    ):

                        st.image(
                            image_url,
                            width=120
                        )

                st.markdown("---")


# ==========================================
# 12. MOVIE EXPLORER PAGE
# ==========================================

elif page == "🎬 Movie Explorer":

    st.title("🎬 Movie Explorer")

    search = st.text_input(
        "Search Movie"
    )

    filtered = work.copy()

    if search:

        filtered = filtered[
            filtered["_title"].str.contains(
                search,
                case=False,
                na=False
            )
        ]

    st.metric(
        "Total Matching Movies",
        len(filtered)
    )

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# 13. MOVIE SEARCH PAGE
# ==========================================

elif page == "🔍 Movie Search":

    st.title("🔍 Movie Search")

    search = st.text_input(
        "Enter Movie Name"
    )

    if search:

        results = work[
            work["_title"].str.contains(
                search,
                case=False,
                na=False
            )
        ]

        if results.empty:

            st.warning("Movie not found.")

        else:

            for _, movie in results.iterrows():

                st.subheader(
                    movie["_title"]
                )

                st.write(
                    "Genre:", movie["_genre"]
                )

                st.write(
                    "Country:", movie["_country"]
                )

                st.write(
                    "Rating:", movie["_rating"]
                )

                if description_col:
                    st.write(movie[description_col])

                if image_col:

                    image_url = movie[image_col]

                    if (
                        isinstance(image_url, str)
                        and image_url.startswith("http")
                    ):
                        st.image(
                            image_url,
                            width=150
                        )

                st.divider()


# ==========================================
# 14. DATASET INFORMATION PAGE
# ==========================================

elif page == "📊 Dataset Information":

    st.title("📊 Dataset Information")

    c1, c2 = st.columns(2)

    c1.metric("Total Movies", len(work))
    c2.metric("Total Columns", len(df.columns))

    st.subheader("Dataset Preview")

    st.dataframe(
        df.head(20),
        use_container_width=True
    )

    st.subheader("All Column Names")

    st.write(df.columns.tolist())

    st.subheader("Missing Values")

    missing = df.isnull().sum().reset_index()

    missing.columns = [
        "Column",
        "Missing Values"
    ]

    st.dataframe(
        missing,
        use_container_width=True
    )

    st.subheader("Data Types")

    st.write(df.dtypes.astype(str))
