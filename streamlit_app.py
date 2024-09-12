import asyncio
import importlib.util
from datetime import datetime

import pandas as pd
from openbb_core.app.utils import basemodel_to_df

import streamlit as st

st.set_page_config(
    layout="wide",
    page_title="Relative Rotation",
    initial_sidebar_state="expanded",
)

symbols = []
benchmark = ""
STUDY_CHOICES = ["Price", "Volume", "Volatility"]
SOURCE_CHOICES = ["Yahoo Finance", "Cboe"]
source_input = "Yahoo Finance"
source_dict = {"Yahoo Finance": "yfinance","Cboe": "cboe"}
source=source_dict[source_input]
window_input = 21
study = "price"
short_period = 21
long_period = 252
window = 21
trading_periods_input = 252
trading_periods = 252
tail_interval = "week"
tail_interval_input = "week"
tail_periods_input = 30
tail_periods = 30
show_tails = False
st.session_state.rrg_data = st.empty()
st.session_state.date = None
st.session_state.fig = None
rrg_data = st.empty()
st.session_state.data_tables = None

def import_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

module = import_from_file("module", "relative_rotation.py")

st.sidebar.markdown(
    """
<style>
section[data-testid="stSidebar"] {
    top: 1% !important;
    height: 98.25% !important;
    left: 0.33% !important;
    margin-top: 0 !important;
}
a:contains('GitHub') {
        display: none !important;
    }
    footer {visibility: hidden;}
section[data-testid="stSidebar"] img {
    margin-top: -75px !important;
    margin-left: -10px !important;
    width: 95% !important;
}
section[data-testid="stVerticalBlock"] {
    gap: 0rem;
}
body {
    line-height: 1.2;
}
#GithubIcon {
  visibility: hidden;
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    .css-1jc7ptx, .e1ewe7hr3, .viewerBadge_container__1QSob,
    .styles_viewerBadge__1yB5_, .viewerBadge_link__1S137,
    .viewerBadge_text__1JaDK {
        display: none;
    }
    #MainMenu {
    visibility: hidden;
}
    </style>
    """,
    unsafe_allow_html=True
)
hide_github_icon = """
#GithubIcon {
  visibility: hidden;
}
"""
st.markdown(hide_github_icon, unsafe_allow_html=True)

st.sidebar.header("Relative Rotation Graph")

with st.sidebar:
    source_input = st.selectbox("Data Source", SOURCE_CHOICES, index=0, key="source")
r2c1, r2c2 = st.sidebar.columns([1, 1])

with r2c1:
    input_string = st.text_input("Symbols", value=",".join(module.SPDRS), key="tickers").replace(" ", "")
    if input_string == "":
        st.write("Enter a list of tickers")

with r2c2:
    benchmark_input = st.text_input("Benchmark", value="SPY", key="benchmark")
    if benchmark_input == "":
        st.write("Enter a benchmark")

date_input = st.sidebar.date_input("Target End Date", value=datetime.today(), key="date_input")
st.session_state.date = date_input

with st.sidebar:
    study_input = st.sidebar.selectbox("Study", STUDY_CHOICES, key="study")
    if study_input == "Volatility":
        st.sidebar.header("Volatility Annualization")
        r4c1, r4c2 = st.sidebar.columns([1, 1])
        with r4c1:
            window_input = st.number_input("Rolling Window", min_value=0, value=21, key="window")
        with r4c2:
            trading_periods_input = st.number_input("Periods Per Year", min_value=0, value=252, key="trading_periods")

st.sidebar.header("Long/Short Momentum Periods")

r3c1, r3c2 = st.sidebar.columns([1, 1])  # Create a new set of columns

with r3c1:
    long_period_input = st.number_input("Long Period", min_value=0, value=252,key="long_period")

with r3c2:
    short_period_input = st.number_input("Short Period", min_value=0, value = 21, key="short_period")

# Initialize the session state for the button if it doesn't exist
if "button_clicked" not in st.session_state:
    st.session_state.button_clicked = False

# When the button is clicked, update the session state
if st.sidebar.button("Fetch Data"):
    st.session_state.button_clicked = True

