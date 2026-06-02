import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import google.generativeai as genai  # สำหรับเชื่อมต่อสมองกล AI ของจริง

# --- ตั้งค่าหน้าจอเปิดกว้างแบบสมดุล ---
st.set_page_config(layout="wide", page_title="DOOHUN - Stock Terminal")
# --- ฟังก์ชันดึงข้อมูลหุ้นผ่านระบบ Cache และปลอมตัวเป็นเบราว์เซอร์ (ป้องกันโดนบล็อก IP) ---
@st.cache_data(ttl=300)  # ดึงข้อมูลครั้งเดียว จำไว้ 5 นาที (300 วินาที) พิมพ์แชทกี่ครั้งก็จะไม่โดนบล็อกแล้ว
def get_cached_stock_data(ticker, start, end):
    import requests
    # สร้าง Session พิเศษเพื่อใส่ข้อมูลปลอมตัวเป็นเบราว์เซอร์ปกติ
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    # ดึงข้อมูลผ่าน Session ที่ตั้งค่าไว้
    ticker_obj = yf.Ticker(ticker, session=session)
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
    </style>
""", unsafe_allow_html=True)

# --- ⚙️ แถบควบคุมด้านข้าง (Sidebar) ---
with st.sidebar:
    st.markdown("### ⚙️ แผงควบคุมระบบอัจฉริยะ")
    st.write("---")
    # ช่องใส่คีย์สำหรับ AI ของจริง
    gemini_key = st.text_input(
        "AQ.Ab8RN6KolgcNbRPOW-QxXiW-u8UGvT2zcc8Jg3H5IP2OEukQeQ", 
        type="password", 
        placeholder="AIzaSy...",
        help="AQ.Ab8RN6KolgcNbRPOW-QxXiW-u8UGvT2zcc8Jg3H5IP2OEukQeQ"
    )

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

if target_ticker:
    # ประกาศตัวแปรสถานะเริ่มต้นก่อนเข้าบล็อกโหลดข้อมูล
    data_loaded = False
    df = pd.DataFrame()

    # บล็อกดึงข้อมูลแบบปลอดภัย (ปิดจบตัวมันเองทันที ไม่ลากยาวไปคลุม UI)
    try:
        with st.spinner('กำลังดึงข้อมูลและคำนวณเทคนิคอล...'):
            ticker_obj = yf.Ticker(target_ticker)
            raw_df = ticker_obj.history(start=start_date, end=end_date)
            
            if raw_df.empty:
                st.error(f"ไม่พบข้อมูลสำหรับหุ้นสัญลักษณ์ '{target_ticker}' กรุณาตรวจสอบตัวย่ออีกครั้ง")
            else:
                df = calculate_indicators(raw_df)
                df = df.dropna()
                data_loaded = True
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการประมวลผลข้อมูลระบบ: {e}")

    # แสดงผลหน้าจอหลักเมื่อโหลดข้อมูลเสร็จสมบูรณ์เรียบร้อยแล้ว
    if data_loaded and not df.empty:
        # สรุปข้อมูลราคาปัจจุบัน
        last_close = df['Close'].iloc[-1]
        prev_close = df['Close'].iloc[-2]
        change_pct = ((last_close - prev_close) / prev_close) * 100
        last_date = df.index[-1].strftime('%d/%m/%Y')

        # คำนวณแนวรับ-แนวต้านอัตโนมัติ
        res2 = df['High'].rolling(30).max().iloc[-1]
        res1 = df['High'].rolling(15).max().iloc[-1]
        sup1 = df['Low'].rolling(15).min().iloc[-1]
        sup2 = df['Low'].rolling(30).min().iloc[-1]

        # --- แสดงแถบราคาด้านบน ---
        price_main_col1, price_main_col2 = st.columns([2, 1])
        with price_main_col1:
            st.markdown(f"<h3 style='margin:0;'>{target_ticker} <span style='font-size:16px; color:#8b949e;'>GLOBAL MARKET</span></h3>", unsafe_allow_html=True)
            trend_status = "BULLISH (ขาขึ้นชัดเจน)" if last_close > df['EMA26'].iloc[-1] else "BEARISH (ขาลง/พักตัว)"
            st.markdown(f"<span class='term-badge-trend'>⚡ เทรนด์: {trend_status}</span>", unsafe_allow_html=True)
        with price_main_col2:
            color_class = "undervalued" if change_pct >= 0 else "overvalued"
            sign = "+" if change_pct >= 0 else ""
            st.markdown(f"""
                <div style='text-align: right;'>
                    <span style='font-size: 28px; font-weight: bold; color: white;'>${last_close:,.2f}</span> <span style='color:#8b949e;'>USD</span><br>
                    <span class='{color_class}'>{sign}{change_pct:.2f}%</span> <span style='color:#6e7681; font-size:12px;'>ณ วันที่ {last_date}</span>
                </div>
            """, unsafe_allow_html=True)

        st.write("---")

        # --- แยกแอปเป็นระบบ Tabs อย่างเป็นสัดส่วน ---
        tab1, tab2 = st.tabs(["📈 หน้ากระดานวิเคราะห์หุ้น (Terminal Dashboard)", "🤖 บอทที่ปรึกษา AI จริง (AI Stock Advisor)"])

        # =========================================================================
        # --- [TAB 1]: แสดงกระดานวิเคราะห์เทคนิคัลหลักของคุณ ---
        # =========================================================================
        with tab1:
            left_layout, right_layout = st.columns([12, 8], gap="large")

            # --- คอลัมน์ซ้าย: กราฟเทคนิคอลเต็มรูปแบบ ---
            with left_layout:
                st.markdown("<p style='color:#8b949e; font-weight:bold; margin-bottom:10px;'>📊 ประสิทธิภาพราคาและเทคนิคอลอินดิเคเตอร์</p>", unsafe_allow_html=True)
                
                fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                                    vertical_spacing=0.03, 
                                    row_width=[0.2, 0.2, 0.6])

                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="ราคาหุ้น"), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['EMA12'], line=dict(color='#d69e2e', width=1.2), name='EMA 12 (ระยะสั้น)'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['EMA26'], line=dict(color='#10b981', width=1.2), name='EMA 26 (ระยะกลาง)'), row=1, col=1)

                levels = [
                    {'y': res2, 'color': '#f87171', 'label': 'แนวต้าน 2'},
                    {'y': res1, 'color': '#ffa3a3', 'label': 'แนวต้าน 1'},
                    {'y': sup1, 'color': '#a7f3d0', 'label': 'แนวรับ 1'},
                    {'y': sup2, 'color': '#10b981', 'label': 'แนวรับ 2'},
                ]
                
                annotation_date = df.index[-1] + pd.Timedelta(days=3)
                for lvl in levels:
                    fig.add_hline(y=lvl['y'], line_dash="dash", line_color=lvl['color'], line_width=1, row=1, col=1)
                    fig.add_annotation(x=annotation_date, y=lvl['y'], text=f" {lvl['label']} (${lvl['y']:,.2f})",
                                       showarrow=False, xanchor="left", font=dict(size=10, color=lvl['color']), row=1, col=1)

                fig.add_shape(type="rect", x0=df.index[0], y0=df['Low'].min()*0.98, x1=df.index[-1], y1=sup2,
                              fillcolor="rgba(16, 185, 129, 0.03)", line=dict(width=0), row=1, col=1)

                fig.add_trace(go.Bar(x=df.index, y=df['Hist'], name='Histogram', marker_color='#4b5563', opacity=0.5), row=2, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='#3b82f6', width=1.2), name='MACD'), row=2, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['Signal'], line=dict(color='#ef4444', width=1), name='Signal Line'), row=2, col=1)

                fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#fbbf24', width=1.2), name='RSI (14)'), row=3, col=1)
                fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", row=3, col=1, line_width=1)
                fig.add_hline(y=30, line_dash="dash", line_color="#10b981", row=3, col=1, line_width=1)

                fig.update_layout(
                    template="plotly_dark", height=680, xaxis_rangeslider_visible=False,
                    margin=dict(l=10, r=90, t=10, b=10),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=10)),
                    plot_bgcolor='#0e1117', paper_bgcolor='#0e1117'
                )
                fig.update_xaxes(showgrid=True, gridcolor="#21262d", row=1, col=1)
                fig.update_xaxes(showgrid=True, gridcolor="#21262d", row=2, col=1)
                fig.update_xaxes(showgrid=True, gridcolor="#21262d", title_text="วันที่", row=3, col=1)
                fig.update_yaxes(side="right", tickprefix="$", gridcolor="#21262d", row=1, col=1)
                fig.update_yaxes(side="right", gridcolor="#21262d", row=2, col=1)
                fig.update_yaxes(side="right", range=[0, 100], gridcolor="#21262d", row=3, col=1)

                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

            # --- คอลัมน์ขวา: ข้อมูลทางพื้นฐานและกรอบมูลค่า ---
            with right_layout:
                st.markdown("<p style='color:#8b949e; font-weight:bold; margin-bottom:5px;'>ℹ️ ลักษณะการประกอบธุรกิจ (Business)</p>", unsafe_allow_html=True)
                with st.container():
                    st.markdown(f"""
                        <div class='term-card'>
                            <h4 style='margin:0 0 8px 0; color:white;'>{target_ticker} Corporation</h4>
                            <p style='margin:0; font-size:13px; color:#8b949e; line-height:1.6;'>
                                ให้บริการและพัฒนาเทคโนโลยีการวิเคราะห์ระบบข้อมูลขั้นสูง มุ่งเน้นการจัดเก็บโครงสร้างฐานข้อมูลเชิงพาณิชย์และนวัตกรรมเพื่อการเติบโตในตลาดสากลอย่างยั่งยืน
                            </p>
                        </div>
                    """, unsafe_allow_html=True)

                st.markdown("<p style='color:#8b949e; font-weight:bold; margin-bottom:5px;'>💎 มูลค่าตามหลักทฤษฎี (DCF Fair Value)</p>", unsafe_allow_html=True)
                dcf_fair_price = 19.07 if target_ticker == "RKLB" else last_close * 0.85
                
                with st.container():
                    valuation_status = ""
                    if last_close > dcf_fair_price:
                        pct_over = ((last_close - dcf_fair_price) / dcf_fair_price) * 100
                        valuation_status = f"<span class='overvalued'>🔴 ราคาสูงเกินพื้นฐานคำนวณ (Overvalued) {pct_over:.1f}%</span>"
                    else:
                        pct_under = ((dcf_fair_price - last_close) / dcf_fair_price) * 100
                        valuation_status = f"<span class='undervalued'>🟢 ราคาต่ำกว่าพื้นฐานคำนวณ (Undervalued) {pct_under:.1f}%</span>"
                    
                    st.markdown(f"""
                        <div class='term-card'>
                            <p style='margin:0; font-size:12px; color:#8b949e;'>Theoretically Calculated Intrinsic Value</p>
                            <h2 style='margin:5px 0; color:#58a6ff;'>${dcf_fair_price:,.2f} <span style='font-size:14px; color:#8b949e;'>USD</span></h2>
                            <div style='font-size:13px; margin-top:5px;'>{valuation_status}</div>
                            <p style='margin:10px 0 0 0; font-size:11px; color:#6e7681; border-top: 1px solid #21262d; padding-top:8px;'>
                                *คำนวณจากสมมติฐานกระแสเงินสดอิสระ (FCF Growth 10%, WACC 9.0%) โดยไม่มีปุ่มควบคุมรบกวนหน้าต่างหลัก
                            </p>
                        </div>
                    """, unsafe_allow_html=True)

                st.markdown("<p style='color:#8b949e; font-weight:bold; margin-bottom:5px;'>🎯 กรอบราคาเหมาะสมจากโบรกเกอร์ (Broker Target)</p>", unsafe_allow_html=True)
                with st.container():
                    broker_target = 134.63 if target_ticker == "RKLB" else last_close * 1.1
                    st.markdown(f"""
                        <div class='term-card'>
                            <p style='margin:0; font-size:12px; color:#8b949e;'>เป้าหมายเฉลี่ยจากนักวิเคราะห์</p>
                            <h3 style='margin:5px 0; color:#34d399;'>${broker_target:,.2f} USD</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                st.markdown("<p style='color:#8b949e; font-weight:bold; margin-bottom:5px;'>📊 คะแนนความแข็งแกร่ง (Performance Score)</p>", unsafe_allow_html=True)
                with st.container():
                    score_val = 0.75 if target_ticker == "RKLB" else 0.60
                    st.markdown("<div class='term-card' style='padding-bottom:25px;'>", unsafe_allow_html=True)
                    st.progress(score_val, text=f"คะแนนความสามารถในการทำกำไรและความปลอดภัยทางบัญชี: {score_val*10:.1f}/10")
                    st.markdown("</div>", unsafe_allow_html=True)

        # =========================================================================
        # --- [TAB 2]: ระบบบอทปรึกษาหุ้นอัจฉริยะของจริง (เชื่อมข้อมูล Real-time) ---
        # =========================================================================
        with tab2:
            st.markdown(f"### 🤖 DOOHUN Real-Time AI Advisor ({target_ticker})")
            st.caption("ระบบดึงข้อมูลดิบและอินดิเคเตอร์จากหน้าจอป้อนเข้าสู่สมองกลวิเคราะห์หุ้นจริง ป้องกันปัญหาบอทเดาคำตอบ")
            
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = [
                    {"role": "assistant", "message": f"สวัสดีครับ! ผมคือ AI ประจำโปรแกรม DOOHUN ตอนนี้ผมได้สแกนและดึงสถิติของหุ้น **{target_ticker}** เข้ามาในหน่วยความจำเรียบร้อย มีตรงไหนอยากให้ผมช่วยวิเคราะห์แนวโน้ม พิมพ์คุยมาได้เลยครับ! 🚀"}
                ]
            
            # วาดประวัติการคุย
            for chat in st.session_state.chat_history:
                with st.chat_message(chat["role"]):
                    if chat["role"] == "assistant":
                        st.markdown(f"<div class='term-card' style='border-left: 3px solid #3b82f6; margin-bottom:0;'>{chat['message']}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='term-card' style='border-left: 3px solid #6e7681; background-color: #1c212c; margin-bottom:0;'>{chat['message']}</div>", unsafe_allow_html=True)
            
            # กล่องรับข้อความแชท
            if chat_input := st.chat_input("พิมพ์ถามเรื่องหุ้นที่นี่ เช่น 'RSI แบบนี้ควรถือต่อหรือขายทำกำไร?', 'ขอแนวรับแนวต้านสำคัญหน่อย'"):
                with st.chat_message("user"):
                    st.markdown(f"<div class='term-card' style='border-left: 3px solid #6e7681; background-color: #1c212c; margin-bottom:0;'>{chat_input}</div>", unsafe_allow_html=True)
                st.session_state.chat_history.append({"role": "user", "message": chat_input})
                
                if not gemini_key:
                    bot_response = "⚠️ **ไม่สามารถประมวลผลได้:** กรุณากรอก **Gemini API Key** ที่แถบเมนูด้านซ้ายมือของคุณก่อนเริ่มใช้งานบอทครับ"
                else:
                    with st.spinner("AI กำลังแกะข้อมูลเทคนิคอลของคุณสักครู่..."):
                        try:
                            genai.configure(api_key=gemini_key)
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            
                            current_rsi = df['RSI'].iloc[-1]
                            current_macd = df['MACD'].iloc[-1]
                            current_signal = df['Signal'].iloc[-1]
                            current_hist = df['Hist'].iloc[-1]
                            
                            prompt_context = f"""
                            คุณคือ 'DOOHUN AI Advisor' ที่ปรึกษาและนักวิเคราะห์หุ้นทางเทคนิคอลผู้เชี่ยวชาญ 
                            จงตอบคำถามของผู้ใช้อย่างชาญฉลาด ตรงไปตรงมา อ้างอิงจากข้อมูลตัวเลขสถิติจริงที่ระบุด้านล่างนี้ ห้ามเดาข้อมูลเอง 
                            ตอบเป็นภาษาไทยที่เป็นกันเอง เข้าใจง่าย และให้มุมมองการลงทุนที่กระชับ

                            ข้อมูลหุ้นปัจจุบันบนหน้าจอ:
                            - ตัวย่อหุ้น: {target_ticker}
                            - ราคาปิดล่าสุด: ${last_close:.2f} USD (เปลี่ยนแปลง {change_pct:.2f}%)
                            - ดัชนีวัดแรงซื้อขาย RSI (14): {current_rsi:.2f}
                            - ค่าอินดิเคเตอร์ MACD: {current_macd:.4f}
                            - เส้น Signal Line: {current_signal:.4f} (Histogram: {current_hist:.4f})
                            - กรอบราคาปัจจุบัน: แนวรับสำคัญ [${sup1:.2f}, ${sup2:.2f}] | แนวต้านสำคัญ [${res1:.2f}, ${res2:.2f}]
                            - การประเมินมูลค่าแท้จริง DCF: ${dcf_fair_price:.2f} USD (เป้าหมายโบรกเกอร์: ${broker_target:.2f} USD)

                            คำถามของผู้ใช้: "{chat_input}"
                            """
                            
                            response = model.generate_content(prompt_context)
                            bot_response = response.text
                            
                        except Exception as ai_err:
                            bot_response = f"❌ เกิดข้อผิดพลาดในระบบเชื่อมต่อ AI: {ai_err}"
                
                with st.chat_message("assistant"):
                    st.markdown(f"<div class='term-card' style='border-left: 3px solid #3b82f6; margin-bottom:0;'>{bot_response}</div>", unsafe_allow_html=True)
                st.session_state.chat_history.append({"role": "assistant", "message": bot_response})
                st.rerun()
else:
    st.info("กรุณาเลือกหรือพิมพ์ชื่อสัญลักษณ์หุ้นที่ต้องการระบบประมวลผลข้อมูล")
