import streamlit as st
import pandas as pd
import yfinance as yf
from groq import Groq

st.set_page_config(page_title="Hedge Fund Stock Screener", layout="wide")
st.title("📊 AI-Powered NSE Stock Screener & Analyst")
st.write("Upload your standard NSE CSV file, scan the metrics, and pass them to the Groq LLM brain for target analysis.")

st.sidebar.header("🔑 Credentials & Settings")
groq_api_key = st.sidebar.text_input("Groq API Key", type="password", help="Enter your Groq Cloud API Key")
selected_model = st.sidebar.selectbox("LLM Brain", ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768"])

uploaded_file = st.file_uploader("Upload your NSE Screener CSV (e.g., niftymicrocap250.csv)", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        
        if len(df.columns) < 3:
            st.error("The uploaded CSV has fewer than 3 columns. Please upload a standard NSE formatted file.")
            st.stop()
            
        symbol_col_name = df.columns[2]
        st.success(f"Successfully loaded CSV! Identified Symbol Column: '**{symbol_col_name}**'")
        
        raw_symbols = df[symbol_col_name].dropna().astype(str).str.strip().str.upper().unique().tolist()
        formatted_tickers = [sym if sym.endswith('.NS') else f"{sym}.NS" for sym in raw_symbols if sym]
        
        st.write(f"Total Unique Tickers Discovered: **{len(formatted_tickers)}**")
        
        st.subheader("🎯 Step 1: Select Stocks for AI Analysis")
        st.info("To avoid API rate limits and keep context clean, select up to 3 stocks from your file to analyze.")
        
        selected_tickers = st.multiselect(
            "Choose exactly 3 stocks to compare:",
            options=formatted_tickers,
            default=formatted_tickers[:min(3, len(formatted_tickers))]
        )
        
        if len(selected_tickers) != 3:
            st.warning("⚠️ Please select exactly 3 stocks to match the quantitative model criteria.")
        else:
            if st.button("Run Financial Deep-Dive 🚀"):
                combined_stock_data = ""
                progress_bar = st.progress(0)
                
                with st.spinner("Fetching live market metrics from Yahoo Finance..."):
                    for idx, ticker in enumerate(selected_tickers):
                        try:
                            stock = yf.Ticker(ticker)
                            info = stock.info
                            
                            name = info.get('longName', ticker)
                            price = info.get('currentPrice', 'N/A')
                            pe = info.get('trailingPE', 'N/A')
                            forward_pe = info.get('forwardPE', 'N/A')
                            debt_to_equity = info.get('debtToEquity', 'N/A')
                            profit_margin = info.get('profitMargins', 'N/A')
                            revenue_growth = info.get('revenueGrowth', 'N/A')
                            
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
                    with st.spinner("Handing over the data to the Groq LLM brain..."):
                        try:
                            client = Groq(api_key=groq_api_key)
                            
                            prompt = f"""
                            You are the Chief Investment Officer of a quantitative hedge fund. 
                            Analyze the raw financial data of these 3 Indian stocks and pick exactly ONE absolute "Best Buy" for a medium-term investment.

                            Here is the raw stock data:
                            {combined_stock_data}

                            Provide your final analysis structured exactly like this:
                            1. THE WINNER: [Stock Name]
                            2. CORE INVESTMENT THESIS: [Explain exactly why its numbers beat the other two in plain English]
                            3. THE CRITICAL RISK: [The single biggest flaw or hidden trap in this winner's data]
                            """
                            
                            completion = client.chat.completions.create(
                                model=selected_model,
                                messages=[{"role": "user", "content": prompt}],
                                temperature=0.2
                            )
                            
                            st.subheader("🏆 AI Chief Investment Officer Report")
                            st.markdown(completion.choices[0].message.content)
                            
                        except Exception as e:
                            st.error(f"Groq API Error: {str(e)}")
                            
    except Exception as e:
        st.error(f"Error reading the file structure: {str(e)}")

else:
    st.info("💡 Drop an active NSE CSV file above to begin the quantitative analysis pipeline.")
