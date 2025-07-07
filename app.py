import base64
import io

import matplotlib.pyplot as plt
import yfinance
from flask import Flask, request, jsonify

app = Flask(__name__)

def analiz_yap(ticker):
    df = yfinance.download(ticker, period='3mo', interval='1d', auto_adjust=False)
    if df.empty:
        return {"error": "Veri bulunamadı."}

    # MACD hesaplama
    short_ema = df['Adj Close'].ewm(span=12, adjust=False).mean()
    long_ema = df['Adj Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = short_ema - long_ema
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # RSI hesaplama
    delta = df['Adj Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Al/Sat sinyali
    last = df.iloc[-1]
    macd = float(last['MACD'])
    signal_line = float(last['Signal'])
    rsi = float(last['RSI'])

    if macd > signal_line and rsi < 30:
        signal = 'BUY'
    elif macd < signal_line and rsi > 70:
        signal = 'SELL'
    else:
        signal = 'HOLD'

    # Grafik oluşturma
    fig, ax = plt.subplots(figsize=(10, 4))
    df['Adj Close'].plot(ax=ax, label='Fiyat')
    df['MACD'].plot(ax=ax, label='MACD')
    df['Signal'].plot(ax=ax, label='Signal')
    ax.set_title(f"{ticker} Fiyat + MACD")
    ax.legend()
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close()

    return {
        "ticker": ticker,
        "price": round(last['Adj Close'], 2),
        "signal": signal,
        "macd": round(macd, 2),
        "rsi": round(rsi, 2),
        "image_base64": image_base64
    }

@app.route('/analyze', methods=['GET'])
def analyze():
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({"error": "ticker parametresi eksik"}), 400

    result = analiz_yap(ticker)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5001)