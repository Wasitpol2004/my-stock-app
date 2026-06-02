import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import os
from google import genai
from google.genai import types

# ตั้งค่าหน้าจอ
st.set_page_config(layout="wide", page_title="DOOHUN - Stock & AI")

# --- โหลด API Key ---
api_key = st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else os.environ.get("GEMINI_API_KEY")
ai_client = genai.Client(api_key=api_key) if api_key else None

# --- ฟังก์ชันคำนวณ ---
def calculate_indicators(df):
    df = df.copy()
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# --- UI หลัก ---
st.title("DOOHUN | ระบบวิเคราะห์หุ้นและ AI")
ticker = st.text_input("ใส่ชื่อหุ้น (เช่น RKLB, TSLA):", "RKLB").upper()

# ดึงข้อมูล
if ticker:
    df = yf.Ticker(ticker).history(period="1y")
    if not df.empty:
        df = calculate_indicators(df)
        
        # สร้าง Tabs
        tab1, tab2 = st.tabs(["📊 กราฟเทคนิค", "🤖 AI วิเคราะห์หุ้น"])
        
        with tab1:
            st.write(f"ราคาล่าสุด: ${df['Close'].iloc[-1]:.2f}")
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
            st.plotly_chart(fig, use_container_width=True)
            
        with tab2:
            if not ai_client:
                st.error("กรุณาตั้งค่า GEMINI_API_KEY ในช่อง Secrets")
            else:
                if "messages" not in st.session_state:
                    st.session_state.messages = []
                
                for msg in st.session_state.messages:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["text"])
                        
                if prompt := st.chat_input("ถาม AI เกี่ยวกับหุ้นตัวนี้..."):
                    st.session_state.messages.append({"role": "user", "text": prompt})
                    with st.chat_message("user"):
                        st.markdown(prompt)
                    
                    with st.chat_message("assistant"):
                        response = ai_client.models.generate_content(
                            model="gemini-2.0-flash",
                            contents=f"หุ้น {ticker} ราคาปัจจุบัน {df['Close'].iloc[-1]:.2f}. คำถาม: {prompt}"
                        )
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "text": response.text})
    else:
        st.error("ไม่พบข้อมูลหุ้น")
