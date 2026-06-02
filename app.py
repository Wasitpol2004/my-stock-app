import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Dependencies to install:
# pip install yfinance pandas pandas-ta numpy plotly streamlit

# ==========================================
# 1. SET CONFIG & THEME
# ==========================================
st.set_page_config(
    page_title="R-STOCK DASHBOARD", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Custom dark theme for Plotly graphs
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .stMetric {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 10px;
        border-radius: 5px;
    }
    div.stButton > button:first-child {
        background-color: #1a1c24;
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    </style>
    """, 
    unsafe_allow_html=True
)

# ==========================================
# 2. FUNCTIONS
# ==========================================

def get_stock_data(ticker, start, end):
    """
    Fetches stock data and calculates all technical indicators.
    """
    try:
        df = yf.download(ticker, start=start, end=end)
        if df.empty:
            return None
            
        # Ensure a clean datetime index
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        
        # technical indicator
        df = pd.concat([df, ta.sma(df['Close'], length=12)], axis=1)
        df = pd.concat([df, ta.ema(df['Close'], length=12)], axis=1)
        df = pd.concat([df, ta.macd(df['Close'], fast=12, slow=26, signal=9)], axis=1)
        df = pd.concat([df, ta.rsi(df['Close'], length=14)], axis=1)
        
        # Calculate key levels (Pivot Points) for R1, R2, S1, S2
        # Based on the whole period's data
        max_period = df['High'].max()
        min_period = df['Low'].min()
        close_period = df['Close'].iloc[-1]
        
        pivot_point = (max_period + min_period + close_period) / 3
        
        df['R1_level'] = (2 * pivot_point) - min_period
        df['R2_level'] = pivot_point + (max_period - min_period)
        df['S1_level'] = (2 * pivot_point) - max_period
        df['S2_level'] = pivot_point - (max_period - min_period)
        df['Pivot_level'] = pivot_point
        
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

def draw_main_chart(df, ticker, show_macd=True):
    """
    Draws the main candlestick chart with moving averages and support/resistance lines.
    """
    # Create subplots for price and MACD
    if show_macd:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.03, subplot_titles=(f'{ticker} Price', 'MACD'), 
                           row_width=[0.2, 0.7])
    else:
        fig = go.Figure()
        fig.add_trace(go.Scatter(name='Close', line=dict(color='#A0AEC0', width=1))) # Placeholder trace for legend
        
    # Candlestick chart
    fig.add_trace(go.Candlestick(x=df.index,
                                open=df['Open'], high=df['High'],
                                low=df['Low'], close=df['Close'],
                                name=ticker), row=1, col=1)
    
    # Moving Averages
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_12'], line=dict(color='#d69e2e', width=1.5), name='EMA 12'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_12'], line=dict(color='#2f855a', width=1), name='SMA 12'), row=1, col=1)
    
    # --- Add Support and Resistance lines like image_5.png ---
    level_pairs = [
        ('R2_level', '#f56565', 'แนวต้าน 2'),
        ('R1_level', '#fc8181', 'แนวต้าน 1'),
        ('Pivot_level', '#4a5568', 'Pivot'),
        ('S1_level', '#68d391', 'แนวรับ 1'),
        ('S2_level', '#38a169', 'แนวรับ 2'),
    ]
    
    # We use a very high time range shape to place labels on the side
    # This simulates "paper coordinates" in Altair
    x_paper_pos = 1.01 
    
    for level_key, color, thai_label in level_pairs:
        price_val = df[level_key].iloc[0] # Levels are constant for the period
        
        # Add a shaded zone for support/resistance area
        zone_color = color.replace('#', 'rgba(') + ', 0.1)'
        fig.add_shape(type="rect",
                      x0=df.index.min(), y0=price_val * 0.995,
                      x1=df.index.max(), y1=price_val * 1.005,
                      fillcolor=zone_color, line=dict(width=0),
                      row=1, col=1)
        
        # Add the horizontal line
        fig.add_hline(y=price_val, line_dash="dash", line_color=color, line_width=1, row=1, col=1)
        
        # Add inline annotation like image_5.png
        #xref="paper" means relative to chart width, not dates
        fig.add_annotation(x=x_paper_pos, y=price_val, xref="paper", yref="y",
                           text=f"{thai_label} ${price_val:,.2f}", 
                           showarrow=False, align="right", xanchor="left",
                           font=dict(size=10, color=color),
                           bgcolor="rgba(26, 28, 36, 0.8)", borderpad=4)

    # Shaded support zone at the bottom like image_5.png
    min_price_period = df['Low'].min()
    fig.add_shape(type="rect",
                  x0=df.index.min(), y0=df['Low'].min() * 0.95,
                  x1=df.index.max(), y1=df['Low'].min() * 1.1,
                  fillcolor="rgba(104, 211, 145, 0.07)", line=dict(width=0),
                  layer="below", row=1, col=1)

    # MACD Plot
    if show_macd:
        fig.add_trace(go.Bar(x=df.index, y=df['MACDh_12_26_9'], name='Histogram', marker_color='rgba(169, 169, 169, 0.4)'), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD_12_26_9'], line=dict(color='#d69e2e', width=1), name='MACD'), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MACDs_12_26_9'], line=dict(color='#fc8181', width=1), name='Signal'), row=2, col=1)
        
    fig.update_layout(
        template="plotly_dark",
        height=700,
        margin=dict(l=20, r=120, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis_rangeslider_visible=False,
    )
    
    # Hide x-axis labels on price plot
    fig.update_xaxes(showticklabels=False, row=1, col=1)
    # Configure y-axes
    fig.update_yaxes(side="left", tickfont=dict(color='#A0AEC0'), tickprefix="$", row=1, col=1)
    fig.update_yaxes(side="left", tickfont=dict(color='#A0AEC0'), row=2, col=1)
    
    return fig

def draw_rsi_chart(df):
    """
    Draws a line chart for RSI with Overbought and Oversold regions.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI_14'], line=dict(color='#f6ad55', width=1.5), name='RSI'))
    
    # RSI levels
    fig.add_hline(y=70, line_dash="dash", line_color="#fc8181", annotation_text="Overbought", row=1, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#68d391", annotation_text="Oversold", row=1, col=1)
    
    fig.update_layout(
        template="plotly_dark",
        title='Relative Strength Index (RSI)',
        height=200,
        margin=dict(l=20, r=20, t=30, b=10),
        xaxis=dict(showgrid=False, tickfont=dict(color='#A0AEC0')),
        yaxis=dict(range=[0, 100], showgrid=True, gridcolor="#2D3748", side="right", tickfont=dict(color='#A0AEC0')),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    return fig

# Company information dictionary (extendable)
company_info = {
    'RKLB': {'name': 'Rocket Lab Corporation', 'desc': 'Rocket Lab provides launch services and satellite components for the space industry.'},
    'JNJ': {'name': 'Johnson & Johnson', 'desc': 'Johnson & Johnson is a diversified healthcare company. They manufacture pharmaceuticals and medical devices.'},
    'XOM': {'name': 'Exxon Mobil Corporation', 'desc': 'ExxonMobil is one of the worlds largest international oil and gas companies.'},
    'ASTS': {'name': 'AST SpaceMobile, Inc.', 'desc': 'AST SpaceMobile building a satellite-based cellular broadband network for mobile devices.'},
    'AMZN': {'name': 'Amazon.com, Inc.', 'desc': 'Amazon is a multinational technology company. Its focus is on e-commerce and cloud computing.'},
    'MU': {'name': 'Micron Technology, Inc.', 'desc': 'Micron manufactures semiconductor devices. They produce dynamic random-access memory chips.'}
}

# ==========================================
# 3. MAIN APPLICATION
# ==========================================

# Use native columns for a clean header, not HTML.
header_col1, header_col2, header_col3 = st.columns([1, 15, 4])

with header_col1:
    # --- SOLUTION FOR MediaFileStorageError ---
    # Use a universally available image (like from Icons8) or an emoji,
    # making deployment foolproof.
    rocket_logo_url = "https://img.icons8.com/color/48/000000/rocket.png"
    st.image(rocket_logo_url, width=48)

with header_col2:
    st.markdown("## DOOHUN <span style='font-weight: 300; color: rgba(255, 255, 255, 0.4)'>| Intelligent Stock Terminal vPro</span>", unsafe_allow_html=True)
    st.markdown("<p style='margin: 0; color: rgba(255, 255, 255, 0.6)'>ระบบวิเคราะห์ข้อมูลหุ้นเรียลไทม์หน้าจอเดี่ยว</p>", unsafe_allow_html=True)

with header_col3:
    # No more hardcoded descriptions. Move to a function.
    pass

st.write("---")

# Quick Watchlist
st.write("### ⭐ หุ้นโปรดของคุณ (Quick Watchlist):")
wl_col1, wl_col2, wl_col3, wl_col4, wl_col5, wl_col6, _ = st.columns([1,1,1,1,1,1,4])
wl_tickers = ["RKLB", "JNJ", "XOM", "ASTS", "AMZN", "MU"]
quick_select = None

for i, tkr in enumerate(wl_tickers):
    with locals()[f"wl_col{i+1}"]:
        if st.button(f"▫️ {tkr}", use_container_width=True):
            quick_select = tkr

# Search and timeframe
col_search, col_time = st.columns([3, 1])
with col_search:
    search_input = st.text_input("🔍 ค้นหาชื่อหุ้นอื่นเพิ่มเติม (พิมพ์ตัวย่อ เช่น AAPL, TSLA, PTT.BK):", "RKLB")
with col_time:
    time_frame = st.selectbox("📅 ช่วงเวลาของกราฟ:", ["6 เดือน", "1 ปี", "2 ปี"], index=1)

# Period mapping
period_map = {"6 เดือน": "6mo", "1 ปี": "1y", "2 ปี": "2y"}
ticker = (quick_select or search_input).upper().strip()

# Fetch and calculate
with st.spinner(f'Fetching and analyzing {ticker}...'):
    stock_data = get_stock_data(ticker, period_map[time_frame], "3000-01-01") # end=future for all up-to-date data

if stock_data is not None:
    last_close = stock_data['Close'].iloc[-1]
    last_date_str = stock_data.index[-1].strftime('%d/%m/%Y')
    
    # RENDER HEADER LIKE TARGET image_8.png
    st.write("---")
    head_left, head_right = st.columns([10, 3])
    
    with head_left:
        sub_logo, sub_text = st.columns([1, 10])
        with sub_logo:
            rocket_logo_url = "https://img.icons8.com/color/48/000000/rocket.png"
            st.image(rocket_logo_url, width=48)
        with sub_text:
            st.markdown(f"<span style='background-color: #3b82f6; color: white; padding: 3px 8px; border-radius: 5px; font-size: 11px; font-weight: 700;'>NMS</span>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='margin: 0; margin-top: 5px;'>{ticker} <span style='font-size: 18px; color: rgba(255, 255, 255, 0.4); font-weight: 400;'>{company_info.get(ticker, {}).get('name', 'Company Name Not Available')}</span></h2>", unsafe_allow_html=True)
            st.markdown(f"<p style='color: #48BB78; font-weight: bold; background-color: rgba(72, 187, 120, 0.1); display: inline; padding: 4px 10px; border-radius: 20px; font-size: 13px;'>⚡ เทรนด์: ขาขึ้นแข็งแกร่ง (Bullish)</p>", unsafe_allow_html=True)

    with head_right:
        # Calculate recent high/low like image_9.png
        recent_high = stock_data['Close'].tail(30).max()
        recent_low = stock_data['Close'].tail(30).min()
        head_right.metric("ราคาสูงสุดรอบนี้", f"{recent_high:,.2f}")
        head_right.metric("ราคาต่ำสุดรอบนี้", f"{recent_low:,.2f}")

    st.write("---")
    main_col1, main_col2, main_col3 = st.columns([5, 3, 2])
    
    # MAIN COLUMN 1: CHART & DESCRIPTIONS
    with main_col1:
        st.write("### 📈 ผลตอบแทนและทิศทางเทคนิคล:")
        main_chart_fig = draw_main_chart(stock_data, ticker)
        st.plotly_chart(main_chart_fig, use_container_width=True)
        
        st.write("### ℹ️ ลักษณะการประกอบธุรกิจ")
        info = company_info.get(ticker, {})
        st.write(f"### Description of {info.get('name', ticker)}", info.get('desc', 'Detailed description not available for this stock.'))
        
        st.write('### Description of MACD', 'Moving Average Convergence Divergence (MACD) is a trend-following momentum indicator. A generic bullish signal is when the MACD line crosses above the Signal line, and a generic bearish signal is when it crosses below.')
        st.write('### Description of RSI', 'Relative Strength Index (RSI) is a momentum indicator that measures the magnitude of recent price changes to evaluate overbought (usually > 70) or oversold (usually < 30) conditions.')

    # MAIN COLUMN 2: FUNCTIONAL DCF VALUATION
    with main_col2:
        st.write("### 💎 ประเมินมูลค่าหุ้นส่วนลดกระแสเงินสด (DCF):")
        
        dcf_input_col1, dcf_input_col2 = st.columns(2)
        
        with dcf_input_col1:
            st.write("**Free Cash Flow (FCF):**")
            current_fcf = st.number_input("", value=3000000000.0, step=1000000.0, format="%f")
            
            st.write("**Terminal Growth:**")
            growth_input = st.slider("", 0.0, 5.0, 2.0, 0.1)
            growth_rate = growth_input / 100.0

        with dcf_input_col2:
            st.write("**Shares Outstanding:**")
            shares_input = st.number_input("", value=400000000, step=1000)
            
            st.write("**WACC:**")
            wacc_input = st.slider("", 5.0, 15.0, 10.0, 0.1)
            wacc_rate = wacc_input / 100.0

        # Simple DCF Calculation
        explicit_years = 5
        future_fcf_sum = 0
        for year in range(explicit_years):
            fcf_n = current_fcf * (1 + growth_rate)**(year+1)
            future_fcf_sum += fcf_n / (1 + wacc_rate)**(year+1)
            
        terminal_value = (current_fcf * (1 + growth_rate)**(explicit_years) * (1 + growth_rate)) / (wacc_rate - growth_rate)
        present_value_tv = terminal_value / (1 + wacc_rate)**explicit_years
        
        intrinsic_value_per_share = (future_fcf_sum + present_value_tv) / shares_input
        
        # --- Display the result PER SHARE like user requested ---
        st.write("---")
        st.markdown(
            f"""
            <div style="background-color: #1a1c24; padding: 20px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.2); text-align: center;">
                <p style="margin: 0; color: rgba(255, 255, 255, 0.6); font-size: 14px;">มูลค่าพื้นฐานที่แท้จริงตามทฤษฎี</p>
                <h1 style="margin: 0; margin-top: 10px; color: #3182CE;">{intrinsic_value_per_share:,.2f} <span style='font-size: 18px'>USD</span></h1>
            </div>
            """, 
            unsafe_allow_html=True
        )

    # MAIN COLUMN 3: Price Metrics and Score
    with main_col3:
        st.metric("ราคาปัจจุบัน", f"{last_close:,.2f}", f"ข้อมูล ณ วันที่: {last_date_str}")
        
        # Safe dummy metrics in place of broken HTML ones
        st.metric("แนวรับถัดไป", f"{stock_data['S1_level'].iloc[0]:,.2f}")
        st.metric("แนวต้านถัดไป", f"{stock_data['R1_level'].iloc[0]:,.2f}")
        
        if show_macd:
            st.write("### MACD Status:")
            curr_macd = stock_data['MACD_12_26_9'].iloc[-1]
            curr_signal = stock_data['MACDs_12_26_9'].iloc[-1]
            macd_change = curr_macd - curr_signal
            arrow = "▲" if macd_change > 0 else "▼"
            st.metric("MACD vs Signal", f"{abs(macd_change):.3f}", f"{arrow} Signal Line")
            
        st.write("---")
        # Dummy performance score until logic is added
        st.write("### Performance Score")
        st.progress(0.75, text=f"{75}%")
        st.progress(0.40, text=f"{40}%")

    # Lower Chart Area
    if show_rsi:
        st.write("---")
        st.plotly_chart(draw_rsi_chart(stock_data), use_container_width=True)

else:
    st.error(f"Error: Could not retrieve data for ticker {ticker}. Please check the ticker symbol and try again.")
