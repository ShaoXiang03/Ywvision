"""
Polymarket Markets Dashboard - Streamlit Application
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from src.clients.gamma import GammaClient
from src.core.parse import parse_market
from src.core.filters import filter_candidates
from src.core.select_focus import select_focus_markets


def main():
    st.set_page_config(
        page_title="Polymarket Markets Dashboard",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Polymarket Markets Dashboard")
    st.markdown("---")
    
    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ Controls")
        
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.subheader("Filter Settings")
        
        # Add debug mode
        debug_mode = st.checkbox("🐛 Debug Mode", value=False)
        
        # Add time filter slider
        max_hours = st.slider(
            "Max Hours to Close",
            min_value=24,
            max_value=720,  # 30 days
            value=168,  # Default 7 days
            step=24,
            help="Maximum hours until market closes"
        )
        
        st.info(f"候选市场过滤条件:\n\n"
                f"✅ enableOrderBook = true\n"
                f"✅ active = true & closed = false\n"
                f"✅ 0 < hours_to_close ≤ {max_hours}\n"
                f"✅ 有效的 YES/NO token IDs")
    
    # Fetch and process data
    with st.spinner("正在从 Polymarket API 拉取数据..."):
        markets_data = fetch_and_process_markets(debug_mode, max_hours)
    
    if not markets_data:
        st.error("❌ 未能获取市场数据，请检查网络连接或稍后重试")
        return
    
    all_markets = markets_data['all_markets']
    candidates = markets_data['candidates']
    focus_markets = markets_data['focus_markets']
    
    # Debug information
    if debug_mode:
        st.expander("🐛 Debug Info", expanded=True).write({
            "Total Markets Fetched": markets_data.get('total_fetched', 0),
            "Successfully Parsed": len(all_markets),
            "After Filter": len(candidates),
            "API Response": markets_data.get('api_status', 'Unknown')
        })
    
    # Display statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总市场数", len(all_markets))
    with col2:
        st.metric("候选市场", len(candidates))
    with col3:
        st.metric("Crypto 市场", "✅" if focus_markets['crypto'] else "❌")
    with col4:
        st.metric("Sports 市场", "✅" if focus_markets['sports'] else "❌")
    
    st.markdown("---")
    
    # Focus Markets Section
    st.header("🎯 Focus Markets (2 个市场)")
    st.markdown("*自动选择: 1 个 Crypto + 1 个 Sports，48 小时内关闭*")
    
    col1, col2 = st.columns(2)
    
    with col1:
        display_focus_market(focus_markets['crypto'], "Crypto", "🪙")
    
    with col2:
        display_focus_market(focus_markets['sports'], "Sports", "🏆")
    
    st.markdown("---")
    
    # Candidate Markets Section
    st.header("📋 候选市场列表")
    
    if len(candidates) == 0:
        st.warning("⚠️ 没有符合条件的市场")
        
        # Show why markets were filtered out
        if debug_mode and len(all_markets) > 0:
            with st.expander("查看被过滤的市场统计"):
                show_filter_stats(all_markets)
        
        return
    
    # Filter controls
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"**共 {len(candidates)} 个候选市场**")
    with col2:
        filter_invalid = st.checkbox("过滤无效价格", value=False)
    with col3:
        show_details = st.checkbox("显示详细列", value=False)
    
    # Filter markets by valid prices
    if filter_invalid:
        display_markets = [
            m for m in candidates 
            if m.yes_price is not None and m.no_price is not None
        ]
        st.info(f"✅ 过滤后: {len(display_markets)} 个市场（价格完整）")
    else:
        display_markets = candidates
    
    if not display_markets:
        st.warning("⚠️ 没有符合条件的市场")
        return
    
    # Convert to DataFrame for display
    df = markets_to_dataframe(display_markets, show_details)
    
    # Display table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "YES Price": st.column_config.NumberColumn(
                "YES Price",
                format="$%.3f"
            ),
            "NO Price": st.column_config.NumberColumn(
                "NO Price",
                format="$%.3f"
            ),
            "Hours to Close": st.column_config.NumberColumn(
                "Hours to Close",
                format="%.2f"
            )
        }
    )
    
    # Footer
    st.markdown("---")
    st.caption(f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
               f"数据源: Polymarket Gamma API")


@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_and_process_markets(debug_mode=False, max_hours=168):
    """Fetch and process markets from Gamma API"""
    client = GammaClient()
    
    # Fetch multiple pages
    all_markets = []
    total_fetched = 0
    api_status = "Success"
    
    try:
        for offset in range(0, 300, 100):  # Fetch 3 pages
            markets = client.get_markets(limit=100, offset=offset, closed=False)
            if not markets:
                break
            total_fetched += len(markets)
            all_markets.extend(markets)
        
        if total_fetched == 0:
            api_status = "No markets returned from API"
            
    except Exception as e:
        api_status = f"API Error: {str(e)}"
        print(f"Error fetching markets: {e}")
    
    # Parse markets
    parsed_markets = []
    for market in all_markets:
        parsed = parse_market(market)
        if parsed:
            parsed_markets.append(parsed)
    
    # Filter candidates with custom max_hours
    candidates = filter_candidates(parsed_markets, max_hours=max_hours)
    
    # Select focus markets (but use 48h filter for focus)
    focus_candidates = filter_candidates(parsed_markets, max_hours=48)
    focus_markets = select_focus_markets(focus_candidates)
    
    return {
        'all_markets': parsed_markets,
        'candidates': candidates,
        'focus_markets': focus_markets,
        'total_fetched': total_fetched,
        'api_status': api_status
    }


def show_filter_stats(all_markets):
    """Show statistics about why markets were filtered out"""
    stats = {
        "Total Markets": len(all_markets),
        "enableOrderBook = False": sum(1 for m in all_markets if not m.enableOrderBook),
        "active = False or closed = True": sum(1 for m in all_markets if not m.active or m.closed),
        "hours_to_close is None": sum(1 for m in all_markets if m.hours_to_close is None),
        "hours_to_close <= 0": sum(1 for m in all_markets if m.hours_to_close is not None and m.hours_to_close <= 0),
        "hours_to_close > 48": sum(1 for m in all_markets if m.hours_to_close is not None and m.hours_to_close > 48),
        "Missing YES/NO tokens": sum(1 for m in all_markets if not m.yes_token_id or not m.no_token_id),
        "Invalid (parse errors)": sum(1 for m in all_markets if m.invalid_reason is not None)
    }
    
    for key, value in stats.items():
        st.write(f"**{key}**: {value}")
    
    # Show sample of hours_to_close distribution
    st.markdown("**Hours to Close Distribution (sample):**")
    hours_list = [m.hours_to_close for m in all_markets[:20] if m.hours_to_close is not None]
    if hours_list:
        st.write(sorted(hours_list))


def display_focus_market(market, market_type, icon):
    """Display a focus market card"""
    if not market:
        st.warning(f"{icon} **{market_type} Market**\n\n"
                   f"未找到符合条件的 {market_type} 市场\n"
                   f"(48 小时内关闭)")
        return
    
    with st.container(border=True):
        st.subheader(f"{icon} {market_type} Market")
        
        st.markdown(f"**问题:** {market.question}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Hours to Close", f"{market.hours_to_close:.2f}h")
            st.metric("Category", market.category)
        with col2:
            yes_price = f"${market.yes_price:.3f}" if market.yes_price else "N/A"
            no_price = f"${market.no_price:.3f}" if market.no_price else "N/A"
            st.metric("YES Price", yes_price)
            st.metric("NO Price", no_price)
        
        if market.slug:
            st.caption(f"Slug: `{market.slug}`")


def markets_to_dataframe(markets, show_details=False):
    """Convert markets list to pandas DataFrame"""
    data = []
    for m in markets:
        row = {
            "Category": m.category or "N/A",
            "Question": m.question or "N/A",
            "End Date": m.endDate[:10] if m.endDate else "N/A",
            "Hours to Close": m.hours_to_close,
            "YES Price": m.yes_price,
            "NO Price": m.no_price,
        }
        
        if show_details:
            row.update({
                "Order Book": "✅" if m.enableOrderBook else "❌",
                "Active": "✅" if m.active else "❌",
                "Closed": "✅" if m.closed else "❌",
                "YES Token": m.yes_token_id[:8] + "..." if m.yes_token_id else "N/A",
                "NO Token": m.no_token_id[:8] + "..." if m.no_token_id else "N/A",
                "Slug": m.slug or "N/A"
            })
        
        data.append(row)
    
    return pd.DataFrame(data)


if __name__ == "__main__":
    main()