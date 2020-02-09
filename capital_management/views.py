# Create your views here.

from django.shortcuts import render, redirect
from .models import TradeLists, CapitalAccount, Broker
from .form import BrokerForm, TradeListsForm

# from django.db.models import Sum

from datetime import date

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

            # 获取股票名称

            query_result = pro.query('stock_basic', ts_code=new_trade.code, fields='name')
            new_trade.name = query_result['name'].values[0]

            # 计算成交金额
            total_capital = round(new_trade.quantity*new_trade.price, 2)

            # 计算印花税
            if new_trade.flag == 'B':
                new_trade.stamp_duty = 0
            else:
                new_trade.stamp_duty = round(total_capital*0.001, 2)

            # 计算券商佣金
            brokerage = round(total_capital*0.00025, 2)
            if brokerage < 1:
                new_trade.brokerage = 0
            else:
                new_trade.brokerage = brokerage

            # 计算过户费
            transfer_fee = round(total_capital*0.00002, 2)
            if transfer_fee >= 5:
                new_trade.transfer_fee = transfer_fee
            else:
                new_trade.transfer_fee = 5

            # 手续费总计
            new_trade.total_fee = round(new_trade.stamp_duty+new_trade.transfer_fee+new_trade.brokerage, 2)

            # 交易总额
            new_trade.total_capital = round(total_capital+new_trade.brokerage+new_trade.transfer_fee
                                            + new_trade.stamp_duty, 2)

            new_trade.save()

            return redirect('capital_management:index')

    context = {'trade_form': trade_form}
    return render(request, 'capital_management/trade.html', context)


def balance(request, capital_account_id):
    """资金账户结算功能，以交易日为单位"""
    """
        Positions计算逻辑：
        以计算日期为单位：
        成本价 = 该资金账户项下某股票的TradeLists的交易总额之和/股票数量
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
    current_date = date.today().strftime("%Y-%m-%d")
    balanced_date = CapitalAccount.date
    form = CapitalAccount()

    if current_date == balanced_date:

        return redirect('capital_management:index')
    elif current_date == '2017-01-01':
        initial_capital = 1000000

        form.initial_capital = initial_capital
        form.total_assets = CapitalAccount.initial_capital
        form.market_capital = 0
        form.fund_balance = CapitalAccount.initial_capital
        form.position_gain_loss = 0
        form.date = date.today()
        form.broker = Broker.objects.get(capital_account_id)

        form.save()

        return redirect('capital_management:index')
    # TODO: 继续完成结算功能 以结算日期为条件
    # else:
    #     total_assets = market_capital + fund_balance
