from flask import Flask, render_template, jsonify
import requests
import pandas as pd
import random
import time

app = Flask(__name__)
app.config["DEBUG"] = True  # Enable debugging

# Store messages in a list instead of sending to Telegram
messages = []

# Fetch option chain data from NSE with error handling
def fetch_banknifty_option_chain(symbol):
    try:
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
        headers = {"User-Agent": "Mozilla/5.0"}

        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers)  # Initial request
        time.sleep(3)  # Add delay to prevent blocking

        response = session.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"Error: NSE API returned {response.status_code}")
            return None, None

        data = response.json()
        records = data["records"]
        spot_price = records["underlyingValue"]
        options = []

        for record in records["data"]:
            for option_type in ["CE", "PE"]:
                if option_type in record:
                    options.append({
                        "Strike Price": record["strikePrice"],
                        "Type": option_type,
                        "Last Price": record[option_type]["lastPrice"],
                        "Open Interest": record[option_type]["openInterest"],
                        "Volume": record[option_type]["totalTradedVolume"],
                    })
        
        return pd.DataFrame(options), spot_price

    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        return None, None

# Get Bank Nifty Trend (Dummy Logic)
def get_banknifty_trend():
    return random.choice(["BULLISH", "BEARISH", "NEUTRAL"])

# Generate Trading Signals
def generate_signals(data, spot_price):
    try:
        trend = get_banknifty_trend()

        if trend == "NEUTRAL":
            return []

        nearest_strike = round(spot_price / 100) * 100
        selected_strikes = [nearest_strike - 200, nearest_strike - 100, nearest_strike, nearest_strike + 100, nearest_strike + 200]

        option_type = "CE" if trend == "BULLISH" else "PE"
        new_messages = []

        for strike in selected_strikes:
            selected_option = data[(data["Strike Price"] == strike) & (data["Type"] == option_type)]

            if selected_option.empty:
                continue

            last_price = selected_option["Last Price"].iloc[0]
            open_interest = selected_option["Open Interest"].iloc[0]
            volume = selected_option["Volume"].iloc[0]

            if volume > 100000 and open_interest > 10000 and last_price > 100:
                signal = "BUY"
                stop_loss = round(last_price * 0.90, 2)
                target_price = round(last_price * 1.15, 2)
            else:
                continue

            message = f"""
            🔔 <b>Bank Nifty Option Signal Alert</b> 🔔<br>
            📊 <b>Strike Price:</b> {strike}<br>
            🔵 <b>Option Type:</b> {option_type}<br>
            💰 <b>Last Price:</b> ₹{last_price}<br>
            📉 <b>Open Interest:</b> {open_interest}<br>
            🔄 <b>Volume:</b> {volume}<br>
            📍 <b>Signal:</b> <b>{signal}</b><br>
            🎯 <b>Stop Loss:</b> ₹{stop_loss}<br>
            🎯 <b>Target Price:</b> ₹{target_price}<br>
            📢 <b>Advice:</b> Follow the signal with proper risk management.<br>
            """
            new_messages.append(message)

        messages.extend(new_messages)  # Store messages in global list
        return new_messages

    except Exception as e:
        print(f"Error generating signals: {str(e)}")
        return []

# Web Route to Fetch Signals
@app.route('/get-signals', methods=['GET'])
def get_signals():
    symbol = "BANKNIFTY"
    option_data, spot_price = fetch_banknifty_option_chain(symbol)

    if option_data is None:
        return jsonify({"error": "Failed to fetch NSE data"}), 500

    new_signals = generate_signals(option_data, spot_price)
    return jsonify({"signals": new_signals})

# Web Route to Display Messages
@app.route('/')
def home():
    return render_template('index.html', messages=messages or ["No signals yet!"])

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
