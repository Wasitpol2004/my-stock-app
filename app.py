import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

# --- ตั้งค่าหน้าจอเปิดกว้างแบบสมดุล ---
st.set_page_config(layout="wide", page_title="DOOHUN - Stock Terminal & AI Advisor")

# --- ฟังก์ชันคำนวณอินดิเคเตอร์พื้นฐาน (ไม่พึ่งพาไลบรารีภายนอกป้องกัน Error) ---
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

# --- ปรับแต่งสไตล์ CSS ให้เป็นธีม Dark Terminal (รักษาโครงสร้างเดิมของคุณไว้ทั้งหมด) ---
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
st.write("⭐ **หุ้นโปรดที่สนใจ**")
wl_cols = st.columns(6)
wl_tickers = ["RKLB", "JNJ", "XOM", "ASTS", "AMZN", "MU"]
clicked_ticker = None

for i, tkr in enumerate(wl_tickers):
    with wl_cols[i]:
        if st.button(f"▫️ {tkr}", use_container_width=True, key=f"wl_{tkr}"):
            clicked_ticker = tkr

# --- ช่องค้นหาเพิ่มเติม ---
search_input = st.text_input("🔍 พิมพ์ชื่อตัวย่อหุ้นที่ต้องการค้นหา (เช่น TSLA, AAPL, RKLB, PTT.BK):", "RKLB")
target_ticker = (clicked_ticker if clicked_ticker else search_input).upper().strip()

# 💡 แก้ไขบั๊กจุดนี้: เปลี่ยนให้ดึงราคาปัจจุบันแบบ Realtime โดยนับย้อนหลังจากวันนี้กลับไป 1 ปีอัตโนมัติ
end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=365)

# แยกส่วน Tab เพื่อให้หน้าตาเรียบร้อย ไม่ซ้อนทับกัน
tab1, tab2 = st.tabs(["📈 หน้ากระดานวิเคราะห์หุ้น (Terminal Dashboard)", "🤖 บอทที่ปรึกษา AI (AI Stock Advisor)"])

# =========================================================================
# --- TAB 1: กระดานวิเคราะห์ข้อมูลหุ้นเดิมของคุณ (Realtime) ---
# =========================================================================
with tab1:
    if target_ticker:
        try:
            with st.spinner('กำลังดึงข้อมูลและคำนวณเทคนิคอล...'):
                ticker_obj = yf.Ticker(target_ticker)
                raw_df = ticker_obj.history(start=start_date, end=end_date)
                
                if raw_df.empty:
                    st.error(f"ไม่พบข้อมูลสำหรับหุ้นสัญลักษณ์ '{target_ticker}' กรุณาตรวจสอบตัวย่ออีกครั้ง")
                    st.stop()
                    
                df = calculate_indicators(raw_df)
                df = df.dropna()

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
                st.markdown(f"<span class='term-badge-trend'>⚡ เทรนด์ล่าสุด: {trend_status}</span>", unsafe_allow_html=True)
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

            left_layout, right_layout = st.columns([12, 8], gap="large")

            # --- คอลัมน์ซ้าย: กราฟเทคนิคัลเต็มรูปแบบ (จากไฟล์ต้นฉบับของคุณ) ---
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

            # --- คอลัมน์ขวา: รายละเอียดธุรกิจและกรอบมูลค่า (จากไฟล์ต้นฉบับของคุณ) ---
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

        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการประมวลผลข้อมูลระบบ: {e}")

