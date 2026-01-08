"""
Polymarket Markets Dashboard - Polished Streamlit Application
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from src.clients.gamma import GammaClient
from src.clients.clob import ClobClient
from src.core.parse import parse_market
from src.core.filters import filter_candidates, is_crypto_market, is_sports_market
from src.core.select_focus import select_focus_markets


def main():
    st.set_page_config(
        page_title="Polymarket Markets Dashboard",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Polymarket Markets Dashboard")
    st.markdown("Real-time binary YES/NO markets with CLOB best ask prices")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Controls")
        
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.subheader("Filter Settings")
        
        debug_mode = st.checkbox("🐛 Debug Mode", value=False)
        
        max_hours = st.slider(
            "Max Hours to Close",
            min_value=24,
            max_value=720,
            value=48,  
            step=24,
            help="Candidate markets must close within this window"
        )
        
        st.info(
            "候选市场过滤条件:\n\n"
            "✅ enableOrderBook = true\n"
            "✅ active = true & closed = false\n"
            "✅ 0 < hours_to_close ≤ selected hours\n"
            "✅ valid binary YES/NO tokens\n\n"
            "Prices from CLOB API (best ask); fallback to Gamma if unavailable."
        )
    
    # Data pipeline
    with st.spinner("Fetching & processing Polymarket data..."):
        markets_data = fetch_and_process_markets(debug_mode, max_hours)
    
    if not markets_data:
        st.error("❌ Failed to fetch market data. Please try again later.")
        return
    
    all_markets = markets_data["all_markets"]
    candidates = markets_data["candidates"]
    focus_markets = markets_data["focus_markets"]
    
    # Debug info
    if debug_mode:
        with st.expander("🐛 Debug Information", expanded=False):
            st.json({
                "Total markets fetched": markets_data["total_fetched"],
                "Parsed successfully": len(all_markets),
                "Candidates (≤ selected hours)": len(candidates),
                "Focus crypto": bool(focus_markets["crypto"]),
                "Focus sports": bool(focus_markets["sports"]),
            })
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("总市场数", markets_data["total_fetched"])
    col2.metric("候选市场", len(candidates))
    col3.metric("Crypto 焦点市场", "✅" if focus_markets["crypto"] else "❌")
    col4.metric("Sports 焦点市场", "✅" if focus_markets["sports"] else "❌")
    
    st.markdown("---")
    
    # Focus Markets (2)
    st.header("🎯 Focus Markets (1 Crypto + 1 Sports)")
    st.markdown("*Selected from markets closing within **48 hours** (fallback to next available if none)*")
    
    col1, col2 = st.columns(2)
    with col1:
        display_focus_market(focus_markets["crypto"], "Crypto", "🪙")
    with col2:
        display_focus_market(focus_markets["sports"], "Sports", "🏆")
    
    st.markdown("---")
    
    # Candidate table
    st.header("📋 候选市场列表")
    
    if len(candidates) == 0:
        st.warning(
            "⚠️ 当前没有符合条件的候选市场（≤ {} 小时关闭）。\n\n"
            "这在某些日期是正常的——试试增加滑块时间范围，或稍后刷新。".format(max_hours)
        )
        return
    
    # Price filter toggle
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.write(f"**共 {len(candidates)} 个候选市场**")
    with col2:
        if "filter_prices" not in st.session_state:
            st.session_state.filter_prices = False
        if st.button("Filter Valid Prices", use_container_width=True):
            st.session_state.filter_prices = not st.session_state.filter_prices
    with col3:
        show_details = st.checkbox("详细列", value=False)
    
    display_markets = candidates
    if st.session_state.filter_prices:
        display_markets = [m for m in candidates if m.yes_price and m.no_price]
        st.info(f"Filtered → {len(display_markets)} markets with complete prices")
    
    df = markets_to_dataframe(display_markets, show_details=show_details)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "YES Price": st.column_config.NumberColumn("YES Price", format="$%.3f"),
            "NO Price": st.column_config.NumberColumn("NO Price", format="$%.3f"),
            "Hours to Close": st.column_config.NumberColumn("Hours to Close", format="%.2f h"),
        }
    )
    
    # Footer
    st.markdown("---")
    st.caption(
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        "Data: Polymarket Gamma API + CLOB API"
    )


@st.cache_data(ttl=300)
def fetch_and_process_markets(debug_mode: bool, max_hours: int):
    client = GammaClient()
    
    # Full pagination
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
    
    # Parse
    parsed_markets = [parse_market(m) for m in raw_markets if parse_market(m)]
    
    # Candidates for selected time window
    candidates = filter_candidates(parsed_markets, max_hours=max_hours)
    
    # CLOB prices (batch)
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
    
    # Focus selection – strict 48h, fallback to 168h if empty
    focus_candidates = filter_candidates(parsed_markets, max_hours=48)
    focus_markets = select_focus_markets(focus_candidates)
    
    if focus_markets["crypto"] is None and focus_markets["sports"] is None:
        # Fallback
        fallback_candidates = filter_candidates(parsed_markets, max_hours=168)
        focus_markets = select_focus_markets(fallback_candidates)
    
    return {
        "all_markets": parsed_markets,
        "candidates": candidates,
        "focus_markets": focus_markets,
        "total_fetched": len(raw_markets),
    }


def display_focus_market(market, label: str, icon: str):
    if not market:
        st.warning(f"{icon} **{label} Market**\n\nNo qualifying market found within 48 hours.")
        return
    
    with st.container(border=True):
        st.subheader(f"{icon} {label} Market")
        st.markdown(f"**{market.question}**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Hours to Close", f"{market.hours_to_close:.2f} h")
            st.metric("Category", market.category or "Inferred")
        with col2:
            yes = f"${market.yes_price:.3f}" if market.yes_price is not None else "N/A"
            no = f"${market.no_price:.3f}" if market.no_price is not None else "N/A"
            st.metric("YES Price", yes)
            st.metric("NO Price", no)
        
        if market.slug:
            st.caption(f"Slug: `{market.slug}`")


def markets_to_dataframe(markets, show_details: bool = False):
    data = []
    for m in markets:
        # Inferred category display
        cat = m.category or "N/A"
        if cat == "N/A":
            if is_crypto_market(m):
                cat = "Crypto"
            elif is_sports_market(m):
                cat = "Sports"
        
        row = {
            "Category": cat,
            "Question": m.question or "N/A",
            "End Date": m.endDate[:10] if m.endDate else "N/A",
            "Hours to Close": m.hours_to_close,
            "YES Price": m.yes_price,
            "NO Price": m.no_price,
            "Slug": m.slug or "N/A",
        }
        
        if show_details:
            row.update({
                "Order Book": "✅" if m.enableOrderBook else "❌",
                "Active": "✅" if m.active else "❌",
                "Closed": "✅" if m.closed else "❌",
                "YES Token": m.yes_token_id[:10] + "..." if m.yes_token_id else "N/A",
                "NO Token": m.no_token_id[:10] + "..." if m.no_token_id else "N/A",
            })
        
        data.append(row)
    
    return pd.DataFrame(data)


if __name__ == "__main__":
    main()