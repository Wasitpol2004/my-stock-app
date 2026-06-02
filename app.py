import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import time  # สำหรับระบบหน่วงเวลาอัปเดตอัตโนมัติ
import google.generativeai as genai  # สำหรับเชื่อมต่อสมองกล AI ของจริง

# --- ตั้งค่าหน้าจอเปิดกว้างแบบสมดุล ---
st.set_page_config(layout="wide", page_title="DOOHUN - Stock Terminal & AI Advisor")

# --- ฟังก์ชันดึงข้อมูลหุ้นผ่านระบบ Cache (สำคัญมาก: ช่วยให้แอปทำงานไว และป้องกันโดนบล็อก IP ยามรีเฟรชถี่) ---
@st.cache_data(ttl=60)  # เก็บความจำข้อมูลไว้ 60 วินาทีต่อการดึง 1 ครั้ง
def load_stock_data(ticker, start, end):
    ticker_obj = yf.Ticker(ticker)
    return ticker_obj.history(start=start, end=end)

# --- ฟังก์ชันคำนวณอินดิเคเตอร์พื้นฐาน ---
def calculate_indicators(df):
    if df.empty: return df
    df = df.copy()
    
    # คำนวณ EMA 12 และ 26
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    
    # คำนวณ MACD
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['Hist'] = df['MACD'] - df['Signal']
    
    # คำนวณ RSI (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    return df

# --- ปรับแต่งสไตล์ CSS ให้เป็นธีม Dark Terminal ---
st.markdown("""
    <style>
        .stApp { background-color: #0e1117; }
        .stMetricValue { color: white !important; font-weight: bold; }
        .stMetricLabel { color: #8a99ad !important; }
        .term-badge { background-color: rgba(59, 130, 246, 0.15); color: #3b82f6; border-radius: 4px; padding: 3px 8px; font-weight: bold; font-size: 11px; }
        .term-badge-trend { background-color: rgba(16, 185, 129, 0.15); color: #10b981; border-radius: 4px; padding: 3px 8px; font-weight: bold; font-size: 11px; }
        .term-card { border: 1px solid #202632; padding: 20px; border-radius: 8px; background-color: #161b22; margin-bottom: 15px; }
        .undervalued { color: #4ade80; font-weight: bold; }
        .overvalued { color: #f87171; font-weight: bold; }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] { background-color: #161b22; border: 1px solid #202632; color: #8b949e; border-radius: 6px 6px 0px 0px; padding: 10px 20px; }
        .stTabs [data-baseweb="tab"]:hover { color: #3b82f6; }
        .stTabs [aria-selected="true"] { background-color: #1e2530 !important; color: white !important; border-bottom: 2px solid #3b82f6 !important; }
    </style>
""", unsafe_allow_html=True)

# --- ⚙️ แถบควบคุมด้านข้าง (Sidebar Controller) ---
with st.sidebar:
    st.markdown("### ⚙️ แผงควบคุมระบบอัจฉริยะ")
    st.write("---")
    
    # ช่องใส่คีย์สำหรับ AI จริง
    gemini_key = st.text_input(
        "🔑 ใส่ Gemini API Key ของคุณ:", 
        type="password", 
        placeholder="AIzaSy...",
        help="สามารถขอ API Key ใช้งานฟรีได้ที่ Google AI Studio"
    )
    
    st.write("---")
    # เมนูตั้งค่าเวลา Auto-Refresh ราคา
    refresh_options = {"ปิดการอัปเดตอัตโนมัติ": 0, "🔄 อัปเดตทุก 1 นาที": 60, "🔄 อัปเดตทุก 3 นาที": 180, "🔄 อัปเดตทุก 5 นาที": 300}
    refresh_choice = st.selectbox("⏱️ ตั้งเวลา Auto-Refresh หน้าจอ:", list(refresh_options.keys()), index=0)
    refresh_seconds = refresh_options[refresh_choice]

# --- ส่วนหัวโปรแกรม (Header) ---
head_col1, head_col2 = st.columns([1, 11])
with head_col1:
    try:
        st.image("logo.png", width=65)
    except:
        st.markdown("<h1 style='margin:0; padding-top:10px;'>🌕</h1>", unsafe_allow_html=True)
with head_col2:
    st.markdown("<h2 style='margin:0;'>DOOHUN <span style='font-weight:300; color:#6e7681;'>| มาดูหุ้นกัน By W_bxss</span></h2>", unsafe_allow_html=True)
    st.markdown("<p style='margin:0; color:#8b949e; font-size:14px;'>ทำกำไร และ To TheMoon🌕</p>", unsafe_allow_html=True)

st.write("---")

# --- คานรายการหุ้นโปรด (Quick Watchlist) ---
st.write("⭐ **หุ้นโปรดทีสนใจ**")
wl_cols = st.columns(6)
wl_tickers = ["RKLB", "JNJ", "XOM", "ASTS", "AMZN", "MU"]
clicked_ticker = None

for i, tkr in enumerate(wl_tickers):
    with wl_cols[i]:
        if st.button(f"▫️ {tkr}", use_container_width=True, key=f"btn_{tkr}"):
            clicked_ticker = tkr

# --- ช่องค้นหาเพิ่มเติม ---
search_input = st.text_input("🔍 พิมพ์ชื่อตัวย่อหุ้นที่ต้องการค้นหา (เช่น TSLA, AAPL, RKLB, PTT.BK):", "RKLB")
target_ticker = (clicked_ticker if clicked_ticker else search_input).upper().strip()

# ดึงข้อมูลย้อนหลัง 1 ปี (มิ.ย. 2025 - มิ.ย. 2026)
start_date = datetime.date(2025, 6, 2)
end_date = datetime.date(2026, 6, 2)

# --- สร้างระบบ Tabs แยกหน้าจอวิเคราะห์ และ หน้าจอคุยกับ AI ออกจากกันอย่างเป็นสัดส่วน ---
tab1, tab2 = st.tabs(["📈 หน้ากระดานวิเคราะห์หุ้น (Terminal Dashboard)", "🤖 บอทที่ปรึกษา AI จริง (AI Stock Advisor)"])

if target_ticker:
    try:
        # ดึงข้อมูลผ่านฟังก์ชันที่ครอบระบบคลังความจำ Cache ไว้
        raw_df = load_stock_data(target_ticker, start_date, end_date)
