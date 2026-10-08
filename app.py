import streamlit as st
import yfinance as yf
import pandas as pd
from groq import Groq
import os

# Initialize Groq Client
# Ensure GROQ_API_KEY is set in Render's Environment Variables
groq_api_key = os.environ.get("GROQ_API_KEY", "")
client = Groq(api_key=groq_api_key) if groq_api_key else None

st.set_page_config(page_title="NSE Advanced Stock Analyzer", layout="wide")
st.title("🚀 Advanced NSE Stock Fundamental Analyzer & LLM Picker")

# 1. Define Stock List (Easily expandable)
NIFTY_BATCH = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "ITC.NS", "TATAMOTORS.NS", "SBIN.NS"]

@st.cache_data(ttl=3600)  # Cache data for 1 hour to avoid yfinance rate limits
def fetch_stock_data(tickers):
    data_list = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Advanced Fundamental Metrics Extraction
            metrics = {
                "Ticker": ticker,
                "Company": info.get("longName", ticker),
                "P/E Ratio": info.get("trailingPE", None),
                "P/B Ratio": info.get("priceToBook", None),
                "ROE (%)": info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else None,
                "Debt/Equity": info.get("debtToEquity", None),
                "Free Cash Flow (Cr)": (info.get("freeCashflow", 0) / 10000000) if info.get("freeCashflow") else None,
                "Dividend Yield (%)": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0,
                "Current Price": info.get("currentPrice", None)
            }
            data_list.append(metrics)
        except Exception as e:
            st.warning(f"Error fetching {ticker}: {str(e)}")
    return pd.DataFrame(data_list)

# Load data
st.subheader("📊 Step 1: Extracting Live Fundamental Data")
with st.spinner("Fetching data from yfinance..."):
    df = fetch_stock_data(NIFTY_BATCH)

st.dataframe(df.style.highlight_max(axis=0, subset=["ROE (%)"]), use_container_width=True)

# 2. Hard Financial Filtering Rule (Scaffolding for LLM)
st.subheader("🎯 Step 2: Algorithmic Ranking")
# Filter for Quality: ROE > 15% and Debt/Equity < 1.5
filtered_df = df[(df["ROE (%)"] > 15) & (df["Debt/Equity"] < 150)].copy() if not df.empty else df
st.write(f"Filtered down to **{len(filtered_df)}** fundamentally strong stocks for LLM Review.")

# 3. Groq LLM Decision Agent
st.subheader("🤖 Step 3: Groq AI Deep Analysis")

if not client:
    st.error("Please set your GROQ_API_KEY in Render environment variables or script.")
else:
    if st.button("Run Groq AI Allocation Picker"):
        # Convert filtered data to markdown table for LLM to ingest cleanly
        data_payload = filtered_df.to_markdown(index=False)
        
        system_prompt = (
            "You are an expert SEBI-registered portfolio manager analyzing Indian equities. "
            "Evaluate the provided fundamental table. Pick the top 2 outperforming stocks based on value (P/E, P/B) "
            "and efficiency (ROE, Free Cash Flow). Provide a crisp investment thesis for each choice."
        )
        
        with st.spinner("Groq LLM is crunching the metrics..."):
            try:
                completion = client.chat.completions.create(
                    model="llama3-70b-8192",  # Using the powerful 70B model for deep financial reasoning
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Here is the data:\n\n{data_payload}"}
                    ],
                    temperature=0.2, # Low temperature for accurate, non-hallucinated data analysis
                )
                
                st.success("Analysis Complete!")
                st.markdown(completion.choices[0].message.content)
                
            except Exception as e:
                st.error(f"Groq API Error: {str(e)}")