with st.sidebar:
    show_tails_input = st.checkbox("Show Tails", value=False, key="show_tails")
    r5c1, r5c2 = st.sidebar.columns([1, 1])
    with r5c1:
        tail_periods_input = st.number_input("Tail Periods", min_value=0, value=30, key="tail_periods")
    with r5c2:
        tail_interval_input = st.selectbox("Tail Interval", ["Week", "Month"], key="tail_interval", index=0)


symbols = input_string.upper().split(",")
benchmark = benchmark_input.split(",")[0].upper()
study = study_input.lower()
long_period = long_period_input
short_period = short_period_input
show_tails=show_tails_input
tail_periods = tail_periods_input
tail_interval = tail_interval_input.lower()
window = window_input
trading_periods = trading_periods_input
date = date_input
source = source_dict[source_input]

if st.session_state.button_clicked:
    try:
        rrg_data = asyncio.run(module.create(
            symbols = symbols,
            benchmark = benchmark,
            study = study,
            date = pd.to_datetime(date),
            long_period = long_period,
            short_period = short_period,
            window = window,
            trading_periods = trading_periods,
            tail_periods = tail_periods,
            tail_interval = tail_interval,
            provider=source,
        ))
        st.session_state.rrg_data = rrg_data
        st.session_state.first_run = False
    except Exception:
        st.session_state.rrg_data = None
        st.session_state.first_run = True
        if input_string != "" and benchmark_input != "":
            st.write(
                "There was an error fetching the data."
                " Please check if the symbols are correct and available at the source."
                " Volume data may not exist for most indexes, for example."
            )
        if input_string == "" or benchmark_input == "":
            st.write("Please enter a list of symbols and a benchmark.")


main_chart = st.expander("Relative Rotation Graph", expanded=True)

if "first_run" not in st.session_state:
    st.session_state.first_run = True

if not st.session_state.first_run and st.session_state.rrg_data is not None:
    with main_chart:
        fig = (
            st.session_state.rrg_data.show(date, show_tails, tail_periods, tail_interval, external=True)
            if show_tails is False
            else st.session_state.rrg_data.show(show_tails=show_tails, tail_periods=tail_periods, tail_interval=tail_interval, external=True)
        )
        fig.update_layout(height=600, margin=dict(l=0, r=20, b=0, t=50, pad=0))
        st.session_state.fig = fig
        st.plotly_chart(
            st.session_state.fig,
            use_container_width=True,
            config={
                "scrollZoom": True,
                "displaylogo": False,
                "modeBarButtonsToRemove": ["lasso2d", "select2d"],
                "modeBarButtons": [
                    ["toImage"],
                    ["zoomIn2d", "zoomOut2d", "autoScale2d", "zoom2d", "pan2d"],
                ],
            }
        )
        st.markdown("""
            <style>
            .js-plotly-plot .plotly .modebar {
                top: -40px !important;
                right: 30px !important;
                bottom: auto !important;
                transform: translateY(0) !important;
            }
                    .css-1jc7ptx, .e1ewe7hr3, .viewerBadge_container__1QSob,
    .styles_viewerBadge__1yB5_, .viewerBadge_link__1S137,
    .viewerBadge_text__1JaDK {
        display: none;
    }
                    
            </style>
            """, unsafe_allow_html=True)



    with st.expander("Study Data Table", expanded=False):
        symbols_data = (
            basemodel_to_df(st.session_state.rrg_data.symbols_data)
            .join(basemodel_to_df(st.session_state.rrg_data.benchmark_data)[st.session_state.rrg_data.benchmark])
        ).set_index("date")
        symbols_data.index = pd.to_datetime(symbols_data.index).strftime("%Y-%m-%d")
        st.dataframe(symbols_data)

    with st.expander("Relative Strength Ratio Table", expanded=False):
        ratios_data = basemodel_to_df(st.session_state.rrg_data.rs_ratios).set_index("date")
        ratios_data.index = pd.to_datetime(ratios_data.index).strftime("%Y-%m-%d")
        st.dataframe(ratios_data)

    with st.expander("Relative Strength Momentum Table", expanded=False):
        ratios_data = basemodel_to_df(st.session_state.rrg_data.rs_momentum).set_index("date")
        ratios_data.index = pd.to_datetime(ratios_data.index).strftime("%Y-%m-%d")
        st.dataframe(ratios_data)


# Add the developed by section
st.sidebar.markdown(
    """
    ---
    **Developed by Hello World Communications for Testing Purposes Only**
    """
)
