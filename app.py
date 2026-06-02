import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import os

# 1. ตั้งค่าระบบหน้าจออัจฉริยะแบบกว้าง (Wide Mode)
st.set_page_config(
    page_title="DOOHUN Terminal & AI Advisor",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# จัดแต่งสไตล์สไตล์ธีมเทอร์มินอลมืด
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
    .stTextInput input { background-color: #1e222b; color: white; border: 1px solid #363c4e; }
    div.stButton > button { width: 100%; background-color: #2962ff; color: white; font-weight: bold; }
    .chat-bubble { padding: 12px; border-radius: 8px; margin-bottom: 10px; line-height: 1.5; }
    </style>
""", unsafe_allow_html=True)

# ฟังก์ชันคำนวณอินดิเคเตอร์เทคนิคสำหรับบอทและกราฟ
def analyze_stock_metrics(symbol):
    try:
        df = yf.download(symbol, period="6mo", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
        
        # คำนวณเส้นเทคนิคพื้นฐาน
        df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
        
        # คำนวณ RSI (Relative Strength Index) แบบแมนนวลป้องกันไลบรารีพัง
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df
    except Exception:
        return None

# ส่วนหัวโปรแกรม
st.markdown("<h2>🚀 DOOHUN <span style='font-size:16px; color:#2962ff;'>| Terminal x AI Advisor v2</span></h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #848e9c; font-size: 13px; margin-top:-5px;'>ระบบจำลองโบรกเกอร์อัจฉริยะและกระดานวิเคราะห์ข้อมูลหุ้นสด</p>", unsafe_allow_html=True)

# 2. สร้างแท็บสำหรับแบ่งหน้าเว็บใหม่แยกออกจากกัน
tab1, tab2 = st.tabs(["📈 หน้ากระดานราคาหุ้น Realtime", "🤖 บอทที่ปรึกษาการลงทุน AI Advisor"])

# กำหนดรายชื่อหุ้นยอดนิยมในระบบสแกน
watchlist = ["RKLB", "AAPL", "NVDA", "TSLA", "AMZN"]

# ==========================================
#  TAB 1: หน้ากระดานราคาหุ้น Realtime
# ==========================================
with tab1:
    col_ctrl1, col_ctrl2 = st.columns([3, 1])
    with col_ctrl1:
        ticker = st.text_input("🔍 ระบุชื่อย่อหุ้นที่ต้องการดูราคาสดวันนี้:", value="RKLB").upper().strip()
    with col_ctrl2:
        time_frame = st.selectbox("📅 ช่วงเวลากราฟ:", ["1 เดือน", "3 เดือน", "6 เดือน", "1 ปี"], index=2)
    
    tf_map = {"1 เดือน":"1mo", "3 เดือน":"3mo", "6 เดือน":"6mo", "1 ปี":"1y"}
    
    df_data = analyze_stock_metrics(ticker)
    
    if df_data is not None and not df_data.empty:
        current_price = float(df_data['Close'].iloc[-1])
        prev_price = float(df_data['Close'].iloc[-2])
        price_diff = current_price - prev_price
        pct_diff = (price_diff / prev_price) * 100
        rsi_now = float(df_data['RSI'].iloc[-1])
        
        # แสดงราคามุมขวาแบบเรียลไทม์
        st.markdown(f"""
            <div style='text-align: right; margin-top: -65px;'>
                <span style='font-size: 28px; font-weight: bold;'>${current_price:,.2f}</span> <span style='font-size:12px; color:#848e9c;'>USD</span><br>
                <span style='color: {"#00c805" if price_diff >= 0 else "#ff3b30"}; font-size: 14px; font-weight: bold;'>
                    {"+" if price_diff >= 0 else ""}{price_diff:.2f} ({pct_diff:.2f}%) วันนี้
                </span>
            </div>
        """, unsafe_allow_html=True)
        
        st.write(f"### กระดานหุ้น: {ticker}")
        
        col_m1, col_m2 = st.columns([3, 2])
        with col_m1:
            # วาดกราฟเทคนิคคอล
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df_data.index, open=df_data['Open'], high=df_data['High'], low=df_data['Low'], close=df_data['Close'], name="ราคา"))
            fig.add_trace(go.Scatter(x=df_data.index, y=df_data['EMA12'], mode='lines', name='EMA 12', line=dict(color='#2962ff')))
            fig.add_trace(go.Scatter(x=df_data.index, y=df_data['EMA26'], mode='lines', name='EMA 26', line=dict(color='#ff9800')))
            fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=400, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
            
        with col_m2:
            st.markdown("📊 **สรุปค่าสัญญาณด่วนรายวัน:**")
            st.metric(label="ดัชนีแรงซื้อ RSI (14 วัน)", value=f"{rsi_now:.2f}", delta="Oversold เกินไปน่าซื้อ" if rsi_now < 30 else ("Overbought ต้องระวัง" if rsi_now > 70 else "สภาวะปกติ"))
            
            # ตารางราคาประวัติ 5 วันล่าสุด
            st.markdown("📋 **ประวัติราคาปิดย้อนหลัง 5 วันล่าสุด:**")
            st.dataframe(df_data[['Open', 'High', 'Low', 'Close']].tail(5), use_container_width=True)
    else:
        st.info("💡 กรุณากรอกชื่อหุ้นเพื่อแสดงผลราคาสดและกราฟเทคนิคคอล")

# ==========================================
#  TAB 2: หน้าบอทที่ปรึกษาการลงทุน AI Advisor
# ==========================================
with tab2:
    st.markdown("### 🤖 ระบบ AI คัดกรองและแนะแนวหุ้นอัตโนมัติ")
    st.caption("บอทจะอ่านข้อมูลอินดิเคเตอร์สดจากตลาดหุ้นเพื่อนำมาวิเคราะห์จังหวะการเข้าซื้อ-ขายให้คุณทันที")
    
    # ตัวอย่างคำถามแนะนำที่กดส่งได้เลย
    st.write("💡 **คำถามแนะนำที่คุณสามารถถามบอทได้:**")
    col_q1, col_q2, col_q3 = st.columns(3)
    q1 = col_q1.button("📌 ตอนนี้หุ้นตัวไหนน่าสนใจซื้อที่สุด?")
    q2 = col_q2.button("📌 วิเคราะห์หุ้น RKLB ให้หน่อย?")
    q3 = col_q3.button("📌 หุ้น NVDA สัญญาณเป็นอย่างไรบ้าง?")
    
    # ระบบบันทึกประวัติการแชท
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "message": "สวัสดีครับ! ผมคือบอทที่ปรึกษาการลงทุนอัจฉริยะ DOOHUN AI คุณอยากให้ผมสแกนหุ้นตัวไหน หรืออยากให้แนะนำหุ้นที่น่าสนใจพิมพ์ถามมาได้เลยครับ! 📈"}
        ]
        
    # จัดการอินพุตคำถาม (จากปุ่มกด หรือจากช่องพิมพ์แชท)
    user_query = ""
    if q1: user_query = "ตอนนี้หุ้นตัวไหนน่าสนใจซื้อที่สุด?"
    elif q2: user_query = "วิเคราะห์หุ้น RKLB ให้หน่อย?"
    elif q3: user_query = "หุ้น NVDA สัญญาณเป็นอย่างไรบ้าง?"
    
    chat_input = st.chat_input("พิมพ์คำถามของคุณที่นี่... (เช่น แนะนำหุ้น AAPL หน่อย, หุ้นตัวไหนน่าซื้อ)")
    if chat_input:
        user_query = chat_input
        
    if user_query:
        # บันทึกคำถามผู้ใช้ลงประวัติแชท
        st.session_state.chat_history.append({"role": "user", "message": user_query})
        
        # --- ประมวลผลคำตอบของบอท (AI Logic Simulation) ---
        bot_reply = ""
        query_upper = user_query.upper()
        
        # กรณีที่ 1: ผู้ใช้ถามหาหุ้นน่าซื้อที่สุดใน Watchlist
        if "ตัวไหนน่าซื้อ" in user_query or "แนะนำหุ้น" in user_query and not any(s in query_upper for s in watchlist):
            bot_reply = "🔍 **ระบบ AI ทำการสแกนหุ้นใน Watchlist ยอดนิยมให้คุณเรียบร้อยครับ:**\n\n"
            recommended_stocks = []
            
            for s in watchlist:
                sd = analyze_stock_metrics(s)
                if sd is not None:
                    r_val = float(sd['RSI'].iloc[-1])
                    c_price = float(sd['Close'].iloc[-1])
                    # เงื่อนไขคัดกรองหุ้นน่าซื้อ: RSI ต่ำ หรือราคากำลังสร้างฐาน
                    if r_val < 45:
                        recommended_stocks.append(f"🟢 **{s}** (ราคาปัจจุบัน ${c_price:.2f}) -> สัญญาณน่าสนใจมาก! ค่า RSI อยู่ที่ {r_val:.2f} ตลาดกำลังเทขายมากเกินไป มีโอกาสเด้งกลับสูงในระยะสั้น")
                    elif r_val > 70:
                        recommended_stocks.append(f"🔴 **{s}** (ราคาปัจจุบัน ${c_price:.2f}) -> RSI สูงถึง {r_val:.2f} เสี่ยงดอยสูง แนะนำชะลอการซื้อเพื่อรอย่อตัวก่อน")
                    else:
                        recommended_stocks.append(f"🟡 **{s}** (ราคาปัจจุบัน ${c_price:.2f}) -> RSI อยู่ที่ {r_val:.2f} สภาพราคากำลังไซด์เวย์สะสมพลัง เหมาะสำหรับทยอยสะสม")
            
            bot_reply += "\n\n".join(recommended_stocks)
            bot_reply += "\n\n*⚠️ คำเตือน: นี่เป็นเพียงการวิเคราะห์เชิงเทคนิคด้วย AI เบื้องต้น โปรดพิจารณาความเสี่ยงก่อนตัดสินใจซื้อขาย*"
            
        # กรณีที่ 2: ผู้ใช้ระบุชื่อหุ้นชัดเจนเพื่อให้วิเคราะห์รายตัว
        else:
            # ค้นหาว่าผู้ใช้ระบุหุ้นตัวไหนในประโยค
            found_stock = "RKLB"  # ค่าเริ่มต้นหากเดาชื่อหุ้นไม่ได้
            for s in watchlist:
                if s in query_upper:
                    found_stock = s
                    break
                    
            sd = analyze_stock_metrics(found_stock)
            if sd is not None:
                r_val = float(sd['RSI'].iloc[-1])
                c_price = float(sd['Close'].iloc[-1])
                ema12 = float(sd['EMA12'].iloc[-1])
                ema26 = float(sd['EMA26'].iloc[-1])
                
                status = "📈 แนวโน้มขาขึ้นแข็งแกร่ง (Bullish)" if ema12 > ema26 else "📉 แนวโน้มระวังการย่อตัว (Bearish)"
                advice = "✅ **คำแนะนำในการซื้อ:** เหมาะแก่การเข้าซื้อสะสม เนื่องจากราคาปิดยืนเหนือเส้นสัญญาณสำคัญและค่า RSI ไม่แรงเกินไป" if r_val < 55 else "❌ **คำแนะนำในการซื้อ:** แนะนำให้ 'ถือรอ' หรือรอให้ย่อตัวลงมาใกล้แนวรับก่อนเข้าซื้อเพิ่ม เพื่อป้องกันความเสี่ยง"
                
                bot_reply = f"🤖 **ผลการวิเคราะห์เจาะลึกหุ้น {found_stock} โดย DOOHUN AI:**\n\n"
                bot_reply += f"• **ราคาปิดล่าสุด:** ${c_price:.2f} USD\n"
                bot_reply += f"• **สัญญาณทิศทางราคากราฟ:** {status}\n"
                bot_reply += f"• **ดัชนีโมเมนตัม RSI:** {r_val:.2f}\n\n"
                bot_reply += f"{advice}\n\n*สัญญาณทางเทคนิคบ่งชี้ว่าตัวนี้มีมูลค่าซื้อขายหนาแน่นและปลอดภัยในการจัดพอร์ตรายสัปดาห์ครับ*"
            else:
                bot_reply = "❌ ขออภัยครับ ระบบไม่สามารถดึงข้อมูลหุ้นที่คุณระบุได้ในขณะนี้ กรุณาเช็กตัวสะกดชื่อย่อหุ้นอีกครั้งครับ"
                
        # บันทึกคำตอบบอทลงประวัติแชท
        st.session_state.chat_history.append({"role": "assistant", "message": bot_reply})
        
    # แสดงบทสนทนาทั้งหมดตามสไตล์ Chat UI สากล
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.markdown(chat["message"])
