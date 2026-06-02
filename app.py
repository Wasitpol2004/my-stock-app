import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==========================================
# 1. SET CONFIG & THEME
# ==========================================
st.set_page_config(
    page_title="DOOHUN - Stock Dashboard vPro", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# สไตล์ตกแต่งเพิ่มเติมสำหรับ Dark Mode
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    div.stButton > button {
        background-color: #1a1c24;
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    div.stButton > button:hover {
        border-color: #3b82f6;
        color: #3b82f6;
    }
    </style>
    """, 
    unsafe_allow_html=True
)

# ==========================================
# 2. FUNCTIONS
# ==========================================

# ฟังก์ชันแสดงโลโก้ส่วนหัวแอป (แก้บั๊ก MediaFileStorageError บน Cloud)
def display_app_logo(image_filename="logo.png", logo_width=60):
    try:
        # พยายามโหลดไฟล์รูปภาพปกติ
        st.image(image_filename, width=logo_width)
    except Exception:
        # Fallback UI: ในกรณีที่ไฟล์ภาพหายหรือ Path ผิดพลาดบน GitHub Cloud แอปจะไม่ล่ม
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 25px;">
                <span style="font-size: 32px;">📈</span>
                <span style="font-size: 24px; font-weight: bold; color: #ffffff; font-family: sans-serif; letter-spacing: 1px;">DOOHUN</span>
            </div>
            """, 
            unsafe_allow_html=True
        )

# ฟังก์ชันดึงข้อมูลหุ้นแบบปลอดภัย (แก้บั๊ก DataFrame MultiIndex, ราคา nan, SyntaxError)
@st.cache_data(ttl=3600)
def load_and_clean_stock_data(ticker, start, end):
    try:
        df = yf.download(ticker, start=start, end=end)
        
        if df.empty:
            return None
            
        # 🌟 Fix จุดที่ 3: แก้ปัญหา MultiIndex DataFrame จาก yfinance เวอร์ชันใหม่
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1) # ลบชื่อ Ticker ชั้นที่ 2 ออก ให้เหลือ Close, High, etc. ชั้นเดียว
            
        # 🌟 Fix จุดที่ 1: เคลียร์ค่า nan แถวสุดท้าย
        # ใช้ Forward Fill เติมค่าว่างด้วยค่าก่อนหน้า และลบแถวที่ยังเป็น NaN ที่เหลือออก
        df = df.ffill().dropna()
        
        # Ensure correct datetime index
        df.index = pd.to_datetime(df.index)
        
        # คำนวณอินดิเคเตอร์เชิงเทคนิคคอลพื้นฐาน
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['EMA50'] = ta.ema(df['Close'], length=50)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df.ta.macd(append=True)
        
        return df
    except Exception as e:
        # ใช้ st.write ในฟังก์ชันคำนวณแทนการใช้ try ครอบ st.write หลักเพื่อป้องกัน SyntaxError
        st.error(f"ไม่สามารถโหลดข้อมูลของหุ้น '{ticker}' ได้ในขณะนี้: {e}")
        return None

# Dictionary เก็บข้อมูลโบรกเกอร์ ( illustrative )
broker_target_data = {
    'RKLB': {'broker': 'Deutsche Bank', 'target': 15.00, 'recommend': 'BUY'},
    'JNJ': {'broker': 'Morgan Stanley', 'target': 185.00, 'recommend': 'OVERWEIGHT'},
    'XOM': {'broker': 'Goldman Sachs', 'target': 130.00, 'recommend': 'NEUTRAL'},
    'AMZN': {'broker': 'J.P. Morgan', 'target': 220.00, 'recommend': 'BUY'},
    'MU': {'broker': 'Citi', 'target': 175.00, 'recommend': 'BUY'},
    'ASTS': {'broker': ' illustrative', 'target': 10.00, 'recommend': ' illustrative'},
}

# Dictionary เก็บข้อมูลพื้นฐานบริษัทจำลอง ( illustrative )
company_info = {
    'RKLB': {'name': 'Rocket Lab USA, Inc.', 'desc': 'Rocket Lab provides launch services and satellite components for the space industry.'},
    'JNJ': {'name': 'Johnson & Johnson', 'desc': 'Johnson & Johnson is a diversified healthcare company. They manufacture pharmaceuticals and medical devices.'},
    'XOM': {'name': 'Exxon Mobil Corporation', 'desc': 'ExxonMobil is one of the worlds largest international oil and gas companies.'},
    'ASTS': {'name': 'AST SpaceMobile, Inc.', 'desc': 'AST SpaceMobile building a satellite-based cellular broadband network for mobile devices.'},
    'AMZN': {'name': 'Amazon.com, Inc.', 'desc': 'Amazon is a multinational technology company. Its focus is on e-commerce and cloud computing.'},
    'MU': {'name': 'Micron Technology, Inc.', 'desc': 'Micron manufactures semiconductor devices. They produce dynamic random-access memory chips.'}
}

# ==========================================
# 3. HTML DESIGN RENDERERS
# ==========================================

