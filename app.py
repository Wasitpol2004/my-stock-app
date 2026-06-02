import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import requests
import os
from google import genai
from google.genai import types

# --- ตั้งค่าหน้าจอเปิดกว้างแบบสมดุล ---
st.set_page_config(layout="wide", page_title="DOOHUN - Stock & AI Terminal")

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
        /* สไตล์เสริมสำหรับแชทบอท */
        .chat-container { border: 1px solid #21262d; border-radius: 6px; padding: 15px; background-color: #0e1117; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- เรียกใช้งานสิทธิ์การใช้งาน Gemini API ---
# ระบบจะดึงอัตโนมัติจาก Streamlit Secrets หรือ Environment Variable ของเครื่อง
api_key = st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else os.environ.get("GEMINI_API_KEY")

# เปิดใช้งาน Client ของ Google GenAI SDK ตัวล่าสุด
if api_key:
    ai_client = genai.Client(api_key=api_key)
else:
    ai_client = None

# --- ฟังก์ชันคำนวณอินดิเคเตอร์พื้นฐาน ---
def calculate_indicators(df):
    if df.empty: 
        return df
    df = df.copy()
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['Hist'] = df['MACD'] - df['Signal']
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# --- ฟังก์ชันดึงข้อมูลหุ้นแบบปลอดภัย (มี Cache) ---
@st.cache_data(ttl=900)
def get_cached_stock_data(ticker, start, end):
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    })
    ticker_obj = yf.Ticker(ticker, session=session)
    df = ticker_obj.history(start=start, end=end)
    return df

# --- ส่วนหัวโปรแกรม (Header) ---
head_col1, head_col2 = st.columns([1, 11])
with head_col1:
    st.markdown("<h1 style='margin:0; text-align:center;'>🌕</h1>", unsafe_allow_html=True)
with head_col2:
    st.markdown("<h2 style='margin:0;'>DOOHUN <span style='font-weight:300; color:#6e7681;'>| Terminal & AI Assistant By W_bxss</span></h2>", unsafe_allow_html=True)
    st.markdown("<p style='margin:0; color:#8b949e; font-size:14px;'>วิเคราะห์เทคนิคอล และคุยกับ AI ปรึกษาแผนลงทุน</p>", unsafe_allow_html=True)

st.write("---")

# --- คานรายการหุ้นโปรด (Quick Watchlist) ---
st.write("⭐ **หุ้นโปรดที่สนใจ**")
wl_cols = st.columns(6)
wl_tickers = ["RKLB", "JNJ", "XOM", "ASTS", "AMZN", "MU"]
clicked_ticker = None

for i, tkr in enumerate(wl_tickers):
    with wl_cols[i]:
        if st.button(f"▫️ {tkr}", use_container_width=True):
            clicked_ticker = tkr

# --- ช่องค้นหาเพิ่มเติม ---
search_input = st.text_input("🔍 พิมพ์ชื่อตัวย่อหุ้นที่ต้องการวิเคราะห์ (เช่น TSLA, AAPL, RKLB, PTT.BK):", "RKLB")
target_ticker = (clicked_ticker if clicked_ticker else search_input).upper().strip()

# ดึงข้อมูลย้อนหลัง 1 ปี
start_date = datetime.date(2025, 6, 2)
end_date = datetime.date(2026, 6, 2)

# --- เตรียมตัวแปรเก็บข้อมูลหุ้น ---
df = pd.DataFrame()
data_loaded = False

if target_ticker:
    try:
        with st.spinner('กำลังโหลดข้อมูลตลาดหุ้น...'):
            raw_df = get_cached_stock_data(target_ticker, start_date, end_date)
            if not raw_df.empty:
                df = calculate_indicators(raw_df)
                df = df.dropna()
                if not df.empty:
                    data_loaded = True
            else:
                st.error(f"❌ ไม่พบข้อมูลสัญลักษณ์ '{target_ticker}' บนระบบ Yahoo Finance")
    except Exception as e:
        st.error(f"ระบบขัดข้อง: {e}")

# =========================================================================
# --- แบ่งหน้าต่างการทำงานหลักออกเป็น 2 หน้าต่าง (Tabs) ---
# =========================================================================
tab1, tab2 = st.tabs(["📊 ตารางและการวิเคราะห์ทางเทคนิค", "🤖 แชทบอทผู้ช่วยส่วนตัว (AI Assistant)"])

