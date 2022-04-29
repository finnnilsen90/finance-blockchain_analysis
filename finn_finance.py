import requests
import pandas as pd
import numpy as np
from datetime import date
from matplotlib import pyplot
import mplfinance as mpf
import datetime
import json
import matplotlib.dates as mpl_dates

### GET DATA ###

def fetch_daily_data(symbol):
    pair_split = symbol.split('/')  # symbol must be in format XXX/XXX ie. BTC/EUR
    symbol = pair_split[0] + '-' + pair_split[1]
    url = f'https://api.pro.coinbase.com/products/{symbol}/candles?granularity=86400'
    response = requests.get(url)
    today = date.today()
    get_date = today.strftime("%Y-%m-%d")
    file = f'data/Coinbase_{pair_split[0] + pair_split[1]}_'+get_date+'.csv'
    if response.status_code == 200:  # check to make sure the response from server is good
        data = pd.DataFrame(json.loads(response.text), columns=['unix', 'low', 'high', 'open', 'close', 'volume'])
        data['date'] = pd.to_datetime(data['unix'], unit='s')  # convert to a readable date
        data['vol_fiat'] = data['volume'] * data['close']      # multiply the BTC volume by closing price to approximate fiat volume
        data['month'] = pd.to_datetime(data['date']).dt.strftime('%B') + ' ' + pd.to_datetime(data['date']).dt.strftime('%Y')
        data['ticker'] = symbol

    # if we failed to get any data, print an error...otherwise write the file
        if data is None:
            print("Did not return any data from Coinbase for this symbol")
        else:
            data.to_csv(file, index=False)
    else:
        print("Did not receieve OK response from Coinbase API")
        
    return file

### CANDLE STICK GRAPH

def candle_stick(data,name):

    data.index.name = 'date'
    mpf.plot(data,type='candle', mav=(10, 20), volume=True, style='charles', title=name)

### BLOCKCHAIN FINANCE ####

def satoshi_price(btc):
    satoshi = btc/100000000
    return satoshi

def wei_price(eth):
    wei = eth/pow(10,18)
    return wei

### OTHER GRAPHS NOT CURRENTLY USED ###

def line_chart(data):
    series = pd.read_csv(data, usecols=['date','close'])
    series.sort_values(by = 'date', ascending = True, inplace = True)
    pyplot.rcParams["figure.figsize"] = [12, 3.50]

    # pyplot.figure(figsize=(50,0))
    series.set_index('date').plot()
    # series.show()

def bar_graph(data):
    date_series = pd.read_csv(data, usecols=['month']).values.tolist()
    date_series = [date_series[i][0] for i in range(len(date_series))]
    date_series = date_series[::-1] # reverse date order.
    high_series  = pd.read_csv(data, usecols=['high']).values.tolist()
    high_series = [high_series[i][0] for i in range(len(high_series))]
    close_series  = pd.read_csv(data, usecols=['close']).values.tolist()
    close_series = [close_series[i][0] for i in range(len(close_series))]

    date_series
    pyplot.bar(date_series, high_series)
    pyplot.rcParams["figure.figsize"] = [25, 10]
    # pyplot.bar(date_series, close_series)
    pyplot.show()

