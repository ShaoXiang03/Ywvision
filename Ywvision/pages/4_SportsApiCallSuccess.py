"""
Sports Markets Page - Raw Data Demo (Top 50, No Filtering)
"""
import streamlit as st
import pandas as pd

from src.clients.gamma import GammaClient


st.set_page_config(page_title="Sports Markets - Raw Demo", page_icon="⚽")
st.title("⚽ Raw Polymarket Markets - Top 50 (Proof of API Access)")

# Session state for full load (optional)
if "load_all_raw_sports" not in st.session_state:
    st.session_state.load_all_raw_sports = False

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("📥 Load All Raw Markets", use_container_width=True):
        st.session_state.load_all_raw_sports = True
        st.rerun()

with col2:
    mode = "ALL raw markets" if st.session_state.load_all_raw_sports else "first 50 raw markets"
    st.info(f"Showing {mode} – **no parsing or filtering applied**")

with st.spinner("Fetching raw data from Gamma API..."):
    client = GammaClient()
    raw_markets = []
    offset = 0

    # Fetch limit: 50 for fast demo, more for "Load All"
    target_count = 1000 if st.session_state.load_all_raw_sports else 50

    while len(raw_markets) < target_count:
        batch_size = min(100, target_count - len(raw_markets))
        batch = client.get_markets(limit=batch_size, offset=offset, closed=False)
        if not batch:
            break
        raw_markets.extend(batch)
        if len(batch) < 100:
            break
        offset += len(batch)

st.success(f"✅ Successfully fetched {len(raw_markets)} raw markets from Polymarket Gamma API")

if raw_markets:
    # Show only essential columns for clarity
    df = pd.DataFrame(raw_markets)
    display_cols = ["id", "slug", "question", "category", "endDate", "active", "closed", "enableOrderBook"]
    available_cols = [col for col in display_cols if col in df.columns]
    st.dataframe(df[available_cols], use_container_width=True, hide_index=True)

    # Optional: expandable raw JSON for debugging
    with st.expander("View full raw JSON (first 5 markets)"):
        for i, market in enumerate(raw_markets[:5]):
            st.json(market, expanded=False)
else:
    st.error("No data returned from API – check network or API status.")