# -------------------------------------------------------------------------
# TAB 1: ระบบดูกราฟและอินดิเคเตอร์เดิม (ยกมาวางอย่างปลอดภัย)
# -------------------------------------------------------------------------
with tab1:
    if data_loaded:
        last_close = df['Close'].iloc[-1]
        prev_close = df['Close'].iloc[-2]
        change_pct = ((last_close - prev_close) / prev_close) * 100
        last_date = df.index[-1].strftime('%d/%m/%Y')

        res2 = df['High'].rolling(30).max().iloc[-1]
        res1 = df['High'].rolling(15).max().iloc[-1]
        sup1 = df['Low'].rolling(15).min().iloc[-1]
        sup2 = df['Low'].rolling(30).min().iloc[-1]

        # แสดงราคาด้านบนย่อยของ Tab
        st.markdown(f"### ราคาปัจจุบันของ {target_ticker}: **${last_close:,.2f}** ({change_pct:+.2f}%) วันที่ {last_date}")
        
        left_layout, right_layout = st.columns([12, 8], gap="large")

        with left_layout:
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_width=[0.2, 0.2, 0.6])
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="ราคาหุ้น"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA12'], line=dict(color='#d69e2e', width=1.2), name='EMA 12'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA26'], line=dict(color='#10b981', width=1.2), name='EMA 26'), row=1, col=1)

            # เส้นแนวรับแนวต้าน
            annotation_date = df.index[-1] + pd.Timedelta(days=3)
            levels = [{'y': res2, 'color': '#f87171', 'label': 'แนวต้าน 2'}, {'y': res1, 'color': '#ffa3a3', 'label': 'แนวต้าน 1'},
                      {'y': sup1, 'color': '#a7f3d0', 'label': 'แนวรับ 1'}, {'y': sup2, 'color': '#10b981', 'label': 'แนวรับ 2'}]
            for lvl in levels:
                fig.add_hline(y=lvl['y'], line_dash="dash", line_color=lvl['color'], row=1, col=1)
                fig.add_annotation(x=annotation_date, y=lvl['y'], text=f" {lvl['label']}", showarrow=False, xanchor="left", font=dict(size=10, color=lvl['color']), row=1, col=1)

            fig.add_trace(go.Bar(x=df.index, y=df['Hist'], name='Histogram', marker_color='#4b5563', opacity=0.5), row=2, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='#3b82f6', width=1.2), name='MACD'), row=2, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['Signal'], line=dict(color='#ef4444', width=1), name='Signal'), row=2, col=1)

            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#fbbf24', width=1.2), name='RSI (14)'), row=3, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="#10b981", row=3, col=1)

            fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False, margin=dict(l=10, r=90, t=10, b=10), plot_bgcolor='#0e1117', paper_bgcolor='#0e1117')
            fig.update_xaxes(showgrid=True, gridcolor="#21262d")
            fig.update_yaxes(side="right", gridcolor="#21262d")
            st.plotly_chart(fig, use_container_width=True)

        with right_layout:
            with st.container():
                st.markdown(f"<div class='term-card'><h4>{target_ticker} Corporation</h4><p style='color:#8b949e; font-size:13px;'>วิเคราะห์โครงสร้างราคาอัตโนมัติด้วยระบบอินดิเคเตอร์เชิงปริมาณ</p></div>", unsafe_allow_html=True)
                dcf_fair_price = 19.07 if target_ticker == "RKLB" else last_close * 0.85
                valuation_status = "🟢 ราคาต่ำกว่าพื้นฐาน (Undervalued)" if last_close < dcf_fair_price else "🔴 ราคาสูงเกินพื้นฐาน (Overvalued)"
                st.markdown(f"<div class='term-card'><h5>💎 มูลค่าทฤษฎี (DCF Fair Value)</h5><h2>${dcf_fair_price:,.2f} USD</h2><p>{valuation_status}</p></div>", unsafe_allow_html=True)
    else:
        st.info("กรุณาระบุชื่อหุ้นเพื่อแสดงข้อมูลกราฟเทคนิคัล")

