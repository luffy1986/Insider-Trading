#!/usr/local/bin/python3

import os
import argparse
import multiprocessing
from multiprocessing import Pool
from multiprocessing import Process 
from multiprocessing import Queue
import re
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import pandas_datareader.data as web
import requests
import datetime
import xlrd
import sys
import yahoo_fin.stock_info as si
from functools import partial
import yfinance as yf
from pytickersymbols import PyTickerSymbols
import matplotlib.pyplot as plt
import numpy as np

def func(pct, allvalues): 
    absolute = int(pct / 100.*np.sum(allvalues)) 
    return "{:.1f}%\n({:d})".format(pct, absolute)

def return_calc(symbol, start, end):
    data = web.DataReader(symbol, 'yahoo', start, end)
    end_price = data['Adj Close'][-1]
    beg_price = data['Adj Close'][0]
    ret = round(((end_price/beg_price)-1)*100, 2)
    return ret

def todayDate():
    todayDate = datetime.datetime.now()
    return todayDate

def calculateDateFromGivenDate(diff):
    agoDate = (todayDate() - datetime.timedelta(days=diff)).date()
    return agoDate

def calculateAbsDiffBwDates(date1, date2):
    d1 = datetime.datetime.strptime(date1, "%Y-%m-%d")
    d2 = datetime.datetime.strptime(date2, "%Y-%m-%d")
    difference = abs(d1-d2).days
    return difference

def extractDate(date):
    return datetime.datetime(int(date[:4]),int(date[5:7]),int(date[8:]))

def calculateDiffBwDates(date1, date2):
    d1 = datetime.datetime.strptime(date1, "%Y-%m-%d")
    d2 = datetime.datetime.strptime(date2, "%Y-%m-%d")
    difference = (d1-d2).days
    return difference

def dateConversion(year, month, day):
    return datetime.date(year, month, day)
    
def calculateMarketValue(mktvalue):
        value = 0
        if re.search(r'K', mktvalue):
            value = mktvalue.split('K')
            value = int((float(value[0])) * 1000)
        elif re.search(r'M', mktvalue):
            value = mktvalue.split('M')
            value = int((float(value[0])) * 1000000)
        elif re.search(r'B', mktvalue):
            value = mktvalue.split('B')
            value = int((float(value[0])) * 1000000000)
        elif re.search(r'T', mktvalue):
            value = mktvalue.split('T')
            value = int((float(value[0])) * 1000000000000)
        else:
            print("Error we have a different denomination %s" %(mktvalue))
        return value 
    
def getCIKs(ticker):
    URL = 'https://www.sec.gov/cgi-bin/browse-edgar?CIK={}&Find=Search&owner=exclude&action=getcompany'
    CIK_RE = re.compile(r'.*CIK=(\d{10}).*')    
    cik_dict = {}
    f = requests.get(URL.format(ticker), stream = True)
    results = CIK_RE.findall(f.text)
    if len(results):
        results[0] = int(re.sub('\.[0]*', '.', results[0]))
        cik_dict[str(ticker).upper()] = str(results[0])
    #f = open('cik_dict', 'w')   
    #f.close(
    return results[0]
    
def tickerReNaming(ticker, type=0):

    newTicker=ticker
    if type == 0:
        if(re.search(r'\.', ticker)):
            breakUp=ticker.split(".")
            newTicker=breakUp[0]+"-"+breakUp[1]
            if (re.search(r'TSE', newTicker)):
                newTicker = newTicker.split(":")
                newTicker=newTicker[1]+".TO"
        elif(re.search(r'TSE', ticker)):
            breakUp = ticker.split(":")
            newTicker=breakUp[1]+".TO"
        elif(re.search(r'CURRENCY', ticker)):
            newTicker = "BTC-USD"
    elif type == 1:
        if re.search(r'BF.B', ticker):
            newTicker = "BFA"
        elif(re.search(r'\.', ticker)):
            breakUp=ticker.split(".")
            newTicker =breakUp[0]+"-"+breakUp[1]

    return newTicker

def to_soup(url):
    url_response = requests.get(url)
    webpage = url_response.content
    soup = BeautifulSoup(webpage, 'html.parser')
    return soup

