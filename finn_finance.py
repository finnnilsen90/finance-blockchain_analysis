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

### ACCOUNT MONITORING

class account_look:

    def __init__(self,transactions,ticker):
        self.transactions = transactions
        self.ticker = ticker
        self.sub_coin = [['BTC/USD',100000000],['ETH/USD',pow(10,18)]]

    def filter_transactions(self):

        transactions = []
        for i in range(len(self.transactions)):
            if self.ticker == self.transactions[i][0]:
                transactions.append(self.transactions[i])
        
        return transactions

    def account_holding(self):
        coin_owned  = 0
        df = 0
        today = date.today()
        get_today = today.strftime("%Y-%m-%d")

        transactions = self.filter_transactions()

        for i in range(len(transactions)):
            for s in range(len(self.sub_coin)):
                if self.ticker == self.sub_coin[s][0]:
                    sub_coin = self.sub_coin[s][1]

            buy_price = transactions[i][1]/sub_coin
            coin = transactions[i][3]/buy_price
            coin_owned = coin_owned + coin

            last_day = len(transactions) - 1
            if i == last_day:
                transaction_date_start = transactions[i][2]
                transaction_date_end = get_today
            else:
                j = i+1
                transaction_date_start = transactions[i][2]
                transaction_date_end = transactions[j][2]

            data_btc = fetch_daily_data(self.ticker)
            date_value = pd.read_csv(data_btc,index_col=['date'],parse_dates=True,usecols = ['date','close'],chunksize=1000)
            date_value = pd.concat((x.query("date >= %a and date < %a"%(transaction_date_start,transaction_date_end)) for x in date_value))
            date_value['value'] = coin_owned*(date_value['close']/sub_coin)
            date_value = date_value.sort_values(by='date')

            def account_value(close):
                return coin_owned*(close/sub_coin)
            pivot = pd.pivot_table(date_value, values=['close'], index=['date'],aggfunc=[account_value])
            
            if i == 0:
                df = pivot
            else:   
                df = pd.concat([df,pivot], ignore_index=False)
                
        return df

### BLOCKCHAIN FINANCE ####

def satoshi_price(btc):
    satoshi = btc/100000000
    return satoshi

def wei_price(eth):
    wei = eth/pow(10,18)
    return wei

