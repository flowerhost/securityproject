# Create your views here.

from django.shortcuts import render, redirect
from .models import TradeLists, TradeDailyReport, CapitalAccount, AccountSurplus, Clearance, TradePerformance, Broker
from .form import BrokerForm, TradeListsForm, CapitalAccountForm

from django.db.models import Sum

import time
import datetime

"""tushare类数据接口"""
import tushare as ts

ts.set_token('033ad3c72aef8ce38d29d34482058b87265b32d788fb6f24d2e0e8d6')
pro = ts.pro_api()


def index(request):
    stocks = TradeLists.objects.values(
        'code', 'name', 'price', 'flag', 'date', 'trade_resource', 'quantity', 'total_capital',
        'account__broker__capitalaccount__name', 'tradeperformance__close', 'tradeperformance__moving_average',
        'tradeperformance__performance', )

    return render(request, 'capital_management/index.html', locals())


def dashboard(request):
    pass
    return render(request, 'capital_management/dashboard.html', locals())


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
            # 修正股票数量
            if new_trade.flag == 'S':
                new_trade.quantity = new_trade.quantity * -1
            elif new_trade.flag == 'T':
                new_trade.quantity = new_trade.quantity * -1
            else:
                new_trade.quantity = new_trade.quantity

            # 计算印花税
            if new_trade.flag == 'B':
                new_trade.stamp_duty = 0
            elif new_trade.flag == 'R':
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
            if new_trade.flag == 'B':
                new_trade.total_capital = round(total_capital + new_trade.total_fee, 2) * -1
            elif new_trade.flag == 'R':
                new_trade.total_capital = round(total_capital + new_trade.total_fee, 2) * -1
            else:
                new_trade.total_capital = round(total_capital - new_trade.total_fee, 2)

            new_trade.save()

            return redirect('capital_management:index')

    context = {'trade_form': trade_form}
    return render(request, 'capital_management/trade.html', context)


def account(request):
    """资金账户"""

    if request.method != 'POST':
        account_form = CapitalAccountForm()
    else:
        account_form = CapitalAccountForm(request.POST)
        if account_form.is_valid():
            account_form.save()
            return redirect('capital_management:dashboard')
    context = {'account_form': account_form}
    return render(request, 'capital_management/account.html', context)


