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

from itertools import chain

ts.set_token('033ad3c72aef8ce38d29d34482058b87265b32d788fb6f24d2e0e8d6')
pro = ts.pro_api()

query_result = ts.pro_bar(ts_code='002007.SZ', adj='qfg', ma=[10], start_date='2020-01-01', end_date='2020-02-14')

close = query_result['close'][0]
high_price = query_result['high'].values[0]
low_price = query_result['low'].values[0]
moving_average = query_result['ma10'].values[0]


print(high_price)
