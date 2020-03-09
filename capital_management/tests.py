from django.test import TestCase

# Create your tests here.

import pandas as pd
import tushare as ts
import numpy as np

from itertools import chain

ts.set_token('033ad3c72aef8ce38d29d34482058b87265b32d788fb6f24d2e0e8d6')
pro = ts.pro_api()

"""2020-2-8 pandas的功能测试"""
# df1 = pd.read_csv('20200208.csv')
# df2 = pd.read_csv('rps20200207.csv')
# df = pd.read_csv('test1.csv'csv)

# df3 = pd.merge(df1, df2, how='left', on=['名称'])


# df3.to_csv("./test.csv", encoding="utf-8-sig", index=False)

# dff = df.rename(columns={'代码': 'code', '名称': 'name', "涨幅%": "change_rate", "现价": "price",  "涨跌": "change", "卖价": "sell",
#                      "买价": "buy", "细分行业": "industry_group", "流通市值": "circulation_capitalization",
#                      "AB股总市值": "market_capitalization", "扣非净利润(亿)": "net_profit_cut",
#                      "总量": "total_quantity", "现量": "quantity", "换手%": "turnover_rate", "20日涨幅%": "change_rate_20_day",
#                      "自选收益%": "earning_rate_from_list", "收盘": "close", "月线反转": "reversal_month_line"})
# print(dff)
#
# dff.to_csv("./reversal.csv", index=False)

"""2020-2-9 Django 的数据库 的字段计算 Sum求和 Count计数"""
"""
python manage.py test
return ok
"""

from django.db.models import Count, Sum, Q
import datetime

# import os
# import django
#
# if os.environ.get('DJANGO_SETTINGS_MODULE'):
#     os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'securityproject.settings')

from capital_management.models import Broker, CapitalAccount, TradeLists, TradeDailyReport, TradePerformance, AccountSurplus


# class SimpleTest(TestCase):
#     def test_basic_sum(self):
#         self.assertEqual(1+1, 2)
#

