from django.test import TestCase
# import pandas as pd
# import numpy as np
# Create your tests here.
# list1 = [['603596.SH', '伯特利', '2017-01-02', 100.0, 200.0, 1, True]]
# list2 = [['000001.SZ', '广汇股份', '2020-1-12', 24000.0, 1000, 1]]
# data = list1 + list2
# data1 = pd.DataFrame(data, columns={'code', 'name', 'date', 'cost', 'amount', 'account_id', 'update_flag'})
#
# # print(data)
#
# print(data1)

import pandas as pd
import tushare as ts
import datetime
import sqlite3
import os

from itertools import chain

ts.set_token('033ad3c72aef8ce38d29d34482058b87265b32d788fb6f24d2e0e8d6')
pro = ts.pro_api()
"""2020-02-29 计算止损点"""
# calendar = pro.query('trade_cal', start_date='20200203', end_date='20200228', is_open=1, fields=['cal_date'])
# print(calendar['cal_date'].values[-1])
#
# stop_loss_data = ts.pro_bar(ts_code='603596.SH', start_date='20200214', end_date='20200228')
#
# stop_loss_data = stop_loss_data.sort_values(by=['trade_date'], ascending=[True])
# stop_loss_data = stop_loss_data[['trade_date', 'low']].values.tolist()
# count_number = 0
# sum_values = 0
# for i in range(11):
#     if i == 0:
#         pass
#     else:
#         latest_low = stop_loss_data[i][1]
#         for j in range(2):
#             early_low = stop_loss_data[i - j][1]
#             if early_low > latest_low:
#                 count_number = count_number + 1
#                 sum_values = sum_values + early_low - latest_low
#         print(j)
# result = stop_loss_data[-2][1] - 3 * sum_values / count_number
#
# print(result)
# data = pro.query('stock_basic', exchange='', list_status='L')
# data = data[['name', 'ts_code', 'area', 'symbol', 'industry', 'market']]
"""数据备份"""
# con = sqlite3.connect('/Users/flowerhost/securityproject/db.sqlite3')
# c = con.cursor()
# data1 = pd.read_csv('/Users/flowerhost/securityproject/data/backup/tradelists20200509.csv')
# data1.to_sql("capital_management_tradelists", con, if_exists="append", index=False)
# data2 = pd.read_csv('/Users/flowerhost/securityproject/data/backup/broker20200407.csv')
# data2.to_sql("capital_management_broker", con, if_exists="append", index=False)
# data3 = pd.read_csv('/Users/flowerhost/securityproject/data/backup/capital2020407.csv')
# data3.to_sql("capital_management_capitalaccount", con, if_exists="append", index=False)
# c.execute("select * from capital_management_capitalaccount")
# result = c.fetchall()
# print(result)
"""基本面SMR数据抽取 tushare 20200404"""
# query_date = datetime.date.today()
# start_query_date = query_date - datetime.timedelta(weeks=300)
# filename ='/Users/flowerhost/securityproject/data/eps20200404.csv'
# for query_date in ['20161231', '20170331', '20170630','20170930', '20171231',
#                    '20180331', '20180630', '20180930', '20181231', '20190331',
#                    '20190630', '20190930', '20191231']:
#     query_data = pro.query('fina_indicator_vip', start_date=query_date, end_date=query_date)
#     df = query_data[['end_date', 'ts_code', 'basic_eps_yoy', 'roe', 'grossprofit_margin', 'q_sales_yoy', 'dt_netprofit_yoy']]
#     if os.path.exists(filename):
#         df.to_csv(filename, mode='a', header=None)
#     else:
#         df.to_csv(filename)
# print(df)
"""EPS数据清洗，删除roe空值的行20200404"""
# df = pd.read_csv('/Users/flowerhost/securityproject/data/eps20200404.csv')
# df = df[df['roe'].notna()]
# df.drop(['Unnamed: 0'], axis=1, inplace=True)
# df.sort_values(by=['ts_code', 'end_date'], ascending=[True, False], inplace=True)
# df.fillna(value=0, inplace=True)
# df.reset_index(drop=True, inplace=True)
# df.to_csv('/Users/flowerhost/securityproject/data/eps.csv')

