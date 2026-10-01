import yfinance as yf
from groq import Groq

# 1. Fetch live technical & fundamental data using Python
tickers = ["SBIN.NS", "RELIANCE.NS", "INFY.NS"]
combined_stock_data = ""

print("Fetching live market metrics from Yahoo Finance...")
for ticker in tickers:
    stock = yf.Ticker(ticker)
    info = stock.info
    
    # Extract messy unstructured data variables
    name = info.get('longName', ticker)
    price = info.get('currentPrice', 'N/A')
    pe = info.get('trailingPE', 'N/A')
    forward_pe = info.get('forwardPE', 'N/A')
    debt_to_equity = info.get('debtToEquity', 'N/A')
    profit_margin = info.get('profitMargins', 'N/A')
    revenue_growth = info.get('revenueGrowth', 'N/A')
    
    # Construct a raw text dossier for Groq to read
    combined_stock_data += f"""
    === STOCK: {name} ({ticker}) ===
    Current Price: INR {price}
    P/E Ratio: {pe} | Forward P/E: {forward_pe}
    Debt to Equity Ratio: {debt_to_equity}
    Profit Margin: {profit_margin}
    Revenue Growth (YoY): {revenue_growth}
    --------------------------------------------------
    """

# 2. Hand over the data to the Groq LLM brain for critical analysis
client = Groq()

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

# Call our active open-source model
completion = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.2 # Low temperature for accurate data-driven thinking
)

print("\n=== AI INVESTMENT INVESTMENT REPORT ===\n")
# FIX: Added [0] to correctly extract the response from the list
print(completion.choices[0].message.content)
