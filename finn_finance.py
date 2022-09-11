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

### CANDLE STICK GRAPH ###

def candle_stick(data,name):

    data.index.name = 'date'
    mpf.plot(data,type='candle', mav=(10, 20), volume=True, style='charles', title=name)

### ACCOUNT MONITORING ###

class crypto_account:

    def __init__(self,transactions):
        self.transactions = transactions
        self.sub_coin = [['BTC/USD',100000000],['ETH/USD',pow(10,18)]]

    def filter_crypto_transactions(self,ticker='All'):

        transactions = []

        def to_array(transact):
            timestamp = pd.Timestamp(transact['Timestamp'][i])
            timestamp.strftime('%Y-%m-%d')
            return [self.transactions['Asset'][i]+'/'+transact['Spot Price Currency'][i],transact['Spot Price at Transaction'][i],timestamp.strftime('%Y-%m-%d'),transact['Subtotal'][i],transact['Transaction Type'][i]]
        
        for i in range(len(self.transactions)):
            if ticker == self.transactions['Asset'][i]+'/'+self.transactions['Spot Price Currency'][i]:
                transactions.append(to_array(self.transactions))
            elif ticker == 'All':
                transactions.append(to_array(self.transactions))
        
        return transactions

    def crypto_dollar_value(self,ticker='All'):
        # Set variables.
        coin_owned  = 0
        df = 0
        today = date.today()
        get_today = today.strftime("%Y-%m-%d")

        # Get transactions.
        transactions = self.filter_crypto_transactions(ticker=ticker)
     
        # Filter transactions according to the ticker.
        for i in range(len(transactions)):
            for s in range(len(self.sub_coin)):
                if transactions[i][0] == self.sub_coin[s][0]:
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

            data_btc = fetch_daily_data(transactions[i][0])
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
        # Transaction data.
        transactions = self.filter_crypto_transactions()

        # Find Tickers in transactiond date.
        tickers = [transactions[i][0] for i in range(len(transactions))]
        tickers = list(dict.fromkeys(tickers))

        # Get date per each ticker.
        coin_accounts = []
        for t in tickers:
            coin_accounts.append(self.crypto_dollar_value(ticker=t))

        # Find account with most data.
        max_val = 0
        min_val = 0
        for c in range(len(coin_accounts)):
            if coin_accounts[max_val].shape[0] <=coin_accounts[c].shape[0]:
                max_val = c
            else:
                min_val = c
        
        # Account with most data to date will set the first for loop.
        index_eth = coin_accounts[max_val].index
        index_btc = coin_accounts[min_val].index

        # Sum data per timestamp and append to transactions array.
        transactions = []
        for e in index_eth:
            timestamp_e = pd.Timestamp(e)
            sum_of_date = [timestamp_e.strftime('%Y-%m-%d'),coin_accounts[1]['account_value']['close'][e]] # Set sum_of_date as the data for that day for the max_val account.
            for b in index_btc:
                timestamp_b = pd.Timestamp(b)
                if timestamp_b.strftime('%Y-%m-%d') == timestamp_e.strftime('%Y-%m-%d'): # If there is no data for the day in the other account move on.
                    sum_of_date = [timestamp_e.strftime('%Y-%m-%d'),coin_accounts[1]['account_value']['close'][e]+coin_accounts[0]['account_value']['close'][e]]
            transactions.append(sum_of_date)

        # Return data as dataframe.
        index = [i[0] for i in transactions]
        data = [i[1] for i in transactions]               
        return pd.DataFrame(data,index=index,columns=['close'])

### ACCOUNT PROJECTING ###