def balance(request):
    """资金账户结算功能，以交易日为单位"""
    """
            更新所有收盘后的数据表：
               1、持股数据表:      TradeDailyReport(models.Model)
               2、清仓数据表:      Clearance(models.Model)
               3、账户资产管理:    AccountSurplus(models.Model)
               4、买卖表现评价
            :param request:
            :return:
    """

    """基础数据表验证"""
    # 1.判断券商信息是否存在
    if not Broker.objects.exists():
        return redirect('capital_management:broker')

    # 2.判断资金账号是否存在
    if not CapitalAccount.objects.exists():
        return redirect('capital_management:account')

    # 3.判断日交易流水表是否为空
    if not TradeLists.objects.exists():
        return redirect('capital_management:trade')

    """交易日报TradeDailyReport结算功能"""
    trade_daily_name = ""
    # 1.判断TradeDailyReport状态
    if TradeDailyReport.objects.exists():
        # daily_report_date_cursor = TradeDailyReport.objects.latest().date
        # daily_report_end_date = TradeLists.objects.latest().date
        trade_daily_id_cursor = TradeDailyReport.objects.latest().id
    else:
        # daily_report_date_cursor = TradeLists.objects.earliest().date
        # daily_report_end_date = TradeLists.objects.latest().date
        trade_daily_id_cursor = 0
    # 2.运算解析数据
    new_value_set = TradeLists.objects.values('date', 'account_id', 'code').annotate(
        amount_num=Sum('quantity'), capital_num=Sum('total_capital'), fee_num=Sum('total_fee'))
    for new_value in new_value_set:
        trade_daily_code = new_value['code']
        # 获得股票名称
        for _ in range(3):
            try:
                query_result = pro.query('stock_basic', ts_code=trade_daily_code, fields='name')
            except:
                time.sleep(1)
            else:
                trade_daily_name = query_result['name'].values[0]  # 股票名称

        trade_daily_amount = new_value['amount_num']  # 当日的买卖某股票的股数。
        trade_daily_total_capital = round(new_value['capital_num'], 2)  # 当日该股所花费的总金额
        trade_daily_total_fee = round(new_value['fee_num'], 2)
        if trade_daily_amount == 0:
            trade_daily_cost = 0
        else:
            trade_daily_cost = round(trade_daily_total_capital / trade_daily_amount, 2) * -1  # 成本价

        trade_daily_account_id = new_value['account_id']  # 资金账户_id
        trade_daily_update_flag = True  # 是否更新标志
        trade_daily_id_cursor = trade_daily_id_cursor + 1
        daily_report_date_cursor = new_value['date']

        TradeDailyReport.objects.create(id=trade_daily_id_cursor, name=trade_daily_name, code=trade_daily_code,
                                        date=daily_report_date_cursor, cost=trade_daily_cost, amount=trade_daily_amount,
                                        total_capital=trade_daily_total_capital, total_fee=trade_daily_total_fee,
                                        account_id=trade_daily_account_id, update_flag=trade_daily_update_flag)

    """账户盈余AccountSurplus结算功能"""
    # 1.判断AccountSurplus状态
    if AccountSurplus.objects.exists():
        account_surplus_id_cursor = AccountSurplus.objects.latest().id
    else:
        account_surplus_id_cursor = 0

    market_capital = 0
    total_fee = 0
    total_capital = 0
    position_gain_loss = 0
    stock_close = 0
    account_surplus_account_id = 0
    clearance_stock_list = {}  # 清仓股票名单
    statistic_date = TradeDailyReport.objects.latest().date  # 结算日起不够准确，目前以日报表的最新日期为统计截止日

    account_surplus_data = TradeDailyReport.objects.values('account_id', 'code').annotate(
        stock_amount=Sum('amount'), stock_fee=Sum('total_fee'), stock_capital=Sum('total_capital'))

    for account_surplus in account_surplus_data:
        stock_code = account_surplus['code']
        # 记录清仓股票和账号 字典{stock_code:account_id}
        if account_surplus['stock_amount'] == 0:  # 一个大坑！害得我抓狂！
            clearance_stock_list[stock_code] = account_surplus['account_id']

        # tushare 获取股票收盘价
        for _ in range(3):
            try:
                query_result = pro.query('daily', ts_code=stock_code, start_date=statistic_date.strftime(
                    "%Y%m%d"), end_date=statistic_date.strftime("%Y%m%d"))
            except:
                time.sleep(1)
            else:
                stock_close = query_result['close'].values[0]
        account_surplus_account_id = account_surplus['account_id']
        # 账户总市值= 个股市值之和；close 收盘价，计算个股市值
        market_capital = market_capital + account_surplus['stock_amount'] * stock_close
        # 账户总费用= 每个股票费用之和
        total_fee = total_fee + account_surplus['stock_fee']
        # 账户总交易金额
        total_capital = total_capital + account_surplus['stock_capital']
        # 账户浮动盈亏
        stock_position_gain_loss = account_surplus['stock_amount'] * stock_close - account_surplus['stock_capital']
        position_gain_loss = position_gain_loss + stock_position_gain_loss * -1

    # 期初资产
    initial_capital = CapitalAccount.objects.get(id=account_surplus_account_id).initial_capital
    fund_balance = initial_capital + total_capital  # 资金余额
    # 总资产
    total_assets = round(fund_balance + market_capital, 2)
    update_flag = True
    account_surplus_id_cursor = account_surplus_id_cursor + 1  # 该表单 id自动加1

    AccountSurplus.objects.create(id=account_surplus_id_cursor, total_assets=total_assets, total_fee=total_fee,
                                  account_id=account_surplus_account_id, market_capital=market_capital,
                                  fund_balance=fund_balance, position_gain_loss=position_gain_loss,
                                  initial_capital=initial_capital, date=statistic_date, update_flag=update_flag)

    """清仓股票结算"""
    clearance_id_cursor = 1
    invest_capital_r = 0
    invest_capital_b = 0
    profit = 0
    stock_name = ""

    for stock_code, account_id in clearance_stock_list.items():

        clearance_data = TradeDailyReport.objects.filter(code=stock_code, account_id=account_id).values(
            'code').annotate(
            transfer_fee=Sum('total_fee'), profit=Sum('total_capital'))  # 计算 建仓日期，交易费用
        # 计算 利润和总费用
        clearance_id_cursor = clearance_id_cursor + 1
        if clearance_data.exists():
            profit = clearance_data[0]['profit']
            total_fee = clearance_data[0]['transfer_fee']

        # 计算股票总投入 invest_capital
        clearance_data = TradeLists.objects.filter(
            account_id=account_id, flag='B', code=stock_code).values('code').annotate(
            invest_capital=Sum('total_capital'))
        if clearance_data.exists():
            invest_capital_b = clearance_data[0]['invest_capital']
        clearance_data = TradeLists.objects.filter(
            account_id=account_id, flag='R', code=stock_code).values('code').annotate(
            invest_capital=Sum('total_capital'))
        if clearance_data.exists():
            invest_capital_r = clearance_data[0]['invest_capital']
        invest_capital = (invest_capital_b + invest_capital_r) * -1
        open_date = TradeDailyReport.objects.filter(code=stock_code, account_id=account_id).earliest().date
        clear_date = TradeDailyReport.objects.filter(code=stock_code, account_id=account_id).latest().date
        # tushare 获取股票名称
        for _ in range(3):
            try:
                query_result = pro.query('stock_basic', ts_code=stock_code, fields='name')
            except:
                time.sleep(1)
            else:
                stock_name = query_result['name'].values[0]

        # 有问题，已经清仓的股票，再次建仓，清仓，其第二次结算的数据不准确反映第二次操作水平。
        if not Clearance.objects.exists():
            Clearance.objects.create(id=clearance_id_cursor, code=stock_code, name=stock_name, open_date=open_date,
                                     clear_date=clear_date, invest_capital=invest_capital, fee=total_fee, profit=profit,
                                     account_id=account_id)
        else:
            flag = Clearance.objects.filter(clear_date=clear_date, open_date=open_date, code=stock_code,
                                            account_id=account_id)
            if flag:
                pass
            else:
                Clearance.objects.create(id=clearance_id_cursor, code=stock_code, name=stock_name, open_date=open_date,
                                         clear_date=clear_date, invest_capital=invest_capital, fee=total_fee,
                                         profit=profit,
                                         account_id=account_id)

    """Performance交易表现评价"""
    close = 0
    high_price = 0
    low_price = 0
    moving_average = 0
    boll_up = 0
    boll_down = 0
    performance = 0
    trade_performance = 0

    # 判断 Performance表状态
    if TradePerformance.objects.exists():
        performance_id_cursor = TradePerformance.objects.latest().id
        performance_score_date = TradePerformance.objects.latest().date
    else:
        performance_id_cursor = 0
        performance_score_date = TradeLists.objects.earliest().date

    performance_ma_date = performance_score_date - datetime.timedelta(days=30)  # 获取tushare均线值用
    # 获取TradeLists交易流水数据
    latest_date = TradeLists.objects.latest().date

    while performance_score_date <= latest_date:
        performance_data_set = TradeLists.objects.filter(date=performance_score_date).values('id', 'code', 'price',
                                                                                             'flag')

        for performance_data in performance_data_set:
            if performance_data_set.exists():
                performance_id_cursor = performance_id_cursor + 1
                performance_code = performance_data['code']
                performance_trade_id = performance_data['id']
                performance_price = performance_data['price']
                performance_flag = performance_data['flag']  # 用于计算交易表现分值--performance
                if performance_flag == 'B':
                    p_flag = True
                elif performance_flag == 'R':
                    p_flag = True
                else:
                    p_flag = False

                for _ in range(10):
                    # 获得股票收盘数据
                    try:
                        query_result = ts.pro_bar(ts_code=performance_code, adj='qfg', ma=[10],
                                                  start_date=performance_ma_date.strftime("%Y%m%d"),
                                                  end_date=performance_score_date.strftime("%Y%m%d"))
                    except:
                        time.sleep(1)
                    else:
                        close = query_result['close'][0]
                        high_price = query_result['high'].values[0]
                        low_price = query_result['low'].values[0]
                        moving_average = query_result['ma10'].values[0]
                        boll_up = round(moving_average * 1.08, 2)
                        boll_down = round(moving_average * 0.92, )

                        performance = round((performance_price - low_price) / (high_price - low_price), 2)
                        # 换算买入表现分值，使得其意义与卖入表现分值所代表的意义一致，分值越高，其表现越好。
                        if p_flag:
                            performance = round((1 - performance), 2)

                if not TradePerformance.objects.exists():
                    TradePerformance.objects.create(id=performance_id_cursor, close=close,
                                                    moving_average=moving_average,
                                                    high_price=high_price, low_price=low_price, boll_up=boll_up,
                                                    boo_down=boll_down, performance=performance,
                                                    trade_id=performance_trade_id,
                                                    trade_performance=trade_performance, date=performance_score_date)
                else:
                    flag = TradePerformance.objects.filter(trade_id=performance_trade_id)
                    if flag:
                        pass
                    else:
                        TradePerformance.objects.create(id=performance_id_cursor, close=close,
                                                        moving_average=moving_average,
                                                        high_price=high_price, low_price=low_price, boll_up=boll_up,
                                                        boo_down=boll_down, performance=performance,
                                                        trade_id=performance_trade_id,
                                                        trade_performance=trade_performance,
                                                        date=performance_score_date)

        performance_score_date = performance_score_date + datetime.timedelta(days=1)

    return redirect('capital_management:index')
