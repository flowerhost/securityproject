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

from itertools import chain

# ts.set_token('033ad3c72aef8ce38d29d34482058b87265b32d788fb6f24d2e0e8d6')
# pro = ts.pro_api()
#
#
# calendar = pro.query('trade_cal', start_date='20200214', end_date='20200221', is_open=1, fields=['cal_date'])
# for data in calendar.values:
#     date_cal = data[0]
#     print(date_cal)

df = ts.pro_bar('000001.SZ', start_date='20191201', end_date='20200223', )
df1 = df.sort_values(by= ['trade_date'], ascending=[True])
data = df1[['trade_date', 'open', 'close', 'high', 'low']].values.tolist()

print(data)
