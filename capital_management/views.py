# Create your views here.

from django.shortcuts import render, redirect
from .models import TradeLists, TradeDailyReport, CapitalAccount, AccountSurplus, Clearance
from .form import BrokerForm, TradeListsForm, CapitalAccountForm

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
            :param request:
            :return:
    """
    # 判断 CapitalAccount表是否存在
    check_capital_account_exists = CapitalAccount.objects.filter().exists()
    if check_capital_account_exists == 0:
        return redirect('capital_management:account')
    else:
        account_num = CapitalAccount.objects.aggregate(account_number=Count('id'))  # 获取资金账户数
        capital_account_number = account_num['account_number']
    # 判断TradeDailyReport表是否为空
    check_trade_daily_exist = TradeDailyReport.objects.filter().exists()
    if check_trade_daily_exist == 0:
        start_date = CapitalAccount.objects.get(id=1).date
        trade_daily_id = 0
    else:
        recorder_num = TradeDailyReport.objects.aggregate(
            trade_daily_num=Count('id'))  # 作用---定位TradeDailyReport的最近的一条记录id号
        trade_daily_id = recorder_num['trade_daily_num']
        start_date = TradeDailyReport.objects.get(id=trade_daily_id).date

    end_date = date.today()
    date_delta = (end_date - start_date).days + 1
    trade_daily_name = ""
    """交易日报结算功能"""
    for account_id in range(capital_account_number + 1):  # 以账户轮询
        if account_id != 0:
            trade_daily_date = start_date
            for _ in range(date_delta):  # 以交易日期轮询

                new_value_set = TradeLists.objects.filter(
                    transaction_date=trade_daily_date, account_id=account_id).values('code').annotate(
                    amount_num=Sum('quantity'), capital_num=Sum('total_capital'), fee_num=Sum('total_fee'))

                i = 0
                for _ in new_value_set.all():  # 取出查询结果，赋值。
                    trade_daily_id = trade_daily_id + 1  # 该表单的id自动加1
                    trade_daily_code = new_value_set[i]['code']  # 股票代码
                    # 获得股票名称
                    for _ in range(3):
                        try:
                            query_result = pro.query('stock_basic', ts_code=trade_daily_code, fields='name')
                        except:
                            time.sleep(1)
                        else:
                            trade_daily_name = query_result['name'].values[0]  # 股票名称

                    trade_daily_amount = new_value_set[i]['amount_num']  # 当日的该股票买卖数。
                    trade_daily_total_capital = round(new_value_set[i]['capital_num'], 2)  # 当日该股所花费的总金额
                    trade_daily_total_fee = round(new_value_set[i]['fee_num'], 2)
                    if trade_daily_amount == 0:
                        trade_daily_cost = 0
                    else:
                        trade_daily_cost = round(trade_daily_total_capital / trade_daily_amount, 2) * -1  # 成本价

                    trade_daily_account_id = account_id  # 资金账户_id
                    trade_daily_update_flag = True  # 是否更新标志
                    # 查找日报表，是否有更新，update_flag = True, 停止更新，否则，增加一条记录
                    flag = TradeDailyReport.objects.filter(date=trade_daily_date, code=trade_daily_code,
                                                           account_id=trade_daily_account_id).values('update_flag')
                    if flag:
                        return redirect('capital_management:trade')

                    else:
                        TradeDailyReport.objects.create(id=trade_daily_id, name=trade_daily_name, code=trade_daily_code,
                                                        date=trade_daily_date, cost=trade_daily_cost,
                                                        amount=trade_daily_amount,
                                                        total_capital=trade_daily_total_capital,
                                                        total_fee=trade_daily_total_fee,
                                                        account_id=trade_daily_account_id,
                                                        update_flag=trade_daily_update_flag)

                    i = i + 1

                trade_daily_date = trade_daily_date + datetime.timedelta(days=1)
    # 判断盈余账户是否存在
    check_account_surplue_exit = AccountSurplus.objects.filter().exists()
    if check_account_surplue_exit == 0:
        account_surplus_id = 0
    else:
        recorder_num = AccountSurplus.objects.aggregate(account_surplus_num=Count('id'))  # 获取盈余账户最新记录数, 定位。
        account_surplus_id = recorder_num['account_surplus_num']
    """账户盈余结算"""
    market_capital = 0
    total_fee = 0
    total_capital = 0
    position_gain_loss = 0
    stock_amount = 0
    stock_code = ""
    stock_close = 0
    clearance_stock_list = {}  # 清仓股票名单

    for account_id in range(capital_account_number + 1):  # 账户轮询
        if account_id != 0:

            account_surplus_data = TradeDailyReport.objects.filter(account_id=account_id).values(
                'code').annotate(stock_amount=Sum('amount'), stock_fee=Sum('total_fee'),
                                 stock_capital=Sum('total_capital'))
            if account_surplus_data.exists():  # 判断资金账户项下是否有数据，避免空转！！！太重要了！！！
                account_surplus_id = account_surplus_id + 1  # 该表单 id自动加1
                i = 0
                for _ in account_surplus_data.all():
                    stock_amount = stock_amount + account_surplus_data[i]['stock_amount']
                    stock_code = account_surplus_data[i]['code']
                    # tushare 获取股票名称
                    for _ in range(3):
                        try:
                            query_result = pro.query('daily', ts_code=stock_code, start_date=end_date, end_date=end_date)
                        except:
                            time.sleep(1)
                        else:
                            stock_close = query_result['close'].values[0]
                    # 账户总市值= 个股市值之和；close 收盘价，计算个股市值
                    market_capital = market_capital + account_surplus_data[i]['stock_amount'] * stock_close
                    # 账户总费用= 每个股票费用之和
                    total_fee = total_fee + account_surplus_data[i]['stock_fee']
                    # 账户总交易金额
                    total_capital = total_capital + account_surplus_data[i]['stock_capital']
                    # 账户浮动盈亏
                    stock_position_gain_loss = \
                        account_surplus_data[i]['stock_amount'] * stock_close - account_surplus_data[i]['stock_capital']
                    position_gain_loss = position_gain_loss + stock_position_gain_loss*-1

                    # 账户个股成本计算
                    # if account_surplus_data[i]['amount'] != 0:
                    #     cost = (account_surplus_data[i][['stock_capital']] -
                    #             account_surplus_data[i]['stock_amount'])/account_surplus_data[i]['amount']
                    # else:
                    #     cost = 0
                    #

                    i = i + 1
                # 待清算股票名单 使用字典：{stock_code:account_id}
                if stock_amount == 0:
                    clearance_stock_list[stock_code] = account_id

                # 期初资产
                initial_capital = CapitalAccount.objects.get(id=account_id).initial_capital
                fund_balance = initial_capital + total_capital  # 资金余额
                # 总资产
                total_assets = fund_balance + market_capital
                update_flag = True

                # 查找AccountSurplus表，是否有更新，update_flag = True, 停止更新，否则，增加一条记录
                flag = AccountSurplus.objects.filter(date=end_date, name_id=account_id).values(
                    'update_flag')
                if flag:
                    return redirect('capital_management:dashboard')
                else:
                    AccountSurplus.objects.create(id=account_surplus_id, total_assets=total_assets, total_fee=total_fee,
                                                  name_id=account_id, market_capital=market_capital,
                                                  fund_balance=fund_balance, position_gain_loss=position_gain_loss,
                                                  initial_capital=initial_capital, date=end_date,
                                                  update_flag=update_flag)

    """清仓股票结算"""
    clearance_id = 1
    invest_capital_r = 0
    invest_capital_b = 0
    profit = 0
    stock_name = ""

    for stock_code, account_id in clearance_stock_list.items():
        clearance_data = TradeDailyReport.objects.filter(code=stock_code, account_id=account_id).values(
            'code').annotate(
            transfer_fee=Sum('total_fee'), profit=Sum('total_capital'))  # 计算 建仓日期，交易费用
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

        # tushare 获取股票名称
        for _ in range(3):
            try:
                query_result = pro.query('stock_basic', ts_code=stock_code, fields='name')
            except:
                time.sleep(1)
            else:
                stock_name = query_result['name'].values[0]
        Clearance.objects.create(id=clearance_id, code=stock_code, name=stock_name, open_date=open_date, clear_date=end_date,
                                 invest_capital=invest_capital, fee=total_fee, profit=profit, account_id=account_id)

        clearance_id = clearance_id + 1
    return redirect('capital_management:index')
