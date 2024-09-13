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

# Import the module
module = import_from_file("module", "relative_rotation.py")

# Define sector ETFs and their components
sector_etfs = {
    "XLB": ["AMCR", "MOS", "FCX", "SW", "IP", "DOW", "NEM", "CTVA", "FMC", "BALL", "CF", "DD", "ALB", "LYB", "EMN", "IFF", "STLD", "CE", "PPG", "NUE", "PKG", "AVY", "VMC", "ECL", "APD", "SHW", "MLM"],
    "XLC": ["ATVI", "CHTR", "CMCSA", "DIS", "EA", "FB", "GOOG", "GOOGL", "NFLX", "TMUS", "TTWO", "TWTR", "VZ"],
    "XLE": ["CVX", "XOM", "COP", "EOG", "SLB", "PXD", "VLO", "PSX", "MPC", "OXY", "KMI", "WMB", "HAL", "DVN", "BKR", "HES", "FANG", "APA", "MRO", "CTRA"],
    "XLF": ["JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "SCHW", "USB", "AXP", "PNC", "TFC", "COF", "BK", "SPGI", "CME", "CB", "MMC", "AON", "MET"],
    "XLI": ["HON", "UNP", "UPS", "BA", "CAT", "GE", "MMM", "LMT", "RTX", "DE", "FDX", "EMR", "ETN", "NSC", "WM", "ITW", "CSX", "GD", "ROK", "LHX"],
    "XLK": ["AAPL", "MSFT", "NVDA", "V", "MA", "AVGO", "CSCO", "ACN", "ADBE", "CRM", "INTC", "QCOM", "TXN", "ORCL", "IBM", "AMD", "PYPL", "INTU", "NOW", "ADI"],
    "XLP": ["PG", "KO", "PEP", "WMT", "COST", "PM", "MO", "EL", "CL", "KMB", "KHC", "GIS", "SYY", "STZ", "KR", "HSY", "TSN", "CAG", "CHD", "K"],
    "XHB": ["LEN", "DHI", "PHM", "NVR", "TOL", "KBH", "TPH", "MDC", "MHO", "LGIH", "TMHC", "CCS", "MTH", "BZH", "HOV", "GRBK", "SKY", "CVCO", "MHK", "LEG"],
    "XLU": ["NEE", "DUK", "SO", "D", "AEP", "SRE", "EXC", "XEL", "WEC", "ES", "ED", "PEG", "AWK", "EIX", "DTE", "FE", "AEE", "CMS", "ETR", "AES"],
    "XLV": ["UNH", "JNJ", "PFE", "ABT", "MRK", "TMO", "ABBV", "DHR", "BMY", "LLY", "AMGN", "MDT", "ISRG", "CVS", "GILD", "SYK", "VRTX", "ZTS", "BDX", "BSX"],
    "XLY": ["AMZN", "TSLA", "HD", "MCD", "NKE", "LOW", "SBUX", "TJX", "TGT", "BKNG", "F", "GM", "MAR", "ROST", "HLT", "YUM", "DG", "DPZ", "ORLY", "CMG"],
    "XLRE": ["PLD", "AMT", "CCI", "EQIX", "PSA", "O", "WELL", "SPG", "SBAC", "DLR", "VICI", "AVB", "EQR", "WY", "ARE", "VTR", "EXR", "MAA", "UDR", "BXP"]
}

# Sidebar configuration
st.sidebar.markdown(
    """
<style>
section[data-testid="stSidebar"] {
    top: 1% !important;
    height: 98.25% !important;
    left: 0.33% !important;
    margin-top: 0 !important;
}
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
</style>
""",
    unsafe_allow_html=True,
)

st.sidebar.header("Relative Rotation Graph")

# Sidebar inputs
with st.sidebar:
    source_input = st.selectbox("Data Source", ["Yahoo Finance", "Cboe"], index=0, key="source")
    benchmark_input = st.text_input("Benchmark", value="SPY", key="benchmark")
    date_input = st.date_input("Target End Date", value=datetime.today(), key="date_input")
    study_input = st.selectbox("Study", ["Price", "Volume", "Volatility"], key="study")
    
    if study_input == "Volatility":
        st.sidebar.header("Volatility Annualization")
        window_input = st.number_input("Rolling Window", min_value=0, value=21, key="window")
        trading_periods_input = st.number_input("Periods Per Year", min_value=0, value=252, key="trading_periods")

    st.sidebar.header("Long/Short Momentum Periods")
    long_period_input = st.number_input("Long Period", min_value=0, value=252, key="long_period")
    short_period_input = st.number_input("Short Period", min_value=0, value=21, key="short_period")

    show_tails_input = st.checkbox("Show Tails", value=False, key="show_tails")
    tail_periods_input = st.number_input("Tail Periods", min_value=0, value=30, key="tail_periods")
    tail_interval_input = st.selectbox("Tail Interval", ["Week", "Month"], key="tail_interval", index=0)

# Create tabs
tabs = st.tabs(list(sector_etfs.keys()) + ["Custom 1", "Custom 2", "Custom 3"])

# Function to create RRG for a given set of symbols
def create_rrg(symbols, benchmark, study, date, long_period, short_period, window, trading_periods, tail_periods, tail_interval, source):
    try:
        rrg_data = asyncio.run(module.create(
            symbols=symbols,
            benchmark=benchmark,
            study=study,
            date=pd.to_datetime(date),
            long_period=long_period,
            short_period=short_period,
            window=window,
            trading_periods=trading_periods,
            tail_periods=tail_periods,
            tail_interval=tail_interval,
            provider=source,
        ))
        return rrg_data
    except Exception as e:
        st.error(f"Error creating RRG: {str(e)}")
        return None

# Function to display RRG
def display_rrg(rrg_data, show_tails, tail_periods, tail_interval):
    if rrg_data is not None:
        fig = rrg_data.show(show_tails=show_tails, tail_periods=tail_periods, tail_interval=tail_interval, external=True)
        fig.update_layout(height=600, margin=dict(l=0, r=20, b=0, t=50, pad=0))
        st.plotly_chart(
            fig,
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

# Process each tab
for i, tab in enumerate(tabs):
    with tab:
        if i < 12:  # Sector ETF tabs
            etf = list(sector_etfs.keys())[i]
            symbols = sector_etfs[etf]
            st.header(f"Relative Rotation Graph for {etf}")
        else:  # Custom tabs
            st.header(f"Custom Relative Rotation Graph {i-11}")
            symbols_input = st.text_input("Enter up to 20 symbols (comma-separated)", key=f"custom_symbols_{i}")
            symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()][:20]
        
        if st.button("Generate RRG", key=f"generate_{i}"):
            rrg_data = create_rrg(
                symbols=symbols,
                benchmark=benchmark_input,
                study=study_input.lower(),
                date=date_input,
                long_period=long_period_input,
                short_period=short_period_input,
                window=window_input,
                trading_periods=trading_periods_input,
                tail_periods=tail_periods_input,
                tail_interval=tail_interval_input.lower(),
                source=source_input.lower().replace(" ", "")
            )
            display_rrg(rrg_data, show_tails_input, tail_periods_input, tail_interval_input.lower())

# Add the developed by section
st.sidebar.markdown(
    """
    ---
    **Developed by Hello World Communications for Testing Purposes Only**
    """
)