"""EPS切片，完成标准差计算20200404"""
# df = pd.read_csv('/Users/flowerhost/securityproject/data/eps.csv')
# df = df.reset_index(drop=True)
#
# df = df.groupby('ts_code').filter(lambda g: g.ts_code.count() >12)
# df.to_csv('/Users/flowerhost/securityproject/data/group.csv')
# data_EPS = df.groupby('ts_code')['basic_eps_yoy'].std().rank(ascending=True)  # 按照季报收益稳定性进行排名。值越小越稳定。
# # 取每组第一个值求和SMR,进行排名。
# data_SMR = df.groupby('ts_code', as_index=False)['roe', 'dt_netprofit_yoy', 'q_sales_yoy', 'grossprofit_margin'].first()
# data_SMR['SMR'] = data_SMR.iloc[:, 1:5].sum(axis=1).rank(ascending=True)
# data_join = pd.merge(data_EPS, data_SMR, on='ts_code')
# # 排名转化为百分比
# x = data_join['ts_code'].count()
# data_join['SMR'] = round(100*data_join['SMR']/x, 1)
# data_join['EPS_Stability'] = round(100*data_join['basic_eps_yoy']/x, 1)
# # print(data_join)
# data_new_quarter = df.groupby('ts_code')['ts_code', 'basic_eps_yoy'].head(1)
# data_new_quarter['new_quarter'] = df['basic_eps_yoy']
# print(data_new_quarter)
# data = df.groupby('ts_code')['ts_code', 'basic_eps_yoy'].head(2)
# print(data)
# data = data.groupby('ts_code').sum()*1.5  # 最近两个季度的eps权重1.5
# df['end_date'] = df['end_date'].astype('str')  # 转化为str型。
# data_year = df[df['end_date'].str.contains('1231')].groupby('ts_code').head(3)
# data_year = data_year[['end_date', 'ts_code', 'basic_eps_yoy']].groupby('ts_code').sum()
# data_year = pd.merge(data, data_year, on='ts_code')
# data_year['EPS'] = data_year.iloc[:, 1:3].sum(axis=1).rank(ascending=True)
# data_join = pd.merge(data_join, data_year, on='ts_code')
# data_join = pd.merge(data_join, data_new_quarter, on='ts_code')
# data_join['EPS'] = round(100*data_join['EPS']/x, 1)
# data_join = data_join[['ts_code', 'EPS', 'SMR', 'EPS_Stability', 'new_quarter']]
#
# data_join.to_csv('/Users/flowerhost/securityproject/data/SMR.csv')

"""RPS强度指标 202020407"""
# # 1、获取交易日期,取最新的交易日，推算出前250日的日期。
# end_date = datetime.date.today()
# start_date = end_date - datetime.timedelta(weeks=60)
# trade_date = pro.query('trade_cal', start_date=start_date.strftime("%Y%m%d"), end_date=end_date.strftime("%Y%m%d"), is_open=1, fields=['cal_date'])
# daily_end_date = trade_date.tail(2)['cal_date'].values[0]
# daily_start_date = trade_date.tail(250)['cal_date'].values[0]
# # 2、分别获得最新日的交易数据收盘价，和250日前交易日期收盘价
# df1 = pro.daily(trade_date=daily_start_date, fields=['ts_code', 'close', 'high'])
# df2 = pro.daily(trade_date=daily_end_date, fields=['ts_code', 'close'])
# data1 = pd.merge(df1, df2, on='ts_code')
# data1.sort_values(by='ts_code', ascending=True, inplace=True)
# data1.reset_index(drop=True, inplace=True)
# # 3、计算涨跌幅度。进行排名。
# data1['RPS'] = data1.apply(lambda x: round((x['close_y']-x['close_x'])/x['close_x'], 2), axis=1).rank(ascending=True)
# x = data1['ts_code'].count()
# data1['RPS'] = round(100*data1['RPS']/x, 1)
# data1['decline_range'] = data1.apply(lambda x: round((x['close_y']-x['high'])/x['high'], 2), axis=1)
# data1.to_csv('/Users/flowerhost/securityproject/data/RPS20200407.csv')
# data1 = pd.read_csv('/Users/flowerhost/securityproject/data/SMR.csv')
# data2 = pd.read_csv('/Users/flowerhost/securityproject/data/RPS20200407.csv')
# data2 = data2[['ts_code', 'RPS', 'decline_range']]
# data_join = pd.merge(data1, data2, on='ts_code')
# data_join['TOTAL'] = data_join.apply(lambda x: round(x['EPS']*2 + x['RPS']*2 + x['SMR'] + x['decline_range'], 2), axis=1).rank(ascending=True)
# x = data_join['ts_code'].count()
# data_join['TOTAL'] = round(100*data_join['TOTAL']/x, 1)
# data_join.reset_index(drop=True, inplace=True)
# data_join.drop(['Unnamed: 0'], axis=1, inplace=True)
#
# data_join.to_csv('/Users/flowerhost/securityproject/data/RPS_SMR.csv')
"""计算52周最高点涨降幅度"""
# end_date = datetime.date.today()
# start_date = end_date - datetime.timedelta(weeks=60)
# trade_date = pro.query('trade_cal', start_date=start_date.strftime("%Y%m%d"), end_date=end_date.strftime("%Y%m%d"), is_open=1, fields=['cal_date'])
# query_date = trade_date.tail(250)['cal_date']
# data = pd.DataFrame()
# for query_day in query_date:
#     query_data = pro.monthly(trade_date=query_day, fields=['trade_date', 'ts_code', 'high'])
#     data = data.append(query_data, ignore_index=True)
#
# first_date = '%d%02d01'%(end_date.year, end_date.month)
# daily_date = pro.query('trade_cal', start_date=first_date, end_date=end_date.strftime("%Y%m%d"), is_open=1, fields=['cal_date'])
# for query_date in daily_date['cal_date']:
#     query_data = pro.daily(trade_date=query_date, fields=['trade_date', 'ts_code', 'high'])
#     data = data.append(query_data, ignore_index=True)
#     print(query_date)
#
# data.to_csv('/Users/flowerhost/securityproject/data/monthly.csv')

