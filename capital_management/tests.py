from django.test import TestCase


# Create your tests here.

# import pandas as pd

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

from django.db.models import Count, Sum
from datetime import date

# import os
# import django
#
# if os.environ.get('DJANGO_SETTINGS_MODULE'):
#     os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'securityproject.settings')

from capital_management.models import Broker, CapitalAccount


# class SimpleTest(TestCase):
#     def test_basic_sum(self):
#         self.assertEqual(1+1, 2)
#

class ModelTest(TestCase):
    def setUp(self):

        Broker.objects.create(id=1, name='国联证券', rate=0.0001, stamp_duty=0.00025, transfer_fee=0.00002,
                              date_added=2020-1-1, introduction='CANSLIM', nick_name='CANSLIM')
        Broker.objects.create(id=2, name='恒泰证券', rate=0.0001, stamp_duty=2, transfer_fee=2,
                              date_added=2020-1-1, introduction='CANSLIM', nick_name='Turtle')
        Broker.objects.create(id=3, name='海通证券', rate=0.0001, stamp_duty=0.00025, transfer_fee=0.00002,
                              date_added=2020-1-1, introduction='CANSLIM', nick_name='Principle')
        Broker.objects.create(id=4, name='恒泰证券', rate=0.0001, stamp_duty=2, transfer_fee=2,
                              date_added=2020-1-1, introduction='CANSLIM', nick_name='success')

        CapitalAccount.objects.create(id=1, total_assets=20, market_capital=33, fund_balance=32,
                                  position_gain_loss=45, initial_capital=21, date="2020-2-9", broker_id=2)
        CapitalAccount.objects.create(id=2, total_assets=20, market_capital=33, fund_balance=32,
                                      position_gain_loss=45, initial_capital=21, date="2020-2-8", broker_id=2)

        CapitalAccount.objects.create(id=3, total_assets=20, market_capital=33, fund_balance=32,
                                  position_gain_loss=45, initial_capital=21, date="2020-2-9", broker_id=2)
        CapitalAccount.objects.create(id=4, total_assets=20, market_capital=33, fund_balance=32,
                                  position_gain_loss=45, initial_capital=21, date="2020-2-9", broker_id=2)

    def test_event_models(self):

        # result = CapitalAccount.objects.values('fund_balance').annotate(num_broker=Sum('fund_balance')).filter(
        # broker_id=2)

        result = CapitalAccount.objects.values('fund_balance').annotate(num_broker=Count('id'))
        self.assertEqual(result[0]['num_broker'], 4)

        # current_day = date.today().strftime("%Y-%m-%d")
        # self.assertEqual(current_day, '2020-02-09')