class ModelTest(TestCase):
    def setUp(self):
        Broker.objects.create(id=1, name='国联证券', rate=0.0001, stamp_duty=0.00025, transfer_fee=0.00002,
                              date_added='2020-01-01', introduction='CANSLIM', nick_name='CANSLIM')
        Broker.objects.create(id=2, name='恒泰证券', rate=0.0001, stamp_duty=2, transfer_fee=2,
                              date_added='2020-01-01', introduction='CANSLIM', nick_name='Turtle')
        Broker.objects.create(id=3, name='海通证券', rate=0.0001, stamp_duty=0.00025, transfer_fee=0.00002,
                              date_added='2020-01-01', introduction='CANSLIM', nick_name='Principle')
        Broker.objects.create(id=4, name='恒泰证券', rate=0.0001, stamp_duty=2, transfer_fee=2,
                              date_added='2020-01-01', introduction='CANSLIM', nick_name='success')

        CapitalAccount.objects.create(id=1, name='CANSLIM',initial_capital=21, date="2020-2-9", broker_id=2)
        CapitalAccount.objects.create(id=2, name='CANSLIM', initial_capital=21, date="2020-2-9", broker_id=2)

        TradeLists.objects.create(id=1, name='华兰生物', code='603596.SH', flag='B', price=24, quantity=1000,
                                  date='2020-02-10', brokerage=21, stamp_duty=0, transfer_fee=30,
                                  total_fee=40, total_capital=24000, clear_flag=1, account_id=1)
        TradeLists.objects.create(id=2, name='华兰生物', code='603596.SH', flag='B', price=24, quantity=1000,
                                  date='2020-02-10', brokerage=21, stamp_duty=0, transfer_fee=32,
                                  total_fee=40, total_capital=24000, clear_flag=1, account_id=1)
        TradeLists.objects.create(id=3, name='伯特利', code='603596.SH', flag='B', price=24, quantity=1000,
                                  date='2020-02-10', brokerage=21, stamp_duty=0, transfer_fee=27,
                                  total_fee=40, total_capital=24000, clear_flag=1, account_id=1)
        TradeLists.objects.create(id=4, name='华兰生物', code='000021.SZ', flag='B', price=24, quantity=1000,
                                  date='2020-02-07', brokerage=21, stamp_duty=0, transfer_fee=34,
                                  total_fee=40, total_capital=24000, clear_flag=1, account_id=3)
        TradeLists.objects.create(id=5, name='科技50', code='603596.SH', flag='B', price=24, quantity=1000,
                                  date='2020-02-06', brokerage=21, stamp_duty=0, transfer_fee=23,
                                  total_fee=40, total_capital=24000, clear_flag=1, account_id=2)
        TradeLists.objects.create(id=6, name='ETF500', code='603596.SH', flag='B', price=24, quantity=1000,
                                  date='2020-02-05', brokerage=21, stamp_duty=0, transfer_fee=23,
                                  total_fee=40, total_capital=24000, clear_flag=1, account_id=3)
        TradeLists.objects.create(id=7, name='广汇股份', code='603599.SH', flag='B', price=24, quantity=1000,
                                  date='2020-02-28', brokerage=21, stamp_duty=0, transfer_fee=23,
                                  total_fee=40, total_capital=24000, clear_flag=1, account_id=1)
        TradeLists.objects.create(id=8, name='千禾味业', code='603598.SH', flag='B', price=24, quantity=1000,
                                  date='2020-02-16', brokerage=21, stamp_duty=0, transfer_fee=23,
                                  total_fee=40, total_capital=24000, clear_flag=1, account_id=1)
        TradeLists.objects.create(id=9, name='千禾味业', code='603597.SH', flag='B', price=24, quantity=1000,
                                  date='2020-02-16', brokerage=21, stamp_duty=0, transfer_fee=23,
                                  total_fee=40, total_capital=24000, clear_flag=1, account_id=3)

        TradeDailyReport.objects.create(id=1, name='伯特利', code='603596.SH', date='2017-1-1', cost='100', amount='200',
                                        account_id=1, total_capital=10, total_fee=10,  update_flag=True)
        TradeDailyReport.objects.create(id=1, name='伯特利', code='603596.SH', date='2017-1-1', cost='10001', amount='200',
                                        account_id=1, total_capital=10, total_fee=10, update_flag=True)
        TradeDailyReport.objects.create(id=2, name='广兰生物', code='000005.SZ', date='2017-1-1', cost='0', amount='0',
                                        account_id=1, total_capital=10, total_fee=1002, update_flag=False)
        TradeDailyReport.objects.create(id=3, name='广兰生物', code='000005.SZ', date='2017-1-1', cost='0', amount='0',
                                        account_id=1, total_capital=101, total_fee=10, update_flag=False)

        TradePerformance.objects.create(id=1, close=60, moving_average=60, high_price=70, low_price=50, boll_up=66,
                                        boo_down=54, performance=23, trade_performance=0, date='2020-02-03', trade_id=3)
        TradePerformance.objects.create(id=2, close=60, moving_average=60, high_price=70, low_price=50, boll_up=66,
                                        boo_down=54, performance=55, trade_performance=0, date='2020-02-03', trade_id=2)
        TradePerformance.objects.create(id=3, close=60, moving_average=60, high_price=70, low_price=50, boll_up=66,
                                        boo_down=54, performance=55, trade_performance=0, date='2020-02-03', trade_id=4)
        TradePerformance.objects.create(id=4, close=60, moving_average=60, high_price=70, low_price=50, boll_up=66,
                                        boo_down=54, performance=31, trade_performance=0, date='2020-02-03', trade_id=1)

        AccountSurplus.objects.create(id=1, total_assets=200000, market_capital=300001, fund_balance=1233,
                                      position_gain_loss=5462, total_fee=12345, initial_capital=1, update_flag=True,
                                      final_cost=100, date='2020-01-01', account_id=1)
        AccountSurplus.objects.create(id=2, total_assets=203000, market_capital=300100, fund_balance=1234,
                                      position_gain_loss=5632, total_fee=12345, initial_capital=1, update_flag=True,
                                      final_cost=100, date='2020-01-01', account_id=2)
        AccountSurplus.objects.create(id=3, total_assets=204000, market_capital=300100, fund_balance=1433,
                                      position_gain_loss=542, total_fee=12345, initial_capital=1, update_flag=True,
                                      final_cost=1002, date='2020-01-01', account_id=2)
        AccountSurplus.objects.create(id=4, total_assets=200500, market_capital=310000, fund_balance=1833,
                                      position_gain_loss=546, total_fee=12345, initial_capital=1, update_flag=True,
                                      final_cost=103, date='2020-01-01', account_id=1)

    def test_event_models(self, columns=None):
        # """2020-02-23eCharts日线图"""
        # df = ts.pro_bar('000001.SZ', start_date='20191201', end_date='20200221',
        #                 )
        # self.assertEqual(df[['trade_date', 'open', 'close', 'high', 'close']], 3)
        #
        """2020-02-20 echarts 表数据结构"""
        # # 筛选一个月的数据
        # data_date = ['product']
        # assets = ['总资产']
        # fund_balance = ['余额']
        # gain_loss = ['浮盈亏']
        # total = []
        # total_data = AccountSurplus.objects.filter(date__gte='2020-01-01').values(
        #     'total_assets', 'market_capital', 'fund_balance', 'position_gain_loss', 'date')
        # for data in total_data:
        #     new_date = data['date']
        #     data_date.append(data['date'])
        #     assets.append(data['total_assets'])
        #     fund_balance.append(data['fund_balance'])
        #     gain_loss.append(data['position_gain_loss'])
        #
        # total.append(data_date)
        # total.append(assets)
        # total.append(fund_balance)
        # total.append(gain_loss)
        #
        # self.assertEqual(total[0][1], 3)
        """tushare 日线接口"""
        # query_result = pro.query('daily', ts_code='002007.SZ', start_date='20200204', end_date='20200204')
        # self.assertEqual(query_result['change'].values[0], 3)
        # stock_lists = []
        # stock_name = []
        # stock_value = []
        # nut = []
        # positions_data = TradeDailyReport.objects.filter(date='2017-1-1').values('name', 'total_capital')
        # for stock in positions_data:
        #     stock_value.append(stock['total_capital'])
        #     stock_name.append(stock['name'])
        #     donut = {'value': stock['total_capital'], 'name': stock['name']}
        #     nut.append(donut)
        #
        # self.assertEqual(positions_data, 3)

        """2020-02-18 多表组合查询功能"""
        # performance_obj = TradePerformance.objects.get(trade_id=1)
        #
        # stock = performance_obj.trade.name
        # stock_list = TradeLists.objects.values(
        #     'account_id', 'code', 'name', 'price', 'flag', 'date', 'trade_resource', 'quantity', 'tradeperformance__close',
        #     'tradeperformance__moving_average', 'tradeperformance__performance', 'tradeperformance__trade_performance')
        #
        # self.assertEqual(stock_list[10]['account_id'], 3)
        # """2020-02-19 dashboard"""
        # data = TradeDailyReport.objects.values('total_capital').latest()
        #
        # self.assertEqual(data['total_capital'], 3)
        """2020-02-18 for循环的简化"""
        # new_value_set = TradeLists.objects.filter(date__year='2020').values('date', 'account_id', 'code').annotate(fee=Sum('total_fee'))
        #
        # self.assertEqual(new_value_set[2]['date'], 3)

        """2020-2-12 TradeDailyReport表单 账户结算功能"""
        # recorder_num = TradeDailyReport.objects.aggregate(
        #     position_num=Count('id'))  # 作用---定位TradeDailyReport的最近的一条记录id号
        # position_id = recorder_num['position_num']
        #
        # account_num = CapitalAccount.objects.aggregate(account_num=Count('id'))  # 作用---获得资金账户数量
        #
        # end_date = datetime.datetime.today().strftime("%Y-%m-%d")  # django的语句比较简洁
        # start_date = TradeDailyReport.objects.get(id=position_id).date
        # date_delta = 50
        # tushare接口获取交易日历
        c

        # # 当前结算日的股票交易汇总数据
        #
        # # 两者之和生成新的结算数据
        # for account_id in range(account_num['account_num'] + 1):
        #     position_date = start_date
        #     history_TradeDailyReport_date = position_date - datetime.timedelta(days=1)
        #     for _ in range(date_delta):  # 以交易日期轮询
        #         # 获得上一日持仓情况
        #         history_data = TradeDailyReport.objects.filter(date=history_TradeDailyReport_date,
        #                                                        account_id=account_id).values('cost', 'amount')
        #         # 检索当日结算值
        #         new_value_set = TradeLists.objects.filter(date=position_date, account_id=account_id) \
        #             .annotate(amount_num=Sum('quantity'), capital_num=Sum('total_capital'))
        #
        #         position_date = position_date + datetime.timedelta(days=1)
        #
        # # new_TradeDailyReport_id = TradeDailyReport.objects.aggregate(TradeDailyReport_num=Count('id'))  # 作用---获得资金账户数量
        # # new_value_set = TradeLists.objects.filter(date='2020-02-03', account_id=1).values(
        # #     'name').annotate(amount_num=Sum('quantity'),
        # #                      capital_num=Sum('total_capital'))
        # # 获取当日结算股票的历史持仓情况
        # history_data = TradeDailyReport.objects.filter(date='2017-1-1', account_id=1).values('code', 'name', 'date',
        #                                                                                      'cost', 'amount',
        #                                                                                      'account_id',
        #                                                                                      'update_flag')
        # new_value_set = TradeLists.objects.filter(date='2020-02-10', account_id=1).values('code').annotate(
        #     amount=Sum('quantity'),
        #     cost=Sum('total_capital'))
        #
        # # df = pd.DataFrame(new_data, columns={'code', 'name', 'date', 'cost', 'amount', 'account_id', 'update_flag'})
        #
        # # combine = df['cost', 'amount'].groupby(df['code']).sum()
        #
        # # 检索当日结算值
        # performance_data = TradeLists.objects.filter(date='2020-02-10').values('id', 'code', 'price', 'flag')



        """2020-2-11"""
        # new_value_set = TradeLists.objects.filter(date='2020-02-03', account_id=2).values(
        #     'name').annotate(amount_num=Sum('quantity'), capital_num=Sum('total_capital'), )
        #
        # self.assertEqual(new_value_set[1]['name'], 3)
        """2020-2-11"""

        # end_date = datetime.datetime.today().strftime("%Y-%m-%d")
        #
        # cal_date = pro.query('trade_cal', start_date=start_date, end_date=end_date, is_open=1, fields=['cal_date'])
        # # 循环结算每个交易日持仓情况
        #
        # for index, cal in cal_date.iterrows():
        #     p_date = (pd.to_datetime(cal["cal_date"])).strftime("%Y-%m-%d")
        #
        #     amount = TradeLists.objects.filter(date=p_date).values('name').annotate(
        #         num_amount=Sum('quantity'))
        #     p_name = TradeLists.objects.filter(date=p_date)

        # result = CapitalAccount.objects.values('fund_balance').annotate(num_broker=Sum('fund_balance')).filter(
        # broker_id=2)

        # result = CapitalAccount.objects.values('fund_balance').annotate(num_broker=Count('id'))
        # self.assertEqual(result[0]['num_broker'], 4)

        # current_day = date.today().strftime("%Y-%m-%d")
        # self.assertEqual(current_day, '2020-02-09')

        # total_capital = TradeLists.objects.values('total_capital').annotate(
        #     answer=Sum('total_capital')).filter(Q(name='华兰生物') & Q(account_id=2))
        # self.assertEqual(total_capital[0]['answer'], 48000)
        # quantity = TradeLists.objects.values('quantity').annotate(
        #     ans=Sum('quantity')).filter(Q(account_id=2) & Q(name='华兰生物'))
        # cost = total_capital[0]['answer'] / quantity[0]['ans']
        # self.assertEqual(cost, 24.)

        # stock_capital = TradeLists.objects.filter(account_id=1).values('name').annotate(transfer=Sum('transfer_fee'))
        # self.assertEqual(stock_capital[0]['transfer'], 60)

        # 某资金账户项下（account_id）的某股票(name)的持股数量之和
        # amount = TradeLists.objects.filter(account_id=1).values('name').annotate(
        #     num_amount=Sum('quantity'))
        # self.assertEqual(amount[0]["num_amount"], 20)
        #

        """2020-02-10 测试时间轮询的函数命令"""

        #  end_date = datetime.datetime.today().strftime("%Y-%m-%d")
        #  start_date = '2017-1-1'
        #  delta = datetime.timedelta(days=1)
        #  d = pro.query('trade_cal', start_date=start_date, end_date=end_date, is_open=1, fields=['cal_date'])
        #
        #  for index, r in d.iterrows():
        #     print((pd.to_datetime(r["cal_date"])).strftime("%Y-%m-%d"))
