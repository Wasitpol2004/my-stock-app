import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import numpy as np

# install requirements first: pip install yfinance pandas plotly streamlit numpy

# --- Initial Page Config for Dark Terminal Theme ---
st.set_page_config(layout="wide", page_title="DOOHUN - Stock Terminal")

# --- Remote Icons (to avoid MediaFileStorageError) ---
rocket_icon_url = "https://img.icons8.com/color/48/000000/rocket.png"
# Use default remote assets for deployed app robustness

# ==========================================
# --- Helper Functions (Indicator Calc without dependencies) ---
# ==========================================

# Clean yfinance messy multi-ticker column headers
def clean_yfinance_headers(df):
    if df.empty: return df
    # Fix for versions >= 0.2.x which create multi-index columns even for one ticker
    if len(df.columns.names) > 1:
        df.columns = df.columns.droplevel('Ticker')
    return df.sort_index()

# Manual Technical Indicators (keeps deployment simple without extra dependencies)
def calculate_basic_indicators(df):
    if df.empty: return df
    df = df.copy()

    # Sort to ensure Wilder's smoothing works
    df = df.sort_index()

    # EMA
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()

    # MACD
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['Hist'] = df['MACD'] - df['Signal']

    # RSI (Approximate Wilder's Smoothing for deployable script robustness)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    return df

# Helper to format percentages based on direction
def format_pct_change(change_pct):
    color = "undervalued" if change_pct >= 0 else "overvalued"
    sign = "+" if change_pct >= 0 else ""
    return f"<span class='{color}'>{sign}{change_pct:.2f}%</span>"

