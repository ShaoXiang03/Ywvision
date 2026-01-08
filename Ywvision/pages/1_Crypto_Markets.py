"""
Crypto Markets Page
"""
import streamlit as st
import pandas as pd

from src.clients.gamma import GammaClient
from src.clients.clob import ClobClient
from src.core.parse import parse_market
from src.core.filters import filter_candidates, is_crypto_market


st.set_page_config(page_title="Crypto Markets - Polymarket", page_icon="🪙")
st.title("🪙 Crypto Markets (closing ≤ 48 hours)")

with st.spinner("Fetching data..."):
    # === Same data pipeline as main page ===
    client = GammaClient()
    raw_markets = []
    offset = 0
    while True:
        batch = client.get_markets(limit=100, offset=offset, closed=False)
        if not batch:
            break
        raw_markets.extend(batch)
        if len(batch) < 100:
            break
        offset += len(batch)

    parsed = [parse_market(m) for m in raw_markets if parse_market(m)]
    candidates = filter_candidates(parsed, max_hours=48)

    # === CLOB prices (same as main page) ===
    clob = ClobClient()
    token_map = {}
    tokens = []
    for m in candidates:
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

    # === Filter only crypto ===
    crypto_markets = [m for m in candidates if is_crypto_market(m)]

st.write(f"**Found {len(crypto_markets)} crypto market(s) closing within 48 hours**")

if crypto_markets:
    df = pd.DataFrame([
        {
            "Question": m.question or "N/A",
            "Hours to Close": f"{m.hours_to_close:.2f}h" if m.hours_to_close else "N/A",
            "YES Price": f"${m.yes_price:.3f}" if m.yes_price is not None else "N/A",
            "NO Price": f"${m.no_price:.3f}" if m.no_price is not None else "N/A",
            "End Date": m.endDate[:10] if m.endDate else "N/A",
            "Slug": m.slug or "N/A",
        }
        for m in crypto_markets
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No crypto markets closing within the next 48 hours right now.")