from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import openpyxl
import statsmodels.api as sm
import pandas as pd
import numpy as np
import tushare as ts
import datetime
import backtrader as bt
import backtrader.feeds as btfeeds
from WindPy import w
import os
w.start()
w.isconnected()


def get_data_tushare(code, start='2020-01-01', end='2020-12-31'):
    df = ts.get_k_data(code, autype='qfq', start=start, end=end)
    df.index = pd.to_datetime(df.date)
    df['openinterest'] = 0
    df = df[['open', 'high', 'low', 'close', 'volume', 'openinterest']]
    return df


def get_data_wind(code, start='2020-01-01', end='2020-12-31'):
    wind = w.wsd(code, "open,high,low,close,volume", start, end, "Currency=CNY")
    wind_time = pd.DataFrame(wind.Times, columns=['Times'])  # 数据源Pandas转置，但是Wind数据源存在格式上的问题
    wind_price = pd.DataFrame(wind.Data).T  # 取价格字段
    wind_price.columns = ['open', 'high', 'low', 'close', 'volume']
    wind_price['openinterest'] = 0
    wind_price.index = pd.to_datetime(wind_time.Times)
    return wind_price


def get_data_wind_minute(code, start="2021-11-05 09:30:00", end="2021-11-05 15:00:00"):
    wind = w.wsi(code, "open,high,low,close,volume", start, end, "ShowBlank=0")
    wind_time = w.wsd('601318.SH', "open", '2020-01-01', '2020-12-30', "Currency=CNY")
    wind_time = pd.DataFrame(wind_time.Times, columns=['Times'])  # 数据源Pandas转置，但是Wind数据源存在格式上的问题
    wind_price = pd.DataFrame(wind.Data).T  # 取价格字段
    wind_price.columns = ['open', 'high', 'low', 'close', 'volume']
    wind_price['openinterest'] = 0
    wind_price.index = pd.to_datetime(wind_time.Times)
    return wind_price

class my_strategy1(bt.Strategy):
    #全局设定交易策略的参数
    params=(
        ('maperiod',20),
           )

    def __init__(self):
        #指定价格序列
        self.dataclose=self.datas[0].close
        # 初始化交易指令、买卖价格和手续费
        self.order = None
        self.buyprice = None
        self.buycomm = None

        #添加移动均线指标，内置了talib模块
        self.sma = bt.indicators.SimpleMovingAverage(
                      self.datas[0], period=self.params.maperiod)
    def next(self):
        if self.order: # 检查是否有指令等待执行,
            return
        # 检查是否持仓
        if not self.position: # 没有持仓
            #执行买入条件判断：收盘价格上涨突破20日均线
            if self.dataclose[0] > self.sma[0]:
                #执行买入
                self.order = self.buy(size=500)
        else:
            #执行卖出条件判断：收盘价格跌破20日均线
            if self.dataclose[0] < self.sma[0]:
                #执行卖出
                self.order = self.sell(size=500)

class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])


data = get_data_wind_minute('512690.SH')

if __name__ == '__main__':
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.addstrategy(bt.Strategy)
    # 加载数据
    data = bt.feeds.PandasData(dataname=data)

    cerebro.run()
    cerebro.plot()

# 初始化cerebro回测系统设置
cerebro = bt.Cerebro()
#将数据传入回测系统
cerebro.adddata(data)
# 将交易策略加载到回测系统中
cerebro.addstrategy(my_strategy1)
# 设置初始资本为10,000
startcash = 10000
cerebro.broker.setcash(startcash)
# 设置交易手续费为 0.2%
cerebro.broker.setcommission(commission=0.002)
cerebro.run()
cerebro.plot(style='candlestick')