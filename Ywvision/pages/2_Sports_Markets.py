"""
Sports Markets Page - Fast Load with Optional Full Fetch
"""
import streamlit as st
import pandas as pd

from src.clients.gamma import GammaClient
from src.clients.clob import ClobClient
from src.core.parse import parse_market
from src.core.filters import filter_candidates, is_sports_market


st.set_page_config(page_title="Sports Markets - Polymarket", page_icon="⚽")
st.title("⚽ Sports Markets (closing ≤ 48 hours)")

# Button to load full data
if "load_all_sports" not in st.session_state:
    st.session_state.load_all_sports = False

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("📥 Load All Sports Markets", use_container_width=True):
        st.session_state.load_all_sports = True
        st.rerun()

with col2:
    limit_note = "Showing first 50 markets (fast load)" if not st.session_state.load_all_sports else "Showing ALL qualifying markets"
    st.info(limit_note)

with st.spinner("Fetching data..."):
    client = GammaClient()
    raw_markets = []
    offset = 0
    max_markets = 500 if st.session_state.load_all_sports else 300
    
    while len(raw_markets) < max_markets:
        remaining = max_markets - len(raw_markets)
        limit = min(100, remaining)
        batch = client.get_markets(limit=limit, offset=offset, closed=False)
        if not batch:
            break
        raw_markets.extend(batch)
        if len(batch) < 100:
            break
        offset += len(batch)

    parsed = [parse_market(m) for m in raw_markets if parse_market(m)]
    candidates_48h = filter_candidates(parsed, max_hours=48)

    # Apply sports filter
    sports_markets = [m for m in candidates_48h if is_sports_market(m)]

    # Limit to first 50 if not loading all
    if not st.session_state.load_all_sports and len(sports_markets) > 50:
        sports_markets = sports_markets[:50]

    # CLOB prices
    clob = ClobClient()
    token_map = {}
    tokens = []
    for m in sports_markets:
        if m.yes_token_id:
            tokens.append(m.yes_token_id)
            token_map[m.yes_token_id] = (m, "yes")
        if m.no_token_id:
            tokens.append(m.no_token_id)
            token_map[m.no_token_id] = (m, "no")

    if tokens:
        prices = clob.get_prices(list(set(tokens)), side="buy")
        for token, price in prices.items():
            if token in token_map:
                market, side = token_map[token]
                if side == "yes":
                    market.yes_price = price
                else:
                    market.no_price = price

st.write(f"**Found {len(sports_markets)} sports market(s) closing within 48 hours**")

if sports_markets:
    df = pd.DataFrame([
        {
            "Question": m.question or "N/A",
            "Hours to Close": f"{m.hours_to_close:.2f}h" if m.hours_to_close else "N/A",
            "YES Price": f"${m.yes_price:.3f}" if m.yes_price is not None else "N/A",
            "NO Price": f"${m.no_price:.3f}" if m.no_price is not None else "N/A",
            "End Date": m.endDate[:10] if m.endDate else "N/A",
            "Slug": m.slug or "N/A",
        }
        for m in sports_markets
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No sports markets closing within the next 48 hours right now.")