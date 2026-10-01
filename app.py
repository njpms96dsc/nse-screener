import streamlit as st
import io
import csv
import requests
from groq import Groq

# Set up clean mobile-optimized page layout
st.set_page_config(page_title="AI Fundamental Screener", layout="wide")
st.title("📊 AI-Powered Fundamental NSE Stock Screener")

# --- Sidebar Configuration ---
st.sidebar.header("🔑 Credentials & Settings")
groq_api_key = st.sidebar.text_input("Groq API Key", type="password", help="Enter your Groq Cloud API Key")
selected_model = st.sidebar.selectbox("LLM Brain", ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"])

st.subheader("📁 Step 1: Provide Your Tickers")
input_method = st.radio("Choose how to input your stocklist:", ["Upload CSV File", "Paste Symbols Text Box"])

raw_symbols = []

if input_method == "Upload CSV File":
    uploaded_file = st.file_uploader("Upload your stock list file:", type=None)
    
    if uploaded_file is not None:
        try:
            bytes_data = uploaded_file.getvalue()
            text_data = bytes_data.decode("utf-8", errors="ignore")
            reader = csv.reader(io.StringIO(text_data))
            
            for row in reader:
                if len(row) >= 3:
                    symbol = row[2].strip().replace('"', '')
                    if symbol and symbol.lower() not in ['symbol', 'ticker', 'name']:
                        raw_symbols.append(symbol)
            
            raw_symbols = list(set(raw_symbols))
            if raw_symbols:
                st.success(f"Successfully loaded file! Extracted **{len(raw_symbols)}** symbols from the 3rd column.")
            else:
                st.error("Could not find any symbols in the 3rd column of this file.")
        except Exception as e:
            st.error(f"Error reading file structure: {str(e)}")
else:
    text_input = st.text_area("Paste your stock symbols here (separated by commas or spaces):", value="SBIN, RELIANCE, INFY")
    if text_input:
        raw_symbols = list(set([sym.strip().upper() for sym in text_input.replace(",", " ").split() if sym.strip()]))

if raw_symbols:
    formatted_tickers = [sym if sym.endswith('.NS') else f"{sym}.NS" for sym in raw_symbols if sym]
    st.write(f"Total Unique Tickers Discovered: **{len(formatted_tickers)}**")
    
    st.subheader("🎯 Step 2: Select Stocks for AI Analysis")
    selected_tickers = st.multiselect("Choose stocks to compare:", options=formatted_tickers, default=formatted_tickers[:min(3, len(formatted_tickers))])
    
    if not selected_tickers:
        st.warning("⚠️ Please select at least one stock to analyze.")
    else:
        if st.button("Run Financial Deep-Dive 🚀"):
            combined_stock_data = ""
            progress_bar = st.progress(0)
            
            # Pydroid network signature to bypass institutional cloud server blocks
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            with st.spinner("Fetching full fundamental modules via API Backend..."):
                for idx, ticker in enumerate(selected_tickers):
                    try:
                        # Pulling summary modules directly to retrieve fundamental metrics securely
                        url = f"https://yahoo.com{ticker}?modules=summaryDetail,financialData,price"
                        response = requests.get(url, headers=headers, timeout=10)
                        
                        name = ticker
                        price = "N/A"
                        pe = "N/A"
                        forward_pe = "N/A"
                        debt_to_equity = "N/A"
                        profit_margin = "N/A"
                        revenue_growth = "N/A"
                        
                        if response.status_code == 200:
                            data = response.json()
                            modules_list = data.get('quoteSummary', {}).get('result', [])
                            
                            if modules_list:
                                result = modules_list[0]
                                price_module = result.get('price', {})
                                summary_module = result.get('summaryDetail', {})
                                financial_module = result.get('financialData', {})
                                
                                name = price_module.get('longName', ticker)
                                price = financial_module.get('currentPrice', {}).get('raw', 'N/A')
                                pe = summary_module.get('trailingPE', {}).get('raw', 'N/A')
                                forward_pe = summary_module.get('forwardPE', {}).get('raw', 'N/A')
                                debt_to_equity = financial_module.get('debtToEquity', {}).get('raw', 'N/A')
                                profit_margin = financial_module.get('profitMargins', {}).get('raw', 'N/A')
                                revenue_growth = financial_module.get('revenueGrowth', {}).get('raw', 'N/A')
                        
                        combined_stock_data += f"""
                        === STOCK: {name} ({ticker}) ===
                        Current Price: INR {price}
                        P/E Ratio: {pe} | Forward P/E: {forward_pe}
                        Debt to Equity Ratio: {debt_to_equity}
                        Profit Margin: {profit_margin}
                        Revenue Growth (YoY): {revenue_growth}
                        --------------------------------------------------
                        """
                    except Exception as e:
                        st.error(f"Error fetching data for {ticker}: {str(e)}")
                    progress_bar.progress((idx + 1) / len(selected_tickers))
            
            with st.expander("🔍 View Raw Extracted Dossier"):
                st.text(combined_stock_data)
            
            if not groq_api_key:
                st.error("🔑 Please provide a valid Groq API Key in the sidebar to run the AI Analysis.")
            else:
                with st.spinner("Handing data over to the Groq LLM brain for valuation vetting..."):
                    try:
                        client = Groq(api_key=groq_api_key)
                        prompt = f"""You are the Chief Investment Officer of a quantitative hedge fund. Analyze the raw financial data of these stocks and pick exactly ONE absolute "Best Buy" for a medium-term investment.\n\nHere is the raw stock data:\n{combined_stock_data}\n\nProvide your final analysis structured exactly like this:\n1. THE WINNER: [Stock Name]\n2. CORE INVESTMENT THESIS: [Explain exactly why its valuation and fundamental numbers beat the others in plain English]\n3. THE CRITICAL RISK: [The single biggest flaw or hidden trap in this winner's data]"""
                        
                        completion = client.chat.completions.create(model=selected_model, messages=[{"role": "user", "content": prompt}], temperature=0.2)
                        st.subheader("🏆 AI Chief Investment Officer Report")
                        st.markdown(completion.choices[0].message.content)
                    except Exception as e:
                        st.error(f"Groq API Error: {str(e)}")
else:
    st.info("💡 Provide a valid file or paste symbols above to begin the quantitative analysis pipeline.")
