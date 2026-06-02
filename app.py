import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import datetime
import base64

# กำหนดค่าหน้าหลักของระบบ (ต้องอยู่ด้านบนสุดของไฟล์เสมอ)
st.set_page_config(
    page_title="R-STOCK DASHBOARD", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# =========================================================================
# BASE64 ENCODED LOGO (ฝังรหัสโลโก้ใหม่ในตัวโค้ด หมดปัญหาภาพไม่ขึ้น 100%)
# =========================================================================
LOGO_BASE64 = """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"""

# =========================================================================
# FUNCTIONS (ฟังก์ชันการคำนวณ)
# =========================================================================
def calculate_moving_averages(data):
    """คำนวณเส้นค่าเฉลี่ยเคลื่อนที่ (EMA)"""
    data['EMA_12'] = data['Close'].ewm(span=12, adjust=False).mean()
    data['EMA_26'] = data['Close'].ewm(span=26, adjust=False).mean()
    return data

def calculate_macd(data):
    """คำนวณอินดิเคเตอร์ MACD"""
    if 'EMA_12' not in data.columns or 'EMA_26' not in data.columns:
        data = calculate_moving_averages(data)
    data['MACD_Line'] = data['EMA_12'] - data['EMA_26']
    data['Signal_Line'] = data['MACD_Line'].ewm(span=9, adjust=False).mean()
    data['MACD_Histogram'] = data['MACD_Line'] - data['Signal_Line']
    return data

def calculate_rsi(data, period=14):
    """คำนวณอินดิเคเตอร์ RSI"""
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    # หลีกเลี่ยงการหารด้วยศูนย์
    loss = loss.replace(0, np.nan)
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    data['RSI'] = rsi.fillna(50)  # แทนค่าเริ่มต้นด้วย 50 หากไม่มีข้อมูลเพียงพอ
    return data

# =========================================================================
# HEADER CONTROL (ส่วนแสดงผลหัวเว็บไซต์และโลโก้)
# =========================================================================
col_logo, col_title = st.columns([1.2, 12])
with col_logo:
    try:
        # แปลงข้อมูล Base64 กลับเป็นรูปภาพและนำไปแสดงผล
        logo_bytes = base64.b64decode(LOGO_BASE64)
        st.image(logo_bytes, width=75)
    except:
        # กรณีฉุกเฉินหากโค้ดมีปัญหา จะแสดงเป็นอิโมจิแทน
        st.markdown("<h2 style='margin:0; text-align:center;'>📊</h2>", unsafe_allow_html=True)

with col_title:
    st.markdown("""
        <h1 style='margin:0; padding-top:5px; font-family:Kanit, sans-serif; color:#FFFFFF; font-size:28px;'>
            R-STOCK FINANCIAL DASHBOARD
        </h1>
        <p style='margin:0; color:#A0AEC0; font-size:14px;'>ระบบวิเคราะห์ข้อมูลหุ้นเชิงเทคนิคระดับมืออาชีพ</p>
    """, unsafe_allow_html=True)

st.markdown("---")

# =========================================================================
# SIDEBAR CONTROL (ส่วนควบคุมเมนูด้านซ้าย)
# =========================================================================
st.sidebar.markdown("### 🔍 ตั้งค่าการค้นหา")
ticker_input = st.sidebar.text_input("สัญลักษณ์หุ้น (เช่น PTT.BK, AAPL, TSLA):", "PTT.BK").upper()

st.sidebar.markdown("### 📅 ช่วงเวลาที่ต้องการวิเคราะห์")
start_date = st.sidebar.date_input("วันที่เริ่มต้น:", datetime.date.today() - datetime.timedelta(days=365))
end_date = st.sidebar.date_input("วันที่สิ้นสุด:", datetime.date.today())

st.sidebar.markdown("### 📈 เลือกอินดิเคเตอร์ที่ต้องการดู")
show_macd = st.sidebar.checkbox("MACD (Trend & Momentum)", True)
show_rsi = st.sidebar.checkbox("RSI (Overbought / Oversold)", True)

# =========================================================================
# DATA FETCHING (ดึงข้อมูลจาก yfinance)
# =========================================================================
@st.cache_data(ttl=3600)  # แคชข้อมูลไว้ 1 ชั่วโมงเพื่อความรวดเร็ว
def load_stock_data(ticker, start, end):
    try:
        df = yf.download(ticker, start=start, end=end)
        if df.empty:
            return None
        # จัดการ Multi-index Columns ของ yfinance ให้เป็น Single-index
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return None

with st.spinner('กำลังดึงข้อมูลและคำนวณดัชนีทางเทคนิค...'):
    stock_data = load_stock_data(ticker_input, start_date, end_date)

# =========================================================================
# MAIN APP DISPLAY (ส่วนแสดงผลหลัก)
# =========================================================================
if stock_data is not None and len(stock_data) > 0:
    # คำนวณอินดิเคเตอร์ต่าง ๆ ลงใน DataFrame
    stock_data = calculate_moving_averages(stock_data)
    stock_data = calculate_macd(stock_data)
    stock_data = calculate_rsi(stock_data)
    
    # 1. ส่วนสรุปราคาปัจจุบัน (Metrics)
    last_row = stock_data.iloc[-1]
    prev_row = stock_data.iloc[-2] if len(stock_data) > 1 else last_row
    
    current_price = float(last_row['Close'])
    prev_price = float(prev_row['Close'])
    price_change = current_price - prev_price
    price_change_pct = (price_change / prev_price) * 100
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("ราคาปิดล่าสุด", f"{current_price:,.2f}", f"{price_change:+.2f} ({price_change_pct:+.2f}%)")
    with col2:
        st.metric("ราคาสูงสุดรอบนี้", f"{stock_data['High'].max():,.2f}")
    with col3:
        st.metric("ราคาต่ำสุดรอบนี้", f"{stock_data['Low'].min():,.2f}")
    with col4:
        st.metric("ปริมาณซื้อขายล่าสุด", f"{int(last_row['Volume']):,}")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 2. กราฟราคาหลัก (Candlestick + EMA)
    fig_price = go.Figure()
    
    # เพิ่มกราฟแท่งเทียน
    fig_price.add_trace(go.Candlestick(
        x=stock_data.index,
        open=stock_data['Open'],
        high=stock_data['High'],
        low=stock_data['Low'],
        close=stock_data['Close'],
        name="ราคาหุ้น"
    ))
    
    # เพิ่มเส้น EMA
    fig_price.add_trace(go.Scatter(x=stock_data.index, y=stock_data['EMA_12'], mode='lines', name='EMA 12 (ระยะสั้น)', line=dict(color='#00E676', width=1.5)))
    fig_price.add_trace(go.Scatter(x=stock_data.index, y=stock_data['EMA_26'], mode='lines', name='EMA 26 (ระยะกลาง)', line=dict(color='#FF1744', width=1.5)))
    
    fig_price.update_layout(
        title=f"วิเคราะห์แนวโน้มราคาหุ้น {ticker_input}",
        yaxis_title="ราคา",
        xaxis_title="วันที่",
        template="plotly_dark",
        height=450,
        xaxis_rangeslider_visible=False
    )
    st.plotly_chart(fig_price, use_container_width=True)
    
    # 3. กrayฟ MACD
    if show_macd:
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(x=stock_data.index, y=stock_data['MACD_Line'], mode='lines', name='MACD Line', line=dict(color='#29B6F6', width=1.5)))
        fig_macd.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Signal_Line'], mode='lines', name='Signal Line', line=dict(color='#FFA726', width=1.5)))
        
        # แท่ง Histogram สีเขียว/แดงตามแรงซื้อแรงขาย
        colors = ['#66BB6A' if val >= 0 else '#EF5350' for val in stock_data['MACD_Histogram']]
        fig_macd.add_trace(go.Bar(x=stock_data.index, y=stock_data['MACD_Histogram'], name='Histogram', marker_color=colors, opacity=0.7))
        
        fig_macd.update_layout(
            title="MACD (Moving Average Convergence Divergence)",
            yaxis_title="ค่าดัชนี",
            template="plotly_dark",
            height=250
        )
        st.plotly_chart(fig_macd, use_container_width=True)
        
    # 4. กราฟ RSI
    if show_rsi:
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=stock_data.index, y=stock_data['RSI'], mode='lines', name='RSI', line=dict(color='#E040FB', width=2)))
        
        # เส้น Overbought & Oversold
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="#FF5252", annotation_text="Overbought (70)")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="#69F0AE", annotation_text="Oversold (30)")
        
        fig_rsi.update_layout(
            title="RSI (Relative Strength Index)",
            yaxis_title="เปอร์เซ็นต์ (%)",
            yaxis=dict(range=[0, 100]),
            template="plotly_dark",
            height=220
        )
        st.plotly_chart(fig_rsi, use_container_width=True)
        
    # 5. แสดงตารางข้อมูลดิบด้านล่างสุด
    with st.expander("📊 ดูข้อมูลราคาหุ้นในรูปแบบตาราง (Raw Data)"):
        st.dataframe(stock_data[['Open', 'High', 'Low', 'Close', 'Volume']].sort_index(ascending=False), use_container_width=True)

else:
    st.error(f"❌ ไม่พบข้อมูลสำหรับสัญลักษณ์หุ้น '{ticker_input}' โปรดตรวจสอบว่าพิมพ์สัญลักษณ์หุ้นถูกต้อง หรือระบบของ Yahoo Finance พร้อมใช้งานในขณะนี้")
