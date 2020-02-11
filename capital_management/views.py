# Create your views here.

from django.shortcuts import render, redirect
from .models import TradeLists, Broker, Positions
from .form import BrokerForm, TradeListsForm

from django.db.models import Count, Sum
from datetime import date
import time
import datetime

"""tushare类数据接口"""
import tushare as ts

ts.set_token('033ad3c72aef8ce38d29d34482058b87265b32d788fb6f24d2e0e8d6')
pro = ts.pro_api()


def index(request):
    stocks = TradeLists.objects.all()
    return render(request, 'capital_management/index.html', locals())


def dashboard(request):
    pass
    return render(request, 'capital_management/dashboard.html', locals())


def prepare_data(request):
    """
        更新所有收盘后的数据表：
           1、持股数据表:      Positions(models.Model)
           2、清仓数据表:      Clearance(models.Model)
           3、账户资产管理:    CapitalAccount(models.Model)
        :param request:
        :return:
    """
    #  首先判断:"持股数据表---Positions"的update_flag字段是否为true？如果是，则判断为数据已经更新过，否则进行更新！


def broker(request):
    if request.method != 'POST':
        broker_form = BrokerForm()
    else:
        broker_form = BrokerForm(request.POST)
        if broker_form.is_valid():
            broker_form.save()
            return redirect('capital_management:index')

    context = {'broker_form': broker_form}
    return render(request, 'capital_management/broker.html', context)


def trade(request):
    """交易流水"""
    if request.method != 'POST':
        trade_form = TradeListsForm()
    else:
        trade_form = TradeListsForm(request.POST)
        if trade_form.is_valid():

            new_trade = trade_form.save(commit=False)

            # tushare 获取股票名称
            for _ in range(3):
                try:
                    query_result = pro.query('stock_basic', ts_code=new_trade.code, fields='name')
                except:
                    time.sleep(1)
                else:
                    new_trade.name = query_result['name'].values[0]

            # 计算成交金额
            total_capital = round(new_trade.quantity * new_trade.price, 2)

            # 计算印花税
            if new_trade.flag == 'B':
                new_trade.stamp_duty = 0
            else:
                new_trade.stamp_duty = round(total_capital * 0.001, 2)

            # 计算券商佣金
            brokerage = round(total_capital * 0.00025, 2)
            if brokerage < 1:
                new_trade.brokerage = 0
            else:
                new_trade.brokerage = brokerage

            # 计算过户费
            transfer_fee = round(total_capital * 0.00002, 2)
            if transfer_fee >= 5:
                new_trade.transfer_fee = transfer_fee
            else:
                new_trade.transfer_fee = 5

            # 手续费总计
            new_trade.total_fee = round(new_trade.stamp_duty + new_trade.transfer_fee + new_trade.brokerage, 2)

            # 交易总额
            new_trade.total_capital = round(total_capital + new_trade.brokerage + new_trade.transfer_fee
                                            + new_trade.stamp_duty, 2)

            new_trade.save()

            return redirect('capital_management:index')

    context = {'trade_form': trade_form}
    return render(request, 'capital_management/trade.html', context)


def balance(request):
    """资金账户结算功能，以交易日为单位"""
    """
        Positions计算逻辑：
        以计算日期为单位：
        成本价 = 该资金账户项下某股票的TradeLists的交易总额之和/持股数量
        持股数量 = 该资金账户项下某股票的TradeLists的股票买卖数量之和
        股票市值 = 持股数量 * 当日收盘价
        浮动盈亏 = （收盘价-成本价）* 持股数量
        end
        
        capitalAccount计算逻辑：
        资金余额 = 上一日资金余额+计算日买卖股票所有的支出
        总市值 = Positions中的所有股票市值之和
        总资产= 总市值 + 资金余额
        浮动盈亏 = Positions中的浮动盈亏之和
        期初资产 = 首次开户资产 + 银行转入资金
        end
        
        if第一次进行资金账户结算，
            总资产等于期初资产，总市值等于0，资金余额等于期初资产
            浮动盈亏等于0，总市值等于0。记账日为2017-1-1
        else
            按照上一交易日的数值进行叠加计算当日的资金账户总体情况。
    """

    recorder_num = Positions.objects.aggregate(position_num=Count('id'))  # 作用---定位Positions的最近的一条记录id号
    if recorder_num == 0:
        pass  # TODO:第一次进行账户结算，完成初始化功能
    else:
        position_id = recorder_num['position_num']

        account_num = Broker.objects.aggregate(account_num=Count('id'))  # 作用---获得资金账户数量

        end_date = date.today()  # django的语句比较简洁
        start_date = Positions.objects.get(id=position_id).date
        date_delta = (end_date - start_date).days
        # tushare接口获取交易日历
        # calendar = pro.query('trade_cal', start_date=start_date, end_date=end_date, is_open=1, fields=['cal_date'])
        # position_form = Positions(request.POST)
        for account_id in range(account_num['account_num'] + 1):
            position_date = start_date
            for _ in range(date_delta):  # 以交易日期轮询

                new_value_set = TradeLists.objects.filter(transaction_date=position_date, account_id=account_id).values(
                    'name').annotate(amount_num=Sum('quantity'),
                                     capital_num=Sum('total_capital'), )
                # 结算当日交易情况

                i = 0
                for _ in new_value_set.all():
                    position_name = new_value_set[i]['name']  # 股票代码
                    position_amount = new_value_set[i]['amount_num']  # 当日的该股票买卖数，需要计算库存数与该值之和。
                    position_total_capital = new_value_set[i]['capital_num']  # 当日该股所花费的总费用
                    position_id = position_id + 1  # 该表单的id自动加1

                    position_account_id = account_id  # 资金账户_id
                    position_cost = position_total_capital / position_amount  # 成本价
                    position_code = 1  # 获得该股票的代码
                    position_market_value = position_amount  # 获得该股票的收盘价
                    position_gain_loss = position_cost  # 收盘价-成本价
                    position_update_flag = True  # 是否更新标志

                    Positions.objects.create(id=position_id, name=position_name, code=position_code, date=position_date,
                                             cost=position_cost, amount=position_amount,
                                             market_value=position_market_value, gain_loss=position_gain_loss,
                                             account_id=position_account_id, update_flag=position_update_flag)

                    # position_form.id = position_id
                    # position_form.name = position_name
                    # position_form.code = position_code
                    # position_form.cost =position_cost
                    # position_form.amount = position_amount
                    # position_form.market_value = position_market_value
                    # position_form.gain_loss = postion_gain_loss
                    # position_form.account_id = position_account_id
                    # position_form.update_flag = position_update_flag
                    #
                    # position_form.save()

                    i = i + 1
                position_date = position_date + datetime.timedelta(days=1)

        return redirect('capital_management:index')
