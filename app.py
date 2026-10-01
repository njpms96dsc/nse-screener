import streamlit as st
import yfinance as yf
from groq import Groq

st.set_page_config(page_title="Simple AI Stock Screener", page_icon="📈")

st.title("📈 Barebones AI Stock Screener")
st.write("Fetch key stock metrics with `yfinance` and let **Groq AI** pick the best stock.")

# --- Sidebar ---
st.sidebar.header("🔑 API Credentials")
api_key = st.sidebar.text_input("Enter Groq API Key", type="password")

# --- Stock Inputs ---
symbols_input = st.text_input("Stock Tickers (comma separated):", value="RELIANCE.NS, SBIN.NS, INFY.NS")

if st.button("Run Fundamental Analysis 🚀"):
    if not api_key:
        st.error("Please provide your Groq API key in the sidebar!")
    else:
        # Split tickers into list
        tickers = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
        
        st.subheader("📊 Stock Data Extracted")
        dossier = ""
        
        with st.spinner("Fetching data from Yahoo Finance..."):
            for ticker in tickers:
                try:
                    # Fetch fundamentals using yfinance
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    
                    # Extract target metrics safely
                    price = info.get("currentPrice", info.get("regularMarketPrice", "N/A"))
                    pe = info.get("trailingPE", "N/A")
                    roe = info.get("returnOnEquity", "N/A")
                    pb = info.get("priceToBook", "N/A")
                    
                    # Convert ROE to percentage format if numeric
                    if isinstance(roe, (int, float)):
                        roe = f"{roe * 100:.2f}%"
                    
                    st.write(f"**{ticker}**: Price = `INR {price}` | P/E = `{pe}` | ROE = `{roe}` | P/BV = `{pb}`")
                    
                    dossier += f"""
=== Stock: {ticker} ===
Price: INR {price}
P/E Ratio: {pe}
Return on Equity (ROE): {roe}
Price-to-Book (P/BV): {pb}
-----------------------
"""
                except Exception as e:
                    st.error(f"Error fetching data for {ticker}: {e}")

        if dossier:
            st.divider()
            st.subheader("🤖 AI CIO Analysis")
            with st.spinner("Asking Groq AI to evaluate..."):
                try:
                    client = Groq(api_key=api_key.strip())
                    
                    # Dynamically query available models to prevent 404 model_not_found errors
                    models_res = client.models.list()
                    available_models = [m.id for m in models_res.data]
                    
                    # Pick the best available text model for your key
                    selected_model = "llama-3.1-8b-instant"
                    for preferred in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "openai/gpt-oss-20b", "mixtral-8x7b-32768"]:
                        if preferred in available_models:
                            selected_model = preferred
                            break
                    
                    prompt = f"""You are a Chief Investment Officer at a quantitative hedge fund. Analyze the following fundamentals for these stocks and pick the single BEST buy for medium-term holding.

Stock Data:
{dossier}

Respond in this exact structure:
1. THE WINNER: [Stock Name]
2. CORE THESIS: [Clear reason why its P/E, ROE, and P/BV make it the best choice]
3. KEY RISK: [Main vulnerability or trap]"""

                    response = client.chat.completions.create(
                        model=selected_model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.2
                    )
                    
                    st.info(f"Analyzed using active model: **{selected_model}**")
                    st.markdown(response.choices[0].message.content)
                    
                except Exception as e:
                    st.error(f"Groq API Error: {str(e)}")
