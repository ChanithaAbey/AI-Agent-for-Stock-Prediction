import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
from news_module import NewsAgent
from typing import List, Dict, Optional
from dotenv import load_dotenv
import requests
import os
import matplotlib.pyplot as plt

load_dotenv()

import os

key = os.getenv("GROQ_API_KEY")


TICKER_TO_COMPANY = {
    "MSFT": "Microsoft Corporation",
    "AAPL": "Apple Inc.",
    "GOOGL": "Alphabet Inc.",
    "AMZN": "Amazon.com, Inc.",
    "TSLA": "Tesla, Inc.",
    "META": "Meta Platforms, Inc."
}

def fetch_stock_data(ticker_symbol, start_date=None, end_date=None):
    try:
        if not ticker_symbol or not isinstance(ticker_symbol, str):
            print("Error: Invalid ticker symbol provided.")
            return None
        
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(start=start_date, end=end_date)

        if df.empty:
            print(f"Error: No stock data found for '{ticker_symbol}'.")
            return None
        df = df.reset_index()

        if 'Date' not in df.columns or 'Close' not in df.columns:
            print("Error: Unexpected data format from yfinance.")
            return None
        
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        df = df.round(2)
        return df
    
    except Exception as e:
        print(f"Error fetching stock data for {ticker_symbol}: {str(e)}")
        return None

def analyze_stock_price(csv_file_name, company_name):
    try:
        csv_data = pd.read_csv(csv_file_name)
        if csv_data.empty:
            print("Error: Analysis failed because the CSV data is empty.")
            return None
        
        csv_head = csv_data.head(10).to_string()
        csv_tail = csv_data.tail(10).to_string()
        stats = csv_data.describe().to_string()
        csv_string = f"Statistics:\n{stats}\n\nFirst 10 rows:\n{csv_head}\n\nLast 10 rows:\n{csv_tail}"

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama3-70b-8192",  # Or another Groq-supported model if desired
            "temperature": 0.7,
            "messages": [
                {
                    "role": "system",
                    "content": "Assume the role of an expert financial analyst and advisor."
                },
                {
                    "role": "user",
                    "content": f"""Please analyze the data of the company {company_name}, find out stock trends when it was higher when it was lower:\n{csv_string}.
                                Provide a detailed analysis of how the stock's price has changed over the time period, and identify any relevant news or events that may have influenced these trends.
                                At the end, write a short summary of the overall stock performance.

                                Then, for each week (for traders, first 4 weeks) and each month (for investors, next 10 months), recommend whether an investor should Buy, Sell, or Hold the stock. 
                                List each recommendation with a brief reasoning.

                                **Format your response in clear plain text. Use simple section headings written as plain text (for example: Stock Performance Analysis, News and Events, Recommendations), but do not use any markdown, bold, italics, bullet points, or special characters. Do not add extra spacing or decorations. The output should be directly suitable for a terminal (CLI) display.**

                                Example structure:
                                Stock Performance Analysis
                                [Your analysis here]

                                News and Events
                                [Your news analysis here]

                                Volatility Analysis
                                [Your news analysis here]

                                Volume Trends
                                [Your news analysis here]

                                Support and Resistance Levels               
                                [Your news analysis here]

                                Technical Indicators
                                [Your analysis here]

                                Comparative Performance
                                [Your analysis here]

                                Dividend History
                                [Your analysis here]

                                Risk Factors
                                [Your analysis here]

                                Recommendations

                                For Traders (Weekly):
                                1st Week: [Buy/Sell/Hold] - [Reason]
                                2nd Week: [Buy/Sell/Hold] - [Reason]
                                ...
                                4th Week: [Buy/Sell/Hold] - [Reason]

                                For Investors (Monthly):
                                1st Month: [Buy/Sell/Hold] - [Reason]
                                2nd Month: [Buy/Sell/Hold] - [Reason]
                                ...
                                10th Month: [Buy/Sell/Hold] - [Reason]

                                Summary
                                [Final summary here]
                                """
                }
            ]
        }
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        if response.status_code != 200:
            print(f"Groq API returned status code {response.status_code}: {response.text}")
            return None
        
        content = response.json()['choices'][0]['message']['content'].strip()
        return content
    
    except Exception as e:
        print(f"An error occurred during analysis: {e}")
        return None

def plot_stock_data(stock_data, ticker, company_name):
    try:
        if stock_data is None or stock_data.empty:
            print("No data available to plot.")
            return
        plt.figure(figsize=(12, 6))
        plt.plot(stock_data['Date'], stock_data['Close'], label='Closing Price', linewidth=2)
        plt.title(f"{company_name} ({ticker}) Stock Closing Price - Past Year")
        plt.xlabel("Date")
        plt.ylabel("Closing Price (USD)")
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"Error displaying the stock performance graph: {e}")

if __name__ == "__main__":
    try:
        ticker = input("Enter stock ticker symbol: ").strip().upper()
        if not ticker:
            print("No ticker entered. Exiting.")
            exit()
        company_name = TICKER_TO_COMPANY.get(ticker, ticker.capitalize())

        stock_data = fetch_stock_data(ticker)
        if stock_data is None:
            print("Could not retrieve stock data. Exiting.")
            exit()
        hf = NewsAgent()

        try:
            row_with_max_value = stock_data.loc[stock_data['High'].idxmax()]
            print("\nHighest price details:")
            print(row_with_max_value)
            try:
                result = hf.get_news(date_str=row_with_max_value['Date'], category="business, tech", search_str=company_name)
                rows = result.get('data', [])
                print(f"\nNews for {row_with_max_value['Date']}")
                if rows:
                    for row in rows:
                        print(row.get('title', '-'))
                else:
                    print("No news found for this date.")
            except Exception as e:
                print(f"Error fetching news for highest price: {e}")
        except Exception as e:
            print(f"Error processing highest price details: {e}")

        try:
            row_with_min_value = stock_data.loc[stock_data['Low'].idxmin()]
            print("\n\nLowest price details:")
            print(row_with_min_value)
            try:
                result = hf.get_news(date_str=row_with_min_value['Date'], category="business, tech", search_str=company_name)
                rows = result.get('data', [])
                print(f"\nNews for {row_with_min_value['Date']}")
                if rows:
                    for row in rows:
                        print(row.get('title', '-'))
                else:
                    print("No news found for this date.")
            except Exception as e:
                print(f"Error fetching news for lowest price: {e}")
        except Exception as e:
            print(f"Error processing lowest price details: {e}")

        print(f"\n\nStock data for {ticker}:")
        print(stock_data.head())

        csv_filename = f"{ticker}_stock_data.csv"
        try:
            stock_data.to_csv(csv_filename, index=False)
            print(f"Data saved to {csv_filename}\n")
        except Exception as e:
            print(f"Error saving CSV: {e}")

        try:
            response = analyze_stock_price(csv_filename, company_name)
            if response:
                print(f"\n{response}")
            else:
                print("No analysis available.")
        except Exception as e:
            print(f"Analysis step failed: {e}")

        # Plotting step
        plot_stock_data(stock_data, ticker, company_name)

    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting gracefully.")
    except Exception as e:
        print(f"Fatal error: {e}")