def insider_trading_all(symbolList, endDate, sales, marketCap):
    symbols = []
    if isinstance(symbolList, list):
        symbols = symbolList
    else:
        symbols.append(symbolList)
    end = endDate
    start_yahoo = extractDate(end)
    end_yahoo = todayDate() 
    dfs = []
    with tqdm(total = len(symbols)) as pbar:
        for i in range(len(symbols)):
            try:
                lst = [symbols[i]]
                if not re.search(r"\$", lst[0]):
                    newTicker = tickerReNaming(lst[0], 0)
                else:
                    pbar.update(1)
                    continue
                cik = getCIKs(newTicker)
                quoteTable = si.get_quote_table(newTicker)
                avgVolume = quoteTable["Avg. Volume"]
                mktCap = quoteTable["Market Cap"]
                if mktCap != "nan":
                    value = calculateMarketValue(mktCap)
                else:
                    pbar.update(1)
                    continue
                if value < marketCap:
                    pbar.update(1)
                    continue

                page = 0
                beg_url = 'https://www.sec.gov/cgi-bin/own-disp?action=getissuer&CIK='+str(cik)+'&type=&dateb=&owner=include&start='+str(page*80)
                urls = [beg_url]
                df_data = []
                #noData = False
                for url in urls:
                    soup = to_soup(url)
                    transaction_report = soup.find('table', {'id':'transaction-report'})

                    t_chil = [i for i in transaction_report.children]
                    t_cont = [i for i in t_chil if i != '\n']

                    headers = [ i for i in t_cont[0].get_text().split('\n') if i != '']
                    data_rough = [i for lst in t_cont[1:] for i in lst.get_text().split('\n') if i != '' ]
                    data = [data_rough[i:i+12] for i in range(0,len(data_rough), 12)]
                    if data:
                        last_line = data[-1]
                    else:
                        noData = True
                    for i in data:
                        diff = calculateDiffBwDates(i[1], end)
                        if (diff < 0):
                            break
                        else:
                            if (i != last_line):
                                df_data.append(i)
                            else:
                                df_data.append(i)
                                page += 1
                                urls.append('https://www.sec.gov/cgi-bin/own-disp?action=getissuer&CIK='+str(cik)+'&type=&dateb=&owner=include&start='+str(page*80))

                #if noData == True:
                #    pbar.update(1)
                #    continue
                df = pd.DataFrame(df_data,columns = headers)
                df['Purch'] = pd.to_numeric(df['Transaction Type'].apply(lambda x: 1 if x == 'P-Purchase' else 0)
                               *df['Number of Securities Transacted'])
                df['Sale'] = pd.to_numeric(df['Transaction Type'].apply(lambda x: 1 if x == 'S-Sale' else 0)
                               *df['Number of Securities Transacted'])
                purch = df['Transaction Type'] == 'P-Purchase'
                sale = df['Transaction Type'] == 'S-Sale'
                num_purch = len(df[purch])
                num_sale = len(df[sale])
                total_purch = int(df['Purch'].sum(skipna=True))
                total_sale = int(df['Sale'].sum(skipna=True))
                if num_purch != 0:
                    avg_purch = int(total_purch/num_purch)
                else:
                    avg_purch = 0
                if num_sale != 0:
                    avg_sale = int(total_sale/num_sale)
                    ratio = round(num_purch/num_sale, 2)
                else:
                    avg_sale = 0
                    ratio = num_purch
                return_y = return_calc(newTicker, start_yahoo, end_yahoo)
               
                if (sales == 1 and (num_purch != 0 or num_sale != 0)) or (sales == 0 and num_purch != 0):
                    lastDate = df['Transaction Date'][0]
                    ticker = yf.Ticker(newTicker)
                    sector = ticker.info['sector']
                    percentHeldByInsiders = ticker.info['heldPercentInsiders'] * 100
                    percentHeldByInstitution = ticker.info['heldPercentInstitutions'] * 100
                    shortPercent = ticker.info['shortPercentOfFloat'] * 100
                    new_df = pd.DataFrame({'Symbol': lst[0],
                                           'Purchases': num_purch,
                                           'Sales': num_sale,
                                           'Buy/Sell Ratio': ratio,
                                           'Period Return (%)': return_y,
                                           'Total Bought': f'{total_purch:,}',
                                           'Total Sold': f'{total_sale:,}',
                                           'Avg Shares Bought': f'{avg_purch:,}',
                                           'Avg Shares Sold': f'{avg_sale:,}',
                                           'Latest Transaction Date': lastDate,
                                           'Market Cap': mktCap,
                                           'Avg Volume': avgVolume,
                                           'Sector' : sector,
                                           'Percent Held By Insiders' : percentHeldByInsiders,
                                           'Percent Held by Institutions' : percentHeldByInstitution,
                                           'Short Percent' : shortPercent},
                                            index = [0])

                    new_df.set_index('Symbol', inplace=True)
                    dfs.append(new_df)
                pbar.update(1)
            except Exception as ex:
                #template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                #message = template.format(type(ex).__name__, ex.args)
                #print(message)
                pbar.update(1)
                continue

    if dfs:
        return new_df

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Parse options for stock analysis script")
    parser.add_argument("-days", "--days", action="store", help="To specify how many days from today do you want to look for insider trading. Default value is 30 days")
    parser.add_argument("-processes", "--processes", action="store", help="To specify how many processes to run parallely. Specifying a large value may slow down your machine. Default value is 10.")
    parser.add_argument("-filename", "--filename", action="store", help="To specify a filename for xlsx. Default name is insider_trading")
    parser.add_argument("-stocklist", "--stocklist", action="store", help="To specify a list of stocks on which to see insider trading. Default list of stocks will be based out of yahoo finance using yahoo_fin python library.")
    parser.add_argument("-insidersales", "--insidersales", action="store", help="To specify if you want to see insider selling in the stocks. Default is 0") 
    parser.add_argument("-mktcap", "--mktcap", action="store", help="To specify the minimum market cap as a criteria for insider trading. You can pass values like 1.5B, 100M. Default is 0") 
    args = parser.parse_args()

    if args.days:
        days = int(args.days)
    else:
        days = 30
    if args.processes:
        noOfProcesses = int(args.processes)
    else:
        noOfProcesses = 10
    if args.filename:
        fileName = args.filename + ".xlsx"
    else:
        fileName = "insider_trading.xlsx"
    if args.stocklist:
        l1 = args.stocklist.split(',')
    else:
        stockData = PyTickerSymbols()
        dow = []
        l1 = list(stockData.get_stocks_by_index('DOW JONES'))
        for i in range(0,len(l1)):
            dow.append(l1[i]['symbol'])
        l1 = si.tickers_sp500() + si.tickers_nasdaq() + si.tickers_other() + dow 
        l1 = list(set(l1))
        l1.sort()
        l1.pop(0)
    if args.insidersales:
        value = int(args.insidersales)
        if value > 1:
            print("ERROR insider sales value can only be 0 or 1 and you have passed %d" %(value))
            sys.exit(1)
        else:
            insiderSales = value
    else:
        insiderSales = 0
    if args.mktcap:
        marketCap = calculateMarketValue(args.mktcap)
    else:
        marketCap = 0


    print(days)
    print(noOfProcesses)
    print(fileName)
    print(l1)
    print(insiderSales)
    print(marketCap)
    
    if os.path.exists(fileName):
        os.remove(fileName)
    dfs = []
    earlierDate = calculateDateFromGivenDate(days)
    year = "%04d" % (earlierDate.year)
    month = "%02d" % (earlierDate.month)
    day = "%02d" % (earlierDate.day)
    date = str(year) + "-" + str(month) + "-" + str(day)
   
    pool = Pool(processes=noOfProcesses)
    part = partial(insider_trading_all, endDate=date, sales=insiderSales, marketCap=marketCap)
    dfs = list(pool.map(part, l1))

    flag = True
    for i in range(0, len(dfs)):
        if not isinstance(dfs[i], type(None)):
            flag = False
            break

    if flag == False: 
        combo = pd.concat(dfs)
        combo.sort_values('Buy/Sell Ratio', inplace=True, ascending=False) 
        combo.to_excel(fileName, index = True)
    else:
        print("There is no insider trading on any of the tickers")
        sys.exit(1)

    sectorList = []
    for i in range(0, len(dfs)):
        sectorList.append(dfs[i]['Sector'][0])

    #print(sectorList)
    uniqueSectorList = list(set(sectorList))
    #print(uniqueSectorList)
    uniqueSectorList = [x for x in sectorList if x != " "]
    #print(uniqueSectorList)
    sectorListDict = {}
    for i in range(0, len(sectorList)):
        for j in range(0, len(uniqueSectorList)):
            if sectorList[i] == uniqueSectorList[j]:
                if uniqueSectorList[j] in sectorListDict:
                    sectorListDict[uniqueSectorList[j]] = sectorListDict[uniqueSectorList[j]] + 1
                else:
                    sectorListDict[uniqueSectorList[j]] = 1
    #print(sectorListDict)
    data = (list(sectorListDict.values()))
    # Creating plot 
    fig = plt.figure(figsize =(10, 7)) 
    plt.pie(data, autopct = lambda pct: func(pct, data), labels = uniqueSectorList) 
      
    # show plot 
    plt.show() 