# high_data = pd.read_csv('/Users/flowerhost/securityproject/data/monthly.csv')
# high_data = high_data.groupby('ts_code')['high'].max()
# print(high_data)
#
# data1 = pd.merge(df1, df2, on='ts_code')
# data1.sort_values(by='ts_code', ascending=True, inplace=True)
# data1.reset_index(drop=True, inplace=True)

"""申万行业指数"""
# df = pro.index_member(index_code='850543.SI')
# print(df)
# index_l3 = pro.sw_daily(trade_date='20200414')
# index_l3 = index_l3.tail(227)
# index_l3.to_csv('/Users/flowerhost/securityproject/data/index_l3.csv')
# member_count = index_l3.count()
# print(member_count)
# l3 = pro.index_classify(level='L3', src='SW')
# data = pd.DataFrame()
# for l_code in l3['index_code']:
#     print(l_code)
#     index_member = pro.index_member(index_code=l_code)
#     data = data.append(index_member, ignore_index=True)
# data.to_csv('/Users/flowerhost/securityproject/data/index_member.csv')
# data['ts_code'] = data['index_code']
#
# merge_join = pd.merge(data, index_l3, on='ts_code')
# print(merge_join)
# merge_join.to_csv('/Users/flowerhost/securityproject/data/merge_join.csv')

# l2.to_csv('/Users/flowerhost/securityproject/data/l2.csv')
# l3.to_csv('/Users/flowerhost/securityproject/data/l3.csv')
# index_member = pro.index_member(index_code='851911.SI')
# print(index_member)
# d = datetime.date.today()
# y = str(d.year - 1)
# week_day = d - datetime.timedelta(days=d.weekday())
# trade_date = pro.query('trade_cal', start_date='20200413',
#                            end_date="20200416", is_open=1, fields=['cal_date'])
#
# new_year_date = trade_date.head(1)['cal_date'].values[0]
# test = trade_date.tail(140)['cal_date'].values[0]
# print(str(y))
# end_date = datetime.datetime.today()
# df_volume_ratio = pro.daily_basic(
#         ts_code='', trade_date=end_date.strftime("%Y%m%d"), fields=['ts_code', 'trade_date', 'volume_ratio'])
# print(df_volume_ratio)
"""复权因子 2020-05-29"""
# adj_factor1 = pro.adj_factor(trade_date='20190528')
# adj_factor = pro.adj_factor(trade_date='20200529')
# adj_factor = pd.merge(adj_factor, adj_factor1, on='ts_code')
# adj_factor['adj_factor_y'] = round(adj_factor['adj_factor_y']/adj_factor['adj_factor_x'], 2)
# adj_factor.to_csv('/Users/flowerhost/securityproject/data/adj_factor.csv')
month_date = pro.query('trade_cal', start_date=20190528, end_date=20200529, is_open=1,
                           fields=['cal_date'])
lase_date = month_date.tail(1)['cal_date'].values[0]
begin_date = month_date['cal_date'][0]
df = pro.monthly(start_date=begin_date, end_date=lase_date)
df.to_csv('/Users/flowerhost/securityproject/data/monthly.csv')

