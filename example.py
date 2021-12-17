import yfinance as yf
import bokeh_fin as bf
import pandas as pd
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

stock = "AAPL"

# load from yfinance
# data = yf.download(stock, start="2021-01-01", end="2021-07-01")
# data.reset_index(inplace=True)

# load from csv
data = pd.read_csv('AAPL.csv')
data['Date'] = pd.to_datetime(data['Date'])
data['EMA9'] = EMAIndicator(
        close=data['Close'], window=9).ema_indicator()
data['EMA12'] = EMAIndicator(
        close=data['Close'], window=12).ema_indicator()
data['RSI'] = RSIIndicator(close=data['Close'], window=14).rsi()

addplot = [dict(
    column='EMA9',
    kind='line',
    color='red',
), dict(
    column='EMA12',
    kind='scatter',
    color='blue'
)]

subplot = [dict(
    column='RSI',
    kind='line',
)]


bfp = bf.plot(stock, data, addplot=addplot)
bfp.add_subplot(subplot)
bfp.show()