# ==========================================
# --- APP CSS (Dark Terminal Theme) ---
# ==========================================
st.markdown("""
    <style>
        .reportview-container { background: #1a1c24; }
        .sidebar .sidebar-content { background: #161a20; }
        .stMetricValue { color: white; }
        .stMetricLabel { color: #A0AEC0; }
        .stButton>button { background-color: #1a1c24; color: #A0AEC0; border: 1px solid #4a5568; }
        .stButton>button:hover { color: white; border: 1px solid white; }
        /* Style standard status badges and colors from terminal */
        .term-badge-global { background-color: rgba(59, 130, 246, 0.15); color: #3b82f6; border-radius: 4px; padding: 2px 8px; font-weight: bold; font-size: 11px;}
        .term-badge-trend { background-color: rgba(16, 185, 129, 0.15); color: #10b981; border-radius: 4px; padding: 2px 8px; font-weight: bold; font-size: 11px;}
        .term-title-panel { color: #A0AEC0; font-size: 13px; font-weight: bold;}
        .overvalued { color: #f87171; font-weight: bold; }
        .undervalued { color: #4ade80; font-weight: bold; }
        .term-border { border: 1px solid #2d3748; padding: 15px; border-radius: 8px; margin-bottom: 20px;}
        .term-price-big { font-size: 32px; font-weight: 800; color: white;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# --- HEADER REPLICATED ---
# ==========================================
head_col1, head_col2 = st.columns([1, 15])
with head_col1:
    st.image(rocket_icon_url, width=48)
with head_col2:
    st.markdown(f"## DOOHUN <span style='font-weight: 300; color: rgba(255, 255, 255, 0.4)'>| Intelligent Stock Terminal vPro</span>", unsafe_allow_html=True)
    st.markdown(f"<p style='margin: 0; color: rgba(255, 255, 255, 0.6)'>ระบบวิเคราะห์ข้อมูลหุ้นเทคนิคคอลและมูลค่าพื้นฐานแบบเรียลไทม์ (โหมดมืดสนิท)</p>", unsafe_allow_html=True)

st.write("---")

# ==========================================
# --- Quick Watchlist replicated ---
# ==========================================
st.write(f"### ⭐ หุ้นโปรดของคุณ (Quick Watchlist):")
wl_col1, wl_col2, wl_col3, wl_col4, wl_col5, wl_col6, _ = st.columns([1,1,1,1,1,1,4])
wl_tickers = ["RKLB", "JNJ", "XOM", "ASTS", "AMZN", "MU"]
quick_select_tkr = None

for idx, tkr in enumerate(wl_tickers):
    with locals()[f"wl_col{idx+1}"]:
        if st.button(f"▫️ {tkr}", use_container_width=True):
            quick_select_tkr = tkr

# --- Search Inputs ---
st.write("### 🔍 ค้นหาหุ้นสากลเพิ่มเติม")
search_input = st.text_input("สัญลักษณ์หุ้น (เช่น AAPL, TSLA, RKLB):", "RKLB").upper() # default from image

# Priority to button click, then search
ticker = (quick_select_tkr or search_input).upper().strip()

# Default period for images seemed to be 1 Year
start_date = datetime.date(2025, 6, 2)
end_date = datetime.date(2026, 6, 2)

# Sidebar left blank or with standard controls (no S/R sliders per user request)
st.sidebar.markdown("## ค้นหา/ตั้งค่า")
st.sidebar.markdown(f"**Symbol:** {ticker}")
st.sidebar.markdown(f"**Period:** {start_date} -> {end_date}")

# ==========================================
# --- Data Fetching logic ---
# ==========================================
if ticker:
    try:
        with st.spinner(f'Fetching data for {ticker}...'):
            raw_df = yf.download(ticker, start=start_date, end=end_date)
            if raw_df.empty:
                st.error(f"No data found for ticker '{ticker}'.")
                st.stop()

            # Fix messy columns (Fixes Type Error: float(...) nan problem)
            df_cleaned = clean_yfinance_headers(raw_df)
            # Calculate basics (Avoids ModuleNotFoundError from pandas_ta)
            df = calculate_basic_indicators(df_cleaned)

            # Important for chart robustness: ensure index is datetime
            df.index = pd.to_datetime(df.index)
            # Drip first 14 days due to RSI calculation
            df = df.dropna()

        # Handle failed TA calc after cleaning
        if df.empty or 'MACD' not in df.columns:
            st.error("Failed to calculate required technical indicators. Data structure might be complex.")
            st.stop()

        # ==========================================
        # --- App Main Components continued ---
        # ==========================================
        last_close = df['Close'].iloc[-1]
        prev_close = df['Close'].iloc[-2]
        change_pct = ((last_close - prev_close) / prev_close) * 100
        last_date = df.index[-1].strftime('%d/%m/%Y')

        # Dummy calculated S/R (simplified rolling min/max for period robustness)
        sr_period = 30 # days
        df['SR_rolling_min'] = df['Close'].rolling(sr_period).min()
        df['SR_rolling_max'] = df['Close'].rolling(sr_period).max()

        support1 = df['SR_rolling_min'].iloc[-1]
        support2 = df['SR_rolling_min'].iloc[-20] # illustrative logic
        resistance1 = df['SR_rolling_max'].iloc[-1]
        resistance2 = df['SR_rolling_max'].iloc[-20] # illustrative logic

        # --- Performance Metric Card ---
        with st.container():
            col_badges, col_price = st.columns([1, 12])
            with col_badges:
                 st.markdown(f"""
                    <div style="display:flex; flex-direction:column; gap:5px; margin-top:20px;">
                        <span class="term-badge-global">NMS</span>
                        <span class="term-badge-global">GLOBAL MARKET</span>
                    </div>
                 """, unsafe_allow_html=True)
            with col_price:
                 price_col1, price_col2 = st.columns([8, 3])
                 with price_col1:
                      st.markdown(f"## {ticker} <span style='color: #A0AEC0; font-weight: normal; font-size: 20px;'>{ticker} Corp (Dummy Desc needed per stock database)</span>", unsafe_allow_html=True)
                      # Illustrative Trend Badge based on last close vs EMA26
                      trend = "undervalued" if last_close > df['EMA26'].iloc[-1] else "overvalued"
                      trend_text = "⚡ เทรนด์: BULLISH" if trend == "undervalued" else "⚠️ เทรนด์: BEARISH"
                      st.markdown(f"<span class='term-badge-trend'>{trend_text}</span>", unsafe_allow_html=True)
                 with price_col2:
                      change_formatted = format_pct_change(change_pct)
                      st.markdown(f"""
                        <div style="text-align: right;">
                             <span class="term-price-big">${last_close:,.2f}</span><span style="color:#A0AEC0"> USD</span><br>
                             <span>({change_formatted}) ข้อมูล ณ วันที่: {last_date}</span>
                        </div>
                      """, unsafe_allow_html=True)

        st.write("---")

        main_col1, main_col2, main_col3 = st.columns([3, 1, 1], gap="medium")

        # ==========================================
        # --- LEFT PANEL: ADVANCED CHART REPLICATED ---
        # ==========================================
        with main_col1:
            st.markdown(f"<span class='term-title-panel'>📊 ประสิทธิภาพราคาและการเติบโต (Price Performance)</span>", unsafe_allow_html=True)

            # subplots: Candlestick, MACD, RSI (Replicating Image 21 logic)
            # Adjust row widths for complex layout robustness on deploy
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                                vertical_spacing=0.02,
                                row_width=[0.2, 0.2, 0.6]) # [Bottom row height, middle, top]

            # 1. Candlestick (replicating chart type of 21/23)
            # If user has missing t-30-3.jpg, and deployed it to streamlit cloud, app will crash.
            # Using remote assets ensures deployment robustness.
            fig.add_trace(go.Candlestick(x=df.index,
                            open=df['Open'],
                            high=df['High'],
                            low=df['Low'],
                            close=df['Close'],
                            name="Price", showlegend=False), row=1, col=1)

            # 2. Add EMAs (replicating Image 21 type chart)
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA12'], name='EMA 12',
                                     line=dict(color='#d69e2e', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA26'], name='EMA 26',
                                     line=dict(color='#48BB78', width=1)), row=1, col=1)

            # --- S/R Lines + Inline Labels in THAI (from Image 23 style request) ---
            levels = [
                {'y': resistance2, 'c': '#f87171', 'thai_label': 'แนวต้าน 2'},
                {'y': resistance1, 'c': '#fc8181', 'thai_label': 'แนวต้าน 1'},
                {'y': support1, 'c': '#68d391', 'thai_label': 'แนวรับ 1'},
                {'y': support2, 'c': '#38a169', 'thai_label': 'แนวรับ 2'},
            ]

            # In line labels with prices added on right paper coordinate (using high paper pos to push to end of chart)
            paper_pos_x = 1.01

            for level in levels:
                # Add horizontal dashed lines
                fig.add_hline(y=level['y'], line_dash="dash", line_color=level['c'], line_width=1, row=1, col=1)
                # Add annotations with labels like Image 23 request
                fig.add_annotation(x=paper_pos_x, y=level['y'], xref="paper", yref="y",
                                   text=f"{level['thai_label']} ${level['y']:,.2f}",
                                   showarrow=False, xanchor="left",
                                   font=dict(size=10, color=level['c']),
                                   bgcolor="rgba(26, 28, 36, 0.8)", borderpad=4)

            # Shaded Support zone dummy replicated from image 23 bottom left area
            # We use shapes for shaded area
            min_y_chart = df['Low'].rolling(sr_period).min().iloc[-1] * 0.95
            if min_y_chart > 0:
                fig.add_shape(type="rect", xref="paper", yref="y",
                              x0=0, y0=0, x1=1, y1=min_y_chart,
                              fillcolor="rgba(104, 211, 145, 0.05)", line=dict(width=0), row=1, col=1)

            # 3. MACD chart
            fig.add_trace(go.Bar(x=df.index, y=df['Hist'], name='Histogram', marker_color='#a0aec0', opacity=0.4, showlegend=False), row=2, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='#d69e2e', width=1.5), showlegend=False), row=2, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['Signal'], name='Signal', line=dict(color='#f87171', width=1), showlegend=False), row=2, col=1)

            # 4. RSI Chart
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='#f6ad55', width=1), showlegend=False), row=3, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="#fc8181", row=3, col=1, line_width=1)
            fig.add_hline(y=30, line_dash="dash", line_color="#68d391", row=3, col=1, line_width=1)

            # Theme Layout (dark terminal robustness)
            fig.update_layout(
                template="plotly_dark",
                height=700,
                xaxis_rangeslider_visible=False,
                margin=dict(l=20, r=120, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color='#A0AEC0', size=11)),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis3_title="วันที่",
            )
            fig.update_xaxes(showticklabels=False, row=1, col=1) # Hide ticklabels on subplots
            fig.update_xaxes(showticklabels=False, row=2, col=1)
            fig.update_yaxes(side="left", tickfont=dict(color='#A0AEC0'), tickprefix="$", row=1, col=1)
            fig.update_yaxes(side="left", tickfont=dict(color='#A0AEC0'), row=2, col=1)
            fig.update_yaxes(range=[0, 100], showgrid=True, gridcolor="#2D3748", side="right", tickfont=dict(color='#A0AEC0'), row=3, col=1) # RHS RSI

            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        # ==========================================
        # --- MIDDLE PANEL: Business and NEW DCF ---
        # ==========================================
        with main_col2:
            st.markdown(f"<span class='term-title-panel'>ℹ️ ลักษณะการประกอบธุรกิจ (Business Description)</span>", unsafe_allow_html=True)
            # Description from Image 4
            st.write(f"### Description of {ticker} Corp (AST dummy desc needed per stock DB)")
            st.write("Description placeholder per Image 22/24 logic needed per specific stock.")

            st.write("---")

            # **NEW MODIFIED DCF PANEL per Image 24 style request**
            # User wants DCF to look like number inputs in image 11 (Image 24).
            # This is illustrative as full fundamental scraping is complex.
            st.markdown(f"<span class='term-title-panel'>💎 มูลค่าตามหลักทฤษฎี (DCF Fair Value)</span>", unsafe_allow_html=True)

            # New static values to replace old DCF panel sliders
            fcf_val_str = "45,000,000" if ticker == "RKLB" else "Dummy FCF"
            wacc_str = "8.5%" if ticker == "RKLB" else "Dummy WACC"
            growth_str = "12%" if ticker == "RKLB" else "Dummy Growth"

            # Replicating the simple display card from Image 22 target design request
            intrinsic_dummy = 19.07 if ticker == "RKLB" else 99.99
            underVal_overVal = " undervaled" if intrinsic_dummy > last_close else " overvalued"

            st.markdown(f"""
                <div class="term-border" style="background-color: #1a1c24;">
                     <p style="margin:0; font-size: 13px; color: #A0AEC0;">
                         Theoretically Calculated Intrinsic Value
                     </p>
                     <h1 style="color: #63b3ed; font-size: 32px; font-weight: 800;">
                         {intrinsic_dummy:,.2f} <span style="font-size: 14px; font-weight: normal; color:#A0AEC0">USD</span>
                     </h1>
                     <p style="margin: 0; color: rgba(255, 255, 255, 0.4); font-size: 11px">
                        Based illustrative static DCF assumptions for this demo.<br>
                        FCF illustrative: {fcf_val_str}, Growth 5yr approx: {growth_str}. WACC illustrative: {wacc_str}.
                     </p>
                </div>
            """, unsafe_allow_html=True)

        # ==========================================
        # --- RIGHT PANEL: Price Metrics replicated from Image 22/24 ---
        # ==========================================
        with main_col3:
            st.markdown(f"<span class='term-title-panel'>🎯 กรอบราคาที่เหมาะสมจากโบรกเกอร์ ( Broker Targets)</span>", unsafe_allow_html=True)
            # Replicating Image 22 structure

            # PricePerformance (placeholder with illustrative dummy data per stock needed)
            st.metric(label="✅ ราคาประเมินเป้าหมายโบรกเกอร์ (Broker Targets)", value="$18.50 USD", delta="Based illustr description needed per stock")
            st.write("Placeholder desc per stock needed.")

            st.markdown("<hr style='margin:10px 0; border-color:#2D3748'/>", unsafe_allow_html=True)

            # Replicating bottom sections (illustrative placeholder values needed)
            st.write("---")
            perf_score_dummy = 0.88 # 8.8 from image 22 but normalized/normalized dummy needed
            
            st.write(f"### Performance Score (Dummy illustrative value needed)")
            st.write("R-Stock Dummy illustrative value description logic needed per stock. Performance value needed.")
            st.progress(perf_score_dummy, text="Based illustr description needed per stock")


    except Exception as e:
        # Final deployment crash robustness: handle failed TA (e.g. TypeError from messy yfinance nan headers)
        st.error(f"Error during technical analysis. App crashed per image error logic request. Error details: {e}")

else:
    st.info("Please select or search for a stock ticker to begin analyzing.")