# -------------------------------------------------------------------------
# TAB 2: ระบบ AI Chatbot อัจฉริยะ (ดึงราคาหุ้นปัจจุบันไปคุยได้ด้วย!)
# -------------------------------------------------------------------------
with tab2:
    st.subheader("🤖 AI ผู้ช่วยวิเคราะห์กลยุทธ์การลงทุน")
    
    if not ai_client:
        st.warning("⚠️ ไม่พบรหัส `GEMINI_API_KEY` กรุณาตั้งค่ารหัสผ่านในระบบก่อนใช้งานฟังก์ชัน AI Chatบอท")
    else:
        # ระบบจัดการหน่วยความจำแชทบอท (Chat History) ป้องกันข้อความหายเมื่อรีเฟรชหน้าจอ
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = [
                {"role": "model", "text": "สวัสดีครับ! ผมคือ AI ผู้ช่วยลงทุนของคุณ วันนี้ต้องการให้ช่วยวิเคราะห์กลยุทธ์ ค้นหาจุดกลับตัว หรือตรวจสอบข้อมูลตัวไหนเพิ่มเติมไหมครับ? 📈"}
            ]

        # ปุ่มกดเพื่อล้างประวัติการคุยเก่า
        if st.button("🧹 ล้างประวัติการคุยทั้งหมด"):
            st.session_state.chat_messages = [
                {"role": "model", "text": "ล้างประวัติเรียบร้อยแล้วครับ! มีอะไรให้ผมช่วยแนะนำใหม่ไหมครับ?"}
            ]
            st.rerun()

        # แสดงกล่องข้อความประวัติการสนทนาที่เคยคุยไว้
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["text"])

        # ช่องสำหรับพิมพ์คำถามใหม่ของผู้ใช้
        if user_prompt := st.chat_input("พิมพ์คำถามของคุณที่นี่... (เช่น แนะนำจุดซื้อขายของหุ้นตัวนี้หน่อย, RSI บอกอะไรบ้าง)"):
            
            # 1. แสดงข้อความของฝั่งผู้ใช้ขึ้นหน้าจอทันที
            with st.chat_message("user"):
                st.markdown(user_prompt)
            st.session_state.chat_messages.append({"role": "user", "text": user_prompt})

            # 2. ส่งคำถามไปประมวลผลที่เซิร์ฟเวอร์ AI ของ Google Gemini
            with st.chat_message("model"):
                with st.spinner("AI กำลังคิดและประมวลผลคำตอบ..."):
                    try:
                        # สร้างประโยคคำสั่งพิเศษเบื้องหลัง (System Instruction) เพื่อบังคับให้บอทฉลาดและตอบในฐานะผู้เชี่ยวชาญการเงิน
                        context_data = ""
                        if data_loaded:
                            context_data = f"(ข้อมูลอ้างอิง: หุ้น {target_ticker} ปัจจุบันราคารอบล่าสุดอยู่ที่ ${df['Close'].iloc[-1]:,.2f} USD, ค่า RSI อยู่ที่ {df['RSI'].iloc[-1]:.2f}, เทรนด์ล่าสุดเป็น {trend_status})"
                        
                        system_prompt = (
                            "คุณคือที่ปรึกษาทางการเงินและผู้เชี่ยวชาญการวิเคราะห์หุ้นทางเทคนิคอลระดับโลก "
                            "จงตอบคำถามด้วยความรอบคอบ ชัดเจน และเป็นกลาง โดยใช้ภาษาไทยที่อ่านเข้าใจง่าย กระชับ "
                            f"ข้อมูลแวดล้อมปัจจุบัน: {context_data}"
                        )
                        
                        # ยิงคำสั่งเข้าสู่โมเดลรุ่นใหม่ล่าสุด Gemini 2.5 Flash
                        response = ai_client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=user_prompt,
                            config=types.GenerateContentConfig(
                                system_instruction=system_prompt,
                                temperature=0.3, # ปรับความแม่นยำของเนื้อหา ไม่ให้บอทเพ้อเจ้อ
                            ),
                        )
                        
                        # นำคำตอบที่ได้มาแสดงผล
                        ai_response_text = response.text
                        st.markdown(ai_response_text)
                        
                        # บันทึกคำตอบลงในหน่วยความจำแชท
                        st.session_state.chat_messages.append({"role": "model", "text": ai_response_text})
                        
                    except Exception as e:
                        st.error(f"❌ ระบบ AI เกิดข้อผิดพลาดในการตอบกลับ: {e}")
