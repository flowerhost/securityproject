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

ts.set_token('033ad3c72aef8ce38d29d34482058b87265b32d788fb6f24d2e0e8d6')
pro = ts.pro_api()

calendar = pro.query('trade_cal', start_date='20200203', end_date='20200228', is_open=1, fields=['cal_date'])

stop_loss_data = ts.pro_bar(ts_code='603596.SH', start_date='20200214', end_date='20200228')

stop_loss_data = stop_loss_data.sort_values(by=['trade_date'], ascending=[True])
stop_loss_data = stop_loss_data[['trade_date', 'low']].values.tolist()
count_number = 0
sum_values = 0
for i in range(11):
    if i == 0:
        pass
    else:
        latest_low = stop_loss_data[i][1]
        for j in range(2):
            early_low = stop_loss_data[i - j][1]
            if early_low > latest_low:
                count_number = count_number + 1
                sum_values = sum_values + early_low - latest_low
        print(j)
result = stop_loss_data[-2][1] - 3 * sum_values / count_number

print(result)

