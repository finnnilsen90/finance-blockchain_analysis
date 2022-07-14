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

class crypto_account:

    def __init__(self,transactions):
        self.transactions = transactions
        self.sub_coin = [['BTC/USD',100000000],['ETH/USD',pow(10,18)]]

    def filter_crypto_transactions(self,ticker='All'):

        transactions = []
        for i in range(len(self.transactions)):
            if ticker == self.transactions['Asset'][i]+'/'+self.transactions['Spot Price Currency'][i]:
                timestamp = pd.Timestamp(self.transactions['Timestamp'][i])
                timestamp.strftime('%Y-%m-%d')
                transactions.append([self.transactions['Asset'][i]+'/'+self.transactions['Spot Price Currency'][i],self.transactions['Spot Price at Transaction'][i],timestamp.strftime('%Y-%m-%d'),self.transactions['Subtotal'][i],self.transactions['Transaction Type'][i]])
            elif ticker == 'All':
                transactions.append(self.transactions[i])
        
        return transactions

    def crypto_dollar_value(self,ticker='All'):
        coin_owned  = 0
        df = 0
        today = date.today()
        get_today = today.strftime("%Y-%m-%d")

        transactions = self.filter_crypto_transactions(ticker=ticker)

        for i in range(len(transactions)):
            for s in range(len(self.sub_coin)):
                if ticker == self.sub_coin[s][0]:
                    sub_coin = self.sub_coin[s][1]

            buy_price = transactions[i][1]/sub_coin
            coin = transactions[i][3]/buy_price

            if 'Buy' == transactions[i][4]:
                coin_owned = coin_owned + coin
            elif 'Sell' == transactions[i][4]:
                coin_owned = coin_owned - coin

            last_day = len(transactions) - 1
            if i == last_day:
                transaction_date_start = transactions[i][2]
                transaction_date_end = get_today
            else:
                j = i+1
                transaction_date_start = transactions[i][2]
                transaction_date_end = transactions[j][2]

            data_btc = fetch_daily_data(ticker)
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

    def total_value(self):
        transactions = self.filter_crypto_transactions()
        tickers = [transactions[i][0] for i in range(len(transactions))]
        tickers = list(dict.fromkeys(tickers))
        df = 0

        # pivot = self.crypto_dollar_value(ticker='ETH/USD')

        for i in range(len(tickers)):
            pivot = self.crypto_dollar_value(ticker=tickers[i])
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

### ACCOUNT PROJECTING ###

# Calculate satoshi bit coin

# def satoshi_price(btc):
#     satoshi = btc/100000000
#     return satoshi

# bitcoin_price = [46726.59,38000.00,35000.00,30000.00]
# bitcoin_sell_price = [70000.00,70000,70000,70000]
# investment = [100,200,300,300]

# satoshi_owned  = 0

# for i in range(len(investment)):
#     satoshi_buy_price = satoshi_price(bitcoin_price[i])
#     satoshi = investment[i]/satoshi_buy_price
    
#     satoshi_owned = satoshi_owned + satoshi
    
#     print('')
#     print('Investment '+str(i+1))
#     print('Satoshi Buy Price: $'+str(satoshi_buy_price))
#     print('Investment: $'+str(investment[i]))
#     print('Satoshi: '+str(satoshi))

#     satoshi_sell_price = satoshi_price(bitcoin_sell_price[i])
#     value = satoshi_sell_price*satoshi
#     print('Satoshi Sell Price: $'+str(satoshi_sell_price))
#     print('Value: $'+str(value))
#     print('Net: $'+str(value-investment[i]))

# def wei_price(eth):
#     wei = eth/pow(10,18)
#     return wei

# ethereum_price = [3525.92,2300.00,2100.00]
# ethereum_sell_price = [4800.00,4800.00,4800.00]
# investment = [100,300,300]

# for i in range(len(investment)):
#     ethereum_buy_price = wei_price(ethereum_price[i])
#     wei = investment[i]/ethereum_buy_price
    
#     print('')
#     print('Investment '+str(i+1))
#     print('Wei Buy Price: $'+str(ethereum_buy_price))
#     print('Investment: $'+str(investment[i]))
#     print('Wei: '+str(wei))
    
#     wei_sell_price = wei_price(ethereum_sell_price[i])
#     value = wei_sell_price*wei
#     print('Wei Sell Price: $'+str(wei_sell_price))
#     print('Value: $'+str(value))
#     print('Net: $'+str(value-investment[i]))

# # Pivot by monthly high and low
# # Generate BTC CSV.
# data = f.fetch_daily_data(ticker_crypto[0])
# df = pd.read_csv(data)

# df['month'] = pd.to_datetime(df['date']).dt.strftime('%B') # make a month column to preserve the order
# df['year'] = pd.to_datetime(df['date']).dt.strftime('%Y') # make a month column to preserve the order
# pivot = pd.pivot_table(df, values=['high','low'], index=['month','year','ticker'],aggfunc=np.average)
# pivot = pivot.sort_values(by=['month','year'], ascending = [True, True])
# pivot