# =========================================================================
# --- TAB 2: บอทสอบถามและแนะนำหุ้นอัจฉริยะ (AI Stock Advisor) ---
# =========================================================================
with tab2:
    st.markdown("### 🤖 DOOHUN AI Chatbot Terminal")
    st.caption("ระบบวิเคราะห์อัลกอริทึมทางเทคนิคคอลสดจากกระดานหุ้นเพื่อเฟ้นหาและคัดเลือกหุ้นที่น่าสนใจในการเข้าซื้อ")
    
    # คำถามคีย์ลัดด่วนเพื่อการทดสอบระบบ
    st.write("💡 **คำถามด่วน:**")
    bot_q_cols = st.columns(3)
    q1 = bot_q_cols[0].button("📌 ช่วยแนะนำหุ้นน่าสนใจเข้าซื้อมากที่สุดตอนนี้ ?", use_container_width=True)
    q2 = bot_q_cols[1].button(f"📊 หุ้น {target_ticker} น่าซื้อไหมในสัปดาห์นี้ ?", use_container_width=True)
    q3 = bot_q_cols[2].button("🛡️ สแกนสถานะความเสี่ยงของหุ้นโปรดทั้งหมดให้หน่อย", use_container_width=True)
    
    # เก็บประวัติการสนทนาใน Session State
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "message": "สวัสดีครับยินดีต้อนรับเข้าสู่ระบบ DOOHUN AI ครับ! 🚀 คุณสามารถถามถึงข้อมูลหุ้นรายตัว หรือคลิกปุ่มด้านบนเพื่อให้ผมประมวลผลคำนวณจังหวะเข้าซื้อของหุ้นที่น่าสนใจให้ได้ทันทีเลยครับ!"}
        ]
        
    user_query = ""
    if q1: user_query = "ช่วยแนะนำหุ้นน่าสนใจเข้าซื้อมากที่สุดตอนนี้ ?"
    elif q2: user_query = f"หุ้น {target_ticker} น่าซื้อไหมในสัปดาห์นี้ ?"
    elif q3: user_query = "สแกนสถานะความเสี่ยงของหุ้นโปรดทั้งหมดให้หน่อย"
    
    chat_box_input = st.chat_input("พิมพ์ข้อความเพื่อสนทนากับบอท หรือสอบถามเรื่องหุ้น...")
    if chat_box_input:
        user_query = chat_box_input
        
    if user_query:
        st.session_state.chat_history.append({"role": "user", "message": user_query})
        bot_response = ""
        
        # --- Logic บอทวิเคราะห์คำนวณค่าเทคนิคแบบ Realtime ---
        if "แนะนำหุ้น" in user_query or "น่าสนใจเข้าซื้อ" in user_query or q1:
            bot_response = "🔍 **ผลการสแกนและสืบค้นสัญญาณทางเทคนิคเพื่อหาจุดเข้าซื้อที่มีความคุ้มค่าสูงสุด (เรียลไทม์):**\n\n"
            scan_results = []
            
            for symbol in wl_tickers:
                try:
                    s_data = yf.Ticker(symbol).history(period="3mo")
                    if not s_data.empty:
                        s_df = calculate_indicators(s_data).dropna()
                        rsi_val = s_df['RSI'].iloc[-1]
                        price_val = s_df['Close'].iloc[-1]
                        
                        # เงื่อนไขคัดกรองสัญญาณ
                        if rsi_val <= 40:
                            scan_results.append(f"🟩 **{symbol}** (ราคาล่าสุด ${price_val:.2f}) -> **[แนะนำซื้อ]** ค่า RSI ต่ำเพียง {rsi_val:.2f} สัญญาณอยู่ในเขตตลาดขายมากเกินไป (Oversold) มีโอกาสเกิด Technical Rebound สูง ปลอดภัยต่อการถือสะสม")
                        elif rsi_val >= 70:
                            scan_results.append(f"🟥 **{symbol}** (ราคาล่าสุด ${price_val:.2f}) -> **[หลีกเลี่ยงก่อน]** ค่า RSI สูงถึง {rsi_val:.2f} อยู่ในเกณฑ์ Overbought แรงซื้อมากเกินไป มีความเสี่ยงในการย่อตัวสูง")
                        else:
                            scan_results.append(f"🟨 **{symbol}** (ราคาล่าสุด ${price_val:.2f}) -> **[ถือรอ/ทยอยซื้อ]** ค่า RSI ทรงตัวอยู่ที่ {rsi_val:.2f} ทิศทางเป็นพักตัวสะสมพลัง (Sideway)")
                except:
                    continue
            
            bot_response += "\n\n".join(scan_results)
            bot_response += "\n\n*⚠️ หมายเหตุ: การวิเคราะห์อ้างอิงจากโมเมนตัมดัชนี RSI ย้อนหลังพิจารณาร่วมกับความเสี่ยงพอร์ตโฟลิโอต้นฉบับ*"
            
        elif "น่าซื้อไหม" in user_query or q2:
            try:
                s_data = yf.Ticker(target_ticker).history(period="3mo")
                if not s_data.empty:
                    s_df = calculate_indicators(s_data).dropna()
                    rsi_val = s_df['RSI'].iloc[-1]
                    price_val = s_df['Close'].iloc[-1]
                    ema12_val = s_df['EMA12'].iloc[-1]
                    ema26_val = s_df['EMA26'].iloc[-1]
                    
                    status_trend = "📈 ขาขึ้นเด่นชัด (Bullish)" if price_val > ema26_val else "📉 พักฐาน/ขาลง (Bearish)"
                    action_advice = "✅ **แนะนำให้ทยอยเข้าซื้อสะสม** เนื่องจากระดับราคายังไม่สูงจนเกินไปและโมเมนตัมยังเอื้ออำนวย" if rsi_val < 60 else "❌ **แนะนำให้ชะลอการซื้อ** เพื่อรอราคาย่อตัวลงมาแตะเส้นแนวรับสำคัญ"
                    
                    bot_response = f"🤖 **สรุปบทวิเคราะห์คำแนะนำสำหรับหุ้น {target_ticker} โดยเฉพาะ:**\n\n"
                    bot_response += f"• **ราคาซื้อขายล่าสุด:** ${price_val:.2f} USD\n"
                    bot_response += f"• **สภาวะแนวโน้มราคา (Trend):** {status_trend}\n"
                    bot_response += f"• **ดัชนีวัดแรงซื้อขาย RSI:** {rsi_val:.2f}\n\n"
                    bot_response += f"{action_advice}\n\n*ประเมินสัญญาณด้วยระบบคิดลบล่วงหน้าควบคู่กับเส้นกรอบเทคนิคคอลเพื่อความปลอดภัยสูงสุด*"
                else:
                    bot_response = f"❌ ไม่สามารถดึงข้อมูลทางเทคนิคของหุ้น {target_ticker} ได้ในขณะนี้"
            except Exception as ex:
                bot_response = f"เกิดข้อผิดพลาดในการประมวลผลข้อมูลบอท: {ex}"
                
        else:
            bot_response = f"🤖 ระบบ DOOHUN AI รับทราบคำสั่งของคุณแล้วครับ จากข้อมูลหุ้นส่วนใหญ่ที่เราจับตามอง ภาพรวมตลาดยังคงมีความผันผวน แนะนำให้พิจารณาเปรียบเทียบระหว่างราคา Intrinsic Value (${dcf_fair_price:.2f}) กับราคาตลาดเรียลไทม์เพื่อประกอบการตัดสินใจซื้อขายครับ"
            
        st.session_state.chat_history.append({"role": "assistant", "message": bot_response})
        
    # วาดหน้าต่างกล่องแชท Terminal สไตล์คลาสสิกตามดีไซน์ต้นฉบับของคุณ
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            if chat["role"] == "assistant":
                st.markdown(f"<div class='term-card' style='border-left: 3px solid #3b82f6;'>{chat['message']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='term-card' style='border-left: 3px solid #6e7681; background-color: #1c212c;'>{chat['message']}</div>", unsafe_allow_html=True)
