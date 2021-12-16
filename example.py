import yfinance as yf
import bokeh_fin as bf

stock = "AAPL"

data = yf.download(stock, start="2021-01-01", end="2021-07-01")
data.reset_index(inplace=True)

bfp = bf.plot(stock, data)
bfp.show()