# ฟังก์ชันแสดงผลส่วนหัวข้อมูลหุ้นแบบ HTML (Fix บั๊ก HTML Leak รั่วเป็นตัวหนังสือ)
def render_modern_stock_header_card(ticker, full_name, current_price, change, change_percent, currency_unit, latest_date_str):
    text_color = "#48BB78" if change >= 0 else "#fc8181"
    arrow_icon = "▲" if change >= 0 else "▼"
    
    # 🌟 Fix จุดที่ 2: ใช้unsafe_allow_html=True เพื่อเรนเดอร์ HTML ให้ถูกต้อง
    st.markdown(
        f"""
        <div style="background-color: #1a1c24; border-radius: 8px; padding: 20px; border: 1px solid rgba(255, 255, 255, 0.1); font-family: sans-serif; margin-bottom: 25px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
                <div>
                    <span style="background-color: #3b82f6; color: white; padding: 3px 8px; border-radius: 5px; font-size: 11px; font-weight: 700;">STK</span>
                    <h2 style="margin: 4px 0 2px 0; color: #ffffff; font-size: 32px; font-weight: 700;">
                        {ticker} <span style="font-size: 18px; color: rgba(255, 255, 255, 0.4); font-weight: 400;">{full_name}</span>
                    </h2>
                    <p style="color: #48BB78; font-weight: bold; background-color: rgba(72, 187, 120, 0.1); display: inline; padding: 4px 10px; border-radius: 20px; font-size: 13px;">⚡ เทรนด์: ขาขึ้นแข็งแกร่ง (Bullish)</p>
                </div>
                
                <div style="text-align: right; min-width: 250px;">
                    <div style="font-size: 36px; font-weight: 800; color: #ffffff;">
                        {current_price:,.2f} <span style="font-size: 16px; color: rgba(255, 255, 255, 0.4); font-weight: 400;">{currency_unit}</span>
                    </div>
                    <div style="font-size: 16px; font-weight: 700; color: {text_color};">
                        {arrow_icon} {abs(change):,.2f} ({change_percent:+.2f}%)
                    </div>
                    <div style="color: rgba(255, 255, 255, 0.4); font-size: 11px; margin-top: 4px;">
                        อัปเดตล่าสุด: {latest_date_str} (Real-time data illustrative)
                    </div>
                </div>
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )

# ฟังก์ชันแสดงผลกล่องสรุปมูลค่าพื้นฐาน DCF ( illustrative, แสดงแค่ตัวเลขราคาเหมาะสมสุทธิ)
def render_dcf_valuation_summary_card(ticker, dcf_intrinsic_value, currency_unit):
    st.markdown(
        f"""
        <div style="background-color: #1a1c24; border-radius: 8px; padding: 22px; border: 1px solid rgba(255, 255, 255, 0.1); font-family: sans-serif; text-align: center;">
            <h4 style="margin: 0 0 15px 0; color: #ffffff; font-size: 15px; font-weight: 700;">
                💎 โมเดลประเมินมูลค่าหุ้นส่วนลดกระแสเงินสด (DCF Intrinsic Value)
            </h4>
            <div style="text-align: center; padding: 15px 0; background-color: rgba(255, 255, 255, 0.03); border-radius: 6px; border: 1px dashed rgba(255, 255, 255, 0.1); margin-bottom: 12px;">
                <div style="color: rgba(255, 255, 255, 0.5); font-size: 13px; margin-bottom: 4px;">มูลค่าพื้นฐานที่คำนวณได้สุทธิ</div>
                <div style="font-size: 34px; font-weight: 800; color: #3b82f6;">
                    {dcf_intrinsic_value:,.2f} <span style="font-size: 16px; font-weight: 400; color: rgba(255, 255, 255, 0.4);">{currency_unit}</span>
                </div>
            </div>
            <div style="font-size: 12px; color: #48BB78; font-weight: 600; padding: 6px; background-color: rgba(72, 187, 120, 0.05); border-radius: 4px;">
                ⚠️ ราคาปัจจุบันต่ำกว่ามูลค่าพื้นฐาน (Undervalued) ประมาณ 15.7% (Illustrative logic)
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )

# ==========================================
# 4. PLOTLY CHART FUNCTIONS (🌟 กราฟใหม่ดูง่าย สไตล์มืออาชีพ)
# ==========================================

