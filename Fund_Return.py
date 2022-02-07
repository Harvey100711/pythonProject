from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from WindPy import w
import pandas as pd
from datetime import datetime
import backtrader as bt
w.start()

#正常显示画图时出现的中文和负号
from pylab import mpl
mpl.rcParams['font.sans-serif']=['SimHei']

#使用tushare旧版接口获取数据
import tushare as ts

# def get_data(code,start='2021-01-01',end='2021-12-31'):
#     df=ts.get_k_data(code,autype='qfq',start=start,end=end)
#     df.index=pd.to_datetime(df.date)
#     df['openinterest']=0
#     df=df[['open','high','low','close','volume','openinterest']]
#     return df

def get_data_wind(code, start='2021-01-01', end='2021-12-31'):
    #wind = w.wsd(code, "open,high,low,close,volume", start, end, "Currency=CNY")
    wind = w.wsd(code,  "nav,nav,nav,nav,nav", start, end, "Currency=CNY")
    wind_time = pd.DataFrame(wind.Times, columns=['Times'])  # 数据源Pandas转置，但是Wind数据源存在格式上的问题
    wind_price = pd.DataFrame(wind.Data).T  # 取价格字段
    wind_price.columns = ['open', 'high', 'low', 'close', 'volume']
    #wind_price.columns = ['close']
    wind_price['openinterest'] = 10
    wind_price['volume'] = 0
    wind_price.index = pd.to_datetime(wind_time.Times)
    return wind_price


class my_strategy1(bt.Strategy):
    #全局设定交易策略的参数

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        #指定价格序列
        self.dataclose=self.datas[0].close
        # 初始化交易指令、买卖价格和手续费
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.Trade_log = pd.read_excel(Trade_log_place,dtype=str)

    def next(self):
        for i in range(len(self.Trade_log)):
            if self.datas[0].datetime.date(0).isoformat() in self.Trade_log.iat[i,9]:
                if '基金申购' in self.Trade_log.iat[i,5]:
                    self.log('Buy, %.2f' % self.dataclose[0])
                    self.order = self.buy(size=1)
                else:
                    self.log('Sell, %.2f' % self.dataclose[0])
                    self.order = self.sell(size=1)


Trade_log_place = r'D:\其他\雪球\2021年终统计\导入模板.xlsx'
Code = pd.read_excel(Trade_log_place).基金代码[0].replace("\t","")

if __name__ == '__main__':

    dataframe = get_data_wind(Code)
    #dataframe=get_data('600000')
    #回测期间
    start=datetime(2021, 1, 1)
    end=datetime(2021, 12, 31)
    # 加载数据
    data = bt.feeds.PandasData(dataname=dataframe,fromdate=start,todate=end)
    # 初始化cerebro回测系统设置
    cerebro = bt.Cerebro()
    #cerebro = bt.Cerebro(stdstats=False)
    #将数据传入回测系统
    cerebro.adddata(data)
    # 将交易策略加载到回测系统中
    cerebro.addstrategy(my_strategy1)
    # 设置初始资本为10,000
    startcash = 10000
    cerebro.broker.setcash(startcash)
    # 设置交易手续费为 0.2%
    #cerebro.broker.setcommission(commission=0.002)

    d1=start.strftime('%Y%m%d')
    d2=end.strftime('%Y%m%d')
    print(f'初始资金: {startcash}\n回测期间：{d1}:{d2}')
    #运行回测系统
    cerebro.run()
    #获取回测结束后的总资金
    portvalue = cerebro.broker.getvalue()
    pnl = portvalue - startcash
    #打印结果
    print(f'总资金: {round(portvalue,2)}')
    cerebro.plot()