# ฟังก์ชันสร้างกราฟ candlestick แบบง่าย มีเส้นแนวรับ-แนวต้านที่มีป้ายราคาติดอยู่ที่ขอบกราฟ
def create_technical_candlestick_chart(df, ticker):
    # ปรับแต่ง illustrative levels เพื่อใช้ในการวาดเส้นประตามภาพตัวอย่าง
    current_close = float(df['Close'].iloc[-1])
    recent_high = float(df['Close'].tail(30).max())
    recent_low = float(df['Close'].tail(30).min())
    
    # คำนวณ illustrative levels (ตัวเลขสมมติเพื่อแสดงผลรูปแบบกราฟ)
    res_2 = recent_high * 1.15
    res_1 = recent_high * 1.05
    sup_1 = current_close * 0.95
    sup_2 = current_close * 0.85
    
    fig = go.Figure()

    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        name='ราคาหุ้น',
        increasing_line_color='#23d386', increasing_fillcolor='#23d386',
        decreasing_line_color='#ff392e', decreasing_fillcolor='#ff392e',
        line_width=1.5,
    ))

    # เส้น EMA หลัก
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], mode='lines', line=dict(color='#A0AEC0', width=1.2), name='EMA20'))
    
    # 🌟 วาดเส้น illustrative levels และป้ายกำกับที่ขอบขวาของกราฟ
    levels = [
        {"val": res_2, "label": f"แนวต้าน 2 ${res_2:,.2f}", "color": "#fca5a5"},
        {"val": res_1, "label": f"แนวต้าน 1 ${res_1:,.2f}", "color": "#fc8181"},
        {"val": sup_1, "label": f"แนวรับ 1 ${sup_1:,.2f}", "color": "#68d391"},
        {"val": sup_2, "label": f"แนวรับ 2 ${sup_2:,.2f}", "color": "#4ade80"},
    ]
    
    for level in levels:
        # วาดเส้นประแนวนอน
        fig.add_hline(y=level["val"], line_dash="dash", line_color=level["color"], line_width=1)
        # แปะป้ายราคาที่ขอบขวาของกราฟ
        fig.add_annotation(
            x=1.005, y=level["val"],
            xref="paper", yref="y",
            text=level["label"],
            showarrow=False,
            xanchor="left",
            font=dict(size=11, color="#ffffff"),
            bgcolor=level["color"],
            bordercolor=level["color"],
            borderwidth=1,
            borderpad=3,
            style=f"background-color: {level['color']}; color: #111827; font-weight: bold; border-radius: 4px;"
        )

    # 🌟 วาด Shaded support zone พื้นหลังสีเขียวอ่อนด้านล่าง
    min_price_period = df['Low'].min()
    fig.add_shape(type="rect",
        x0=df.index.min(), y0=df['Low'].min() * 0.9,
        x1=df.index.max(), y1=df['Low'].min() * 1.02,
        fillcolor="rgba(104, 211, 145, 0.05)", line=dict(width=0),
        layer="below")

    # ปรับแต่งเลย์เอาต์กราฟแบบ Dark Mode
    fig.update_layout(
        template="plotly_dark",
        height=550,
        margin=dict(l=10, r=120, t=10, b=10),
        plot_bgcolor='#111319',
        paper_bgcolor='#111319',
        xaxis=dict(showgrid=True, gridcolor='#1e2229'),
        yaxis=dict(side="right", showgrid=True, gridcolor='#1e2229', tickfont=dict(color='#A0AEC0'), tickprefix="$"),
        xaxis_rangeslider_visible=False,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ฟังก์ชันสร้างกราฟ MACD Chart 2 ( illustrative )
def create_illustrative_macd_chart(df):
    fig = make_subplots(rows=1, cols=1)
    
    # MACD lines
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_12_26_9'], mode='lines', line=dict(color='#8b949e', width=1), name='MACD Line'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACDs_12_26_9'], mode='lines', line=dict(color='#fc8181', width=1), name='Signal Line'), row=1, col=1)
    
    # Histogram
    colors = ['#23d386' if val >= 0 else '#ff392e' for val in df['MACDh_12_26_9']]
    fig.add_trace(go.Bar(x=df.index, y=df['MACDh_12_26_9'], marker_color=colors, name='Histogram'), row=1, col=1)
    
    fig.update_layout(
        template="plotly_dark",
        height=180,
        margin=dict(l=10, r=120, t=10, b=10),
        plot_bgcolor='#111319',
        paper_bgcolor='#111319',
        xaxis=dict(showgrid=True, gridcolor='#1e2229'),
        yaxis=dict(side="right", showgrid=True, gridcolor='#1e2229', tickfont=dict(color='#A0AEC0')),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 5. MAIN EXECUTION LOOP
# ==========================================

def main():
    # เรียกใช้โลโก้ส่วนหัวแอปพลิเคชัน
    display_app_logo()
    
    # ส่วนของ Sidebar ฝั่งซ้าย
    st.sidebar.markdown("### 🔍 ค้นหาและตั้งค่า")
    search_input = st.sidebar.text_input("ค้นหาชื่อหุ้น (พิมพ์ตัวย่อ):", "RKLB")
    time_frame = st.sidebar.selectbox("📅 เลือกช่วงเวลา:", ["6 เดือน", "1 ปี", "2 ปี", "5 ปี"], index=1)

    # Watchlist buttons (illustrative)
    st.sidebar.write("⭐ หุ้นโปรดเข้าดูด่วน (Watchlist illustrative):")
    cols = st.sidebar.columns(2)
    with cols[0]:
        rklb_btn = st.button("🚀 RKLB")
        jnj_btn = st.button("💊
