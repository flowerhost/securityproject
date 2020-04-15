# Create your views here.

from django.shortcuts import render, redirect
from .models import TradeLists, TradeDailyReport, CapitalAccount, AccountSurplus, Clearance, TradePerformance, Broker
from .models import Positions, CapitalManagement, EvaluateStocks, CumulativeRank
from .form import BrokerForm, TradeListsForm, CapitalAccountForm

from django.db.models import Sum

import sqlite3
import time
import datetime
import pandas as pd

"""tushare类数据接口"""
import tushare as ts

ts.set_token('033ad3c72aef8ce38d29d34482058b87265b32d788fb6f24d2e0e8d6')
pro = ts.pro_api()


def index(request):
    stocks = TradeLists.objects.values(
        'code', 'name', 'price', 'flag', 'date', 'trade_resource', 'quantity', 'total_capital',
        'account__name', 'tradeperformance__close', 'tradeperformance__moving_average',
        'tradeperformance__performance', ).order_by('-date')

    return render(request, 'capital_management/index.html', locals())


def dashboard(request):
    """仪表盘，主要展示监控资金账户和股票总体表现情况"""
    # 资金账户总体情况
    category = ['浮动盈亏', '资金余额', '总市值', '总资产']
    capital_date = []
    gain_data = []
    balance_data = []
    capital_data = []
    assets_data = []
    legend_data = []

    # demo 测试数据
    data_date = ['日期']
    assets = ['总资产']
    fund_balance = ['资金余额']
    gain_loss = ['浮动盈亏']
    final_cost = ['总投入']
    total = []

    # 个股市值 Positions
    stock_lists = []
    stock_value = []
    stock_name = []
    nut = []

    # 持仓情况-->Positions
    if Positions.objects.exists():
        pass
    else:
        return redirect('capital_management:balance')
    # 账户盈余情况-->AccountSurplus
    if not AccountSurplus.objects.exists():
        return redirect('capital_management:balance')
    else:
        total_assets = AccountSurplus.objects.values('total_assets').latest()  # 最新日期的总资产
        market_capital = AccountSurplus.objects.values('market_capital').latest()  # 最新的总市值
        balance = AccountSurplus.objects.values('fund_balance').latest()  # 最新的资金余额
        position_gain_loss = AccountSurplus.objects.values('position_gain_loss').latest()  # 最新的浮动盈亏

        market_capital_percentage = round(market_capital['market_capital'] / total_assets['total_assets'], 2)  # 仓位比例
        gain_loss_percentage = round(position_gain_loss['position_gain_loss'] / total_assets['total_assets'], 2)
        asset_trend = AccountSurplus.objects.values('date', 'total_assets')  # 资产走势图

        # Positions仓位情况的展示 Donut
        positions_date = Positions.objects.latest().date
        surplus_id = AccountSurplus.objects.latest().id
        positions_data = Positions.objects.filter(date=positions_date).values('name').annotate(
            amount=Sum('amount'), capital=Sum('market_capital'))
        surplus_balance = AccountSurplus.objects.get(id=surplus_id)
        for stock in positions_data:
            if stock['amount'] == 0:
                pass
            else:
                stock_lists.append(stock['name'])
                stock_value.append(stock['capital'])
                stock_name.append(stock['name'])
                donut = {'value': stock['capital'], 'name': stock['name']}
                nut.append(donut)
        donut = {'value': surplus_balance.fund_balance, 'name': '资金余额'}
        nut.append(donut)
        stock_lists.append('资金余额')

        # 资金账户总体情况展示
        charts_date = (datetime.date.today() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
        total_data = AccountSurplus.objects.filter(date__gte=charts_date).values(
            'total_assets', 'final_cost', 'market_capital', 'fund_balance', 'position_gain_loss', 'date')
        for account_data in total_data:
            capital_date.append(account_data['date'].strftime("%b%d"))
            gain_data.append(round(account_data['position_gain_loss'] / 10000, 2))
            balance_data.append(round(account_data['fund_balance'] / 10000, 2))
            capital_data.append(round(account_data['market_capital'] / 10000, 2))
            assets_data.append(round(account_data['total_assets'] / 10000, 2))
        account_gain = {'name': '浮动盈亏', 'type': 'line', 'stack': '总量', 'areaStyle': {}, 'data': gain_data}
        account_balance = {'name': '资金余额', 'type': 'line', 'stack': '总量', 'areaStyle': {}, 'data': balance_data}
        capital = {'name': '总市值', 'type': 'line', 'stack': '总量', 'areaStyle': {}, 'data': capital_data}
        account_asset = {'name': '总资产', 'type': 'line', 'stack': '总量', 'areaStyle': {}, 'data': assets_data}
        legend_data.append(account_gain)
        legend_data.append(account_balance)
        legend_data.append(capital)
        legend_data.append(account_asset)

        """测试 eCharts 饼图+折线图 demo"""
        for data in total_data:
            month_day = data['date'].strftime("%b%d")
            data_date.append(month_day)
            assets.append(round(data['total_assets'] / 10000, 2))
            fund_balance.append(round(data['fund_balance'] / 10000, 2))
            gain_loss.append(round(data['position_gain_loss'] / 10000, 2))
            final_cost.append(round(data['final_cost'] / (-10000), 2))

        total.append(data_date)
        total.append(assets)
        total.append(final_cost)
        total.append(fund_balance)
        total.append(gain_loss)
        start_day = total[0][-1]
        """end eCharts demo测试"""

        context = {'total': total, 'start_day': start_day, 'stock_lists': stock_lists, 'nut': nut,
                   'legend_data': legend_data, 'capital_date': capital_date, 'category': category}
    return render(request, 'capital_management/dashboard.html', context)


def line(request):
    """个股均线分析"""
    error_msg = ""
    stock_name = ""
    data = []
    query_date = datetime.date.today()
    start_query_date = query_date - datetime.timedelta(weeks=120)

    if request.method == "POST":
        stock_code = request.POST.get("stock_code")
        for _ in range(3):
            try:
                query_result = pro.query('stock_basic', ts_code=stock_code, fields='name')
                line_data = ts.pro_bar(ts_code=stock_code, freq='D', start_date=start_query_date.strftime("%Y%m%d"),
                                       end_date=query_date.strftime("%Y%m%d"), adj='qfq')
            except:
                time.sleep(0)
            else:
                stock_name = query_result['name'].values[0]
                reverse_line_data = line_data.sort_values(by=['trade_date'], ascending=[True])
                data = reverse_line_data[['trade_date', 'open', 'close', 'low', 'high']].values.tolist()

        context = {'line_data': data, 'stock_name': stock_name}
        return render(request, 'capital_management/line.html', context)

    return render(request, 'capital_management/line.html', {'error_msg': error_msg})


def broker(request):
    if request.method != 'POST':
        broker_form = BrokerForm()
    else:
        broker_form = BrokerForm(request.POST)
        if broker_form.is_valid():
            broker_form.save()
            return redirect('capital_management:account')

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
            return redirect('capital_management:trade')
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
    # 1.判断TradeDailyReport状态
    if TradeDailyReport.objects.exists():
        daily_report_date_cursor = TradeDailyReport.objects.latest().date
        trade_daily_id_cursor = TradeDailyReport.objects.last().id
    else:
        daily_report_date_cursor = TradeLists.objects.earliest().date
        trade_daily_id_cursor = 0
    # 2.运算解析数据
    new_value_set = TradeLists.objects.filter(
        date__gte=daily_report_date_cursor).values('date', 'account_id', 'code', 'name').annotate(
        amount_num=Sum('quantity'), capital_num=Sum('total_capital'), fee_num=Sum('total_fee'))
    for new_value in new_value_set:
        trade_daily_date = new_value['date']
        trade_daily_code = new_value['code']
        trade_daily_account_id = new_value['account_id']  # 资金账户_id

        flag = TradeDailyReport.objects.filter(
            date=trade_daily_date, code=trade_daily_code, account_id=trade_daily_account_id)
        # 避免重复写数据。
        if flag:
            pass
        else:
            trade_daily_id_cursor = trade_daily_id_cursor + 1
            trade_daily_name = new_value['name']

            trade_daily_amount = new_value['amount_num']  # 当日的买卖某股票的股数。
            trade_daily_total_capital = round(new_value['capital_num'], 2)  # 当日该股所花费的总金额
            trade_daily_total_fee = round(new_value['fee_num'], 2)
            if trade_daily_amount == 0:
                trade_daily_cost = 0
            else:
                trade_daily_cost = round(trade_daily_total_capital / trade_daily_amount, 2) * -1  # 成本价

            TradeDailyReport.objects.create(id=trade_daily_id_cursor, name=trade_daily_name, code=trade_daily_code,
                                            date=trade_daily_date, cost=trade_daily_cost, amount=trade_daily_amount,
                                            total_capital=trade_daily_total_capital, total_fee=trade_daily_total_fee,
                                            account_id=trade_daily_account_id, update_flag=True)

    """账户盈余AccountSurplus结算功能"""
    # 1.判断AccountSurplus状态
    if AccountSurplus.objects.exists():
        account_surplus_id_cursor = AccountSurplus.objects.latest().id
        start_date = AccountSurplus.objects.latest().date
    else:
        account_surplus_id_cursor = 0
        start_date = TradeDailyReport.objects.earliest().date

    # 2.判断Positions状态
    if Positions.objects.exists():
        positions_id_cursor = Positions.objects.last().id  # 只能取最新日期的第一条记录 latest().id
    else:
        positions_id_cursor = 0

    """判断提取数据时间"""
    # 如果是17：00之前，提取前一交易日数据
    check_time = datetime.datetime.strptime(str(datetime.date.today()) + '17:00', '%Y-%m-%d%H:%M')
    now_time = datetime.datetime.now()
    if now_time < check_time:
        statistic_date = datetime.date.today() - datetime.timedelta(days=1)
    else:
        statistic_date = datetime.date.today()

    # 获取交易日历
    calendar = []
    for _ in range(3):
        try:
            calendar = pro.query('trade_cal', start_date=start_date.strftime("%Y%m%d"),
                                 end_date=statistic_date.strftime("%Y%m%d"), is_open=1, fields=['cal_date'])
        except:
            time.sleep(1)

    for cal in calendar.values:  # 遵照交易日历来结算
        # 局部变量
        market_capital = 0
        total_fee = 0
        total_capital = 0
        position_gain_loss = 0
        stock_close = 0
        account_surplus_account_id = 0

        date_cursor = datetime.datetime.strptime(cal[0], "%Y%m%d").strftime("%Y-%m-%d")
        flag = AccountSurplus.objects.filter(date=date_cursor)
        # 避免重复写数据
        if flag:
            pass
        else:
            account_surplus_data = TradeDailyReport.objects.filter(date__lte=date_cursor).values(
                'account_id', 'code', 'name').annotate(stock_amount=Sum('amount'), stock_fee=Sum('total_fee'),
                                                       stock_capital=Sum('total_capital'))
            for account_surplus in account_surplus_data:
                account_surplus_account_id = account_surplus['account_id']
                stock_code = account_surplus['code']
                stock_name = account_surplus['name']
                # tushare 获取股票当日收盘价
                for _ in range(3):
                    try:
                        query_result = pro.query('daily', ts_code=stock_code, start_date=cal[0], end_date=cal[0])
                    except:
                        time.sleep(1)
                    else:
                        stock_close = query_result['close'].values[0]

                # 账户总市值= 个股市值之和；close 收盘价，计算个股市值
                stock_amount = account_surplus['stock_amount']
                stock_market_capital = round(stock_amount * stock_close, 2)
                market_capital = round(market_capital + stock_market_capital, 2)
                # 账户总费用= 每个股票费用之和
                stock_fee = round(account_surplus['stock_fee'], 2)
                total_fee = round(total_fee + stock_fee, 2)
                stock_capital = round(account_surplus['stock_capital'], 2)  # 个股投入资金成本，有正负号区分，买入为负，卖出为正。
                total_capital = round((total_capital + stock_capital), 2)
                # 个股的每股成本价
                if stock_amount == 0:
                    stock_cost = 0
                else:
                    stock_cost = round(stock_capital / stock_amount * -1, 2)
                # 账户浮动盈亏
                stock_position_gain_loss = round((stock_amount * stock_close + stock_capital), 2)
                position_gain_loss = round((position_gain_loss + stock_position_gain_loss), 2)
                stock_open_date = TradeDailyReport.objects.filter(code=stock_code).earliest().date

                # 股票持仓情况更新
                # 完成二次建仓功能，避免重复计算前次清仓股票重复计算。
                # 思路：找到清仓股票表中最新的清仓日期。从清仓日期开始计算股数和成本等数据。
                if stock_amount != 0:
                    flag = Clearance.objects.filter(code=stock_code, account_id=account_surplus_account_id)
                    if flag:
                        check_date = Clearance.objects.filter(
                            code=stock_code, account_id=account_surplus_account_id).latest().clear_date

                        position_values = TradeDailyReport.objects.filter(
                            date__gt=check_date, date__lte=date_cursor, code=stock_code,
                            account_id=account_surplus_account_id).values('account_id', 'code', 'name').annotate(
                            stock_amount=Sum('amount'), stock_fee=Sum('total_fee'), stock_capital=Sum('total_capital'))
                        for position_values_data in position_values:
                            stock_amount = position_values_data['stock_amount']
                            stock_market_capital = round(stock_amount * stock_close, 2)
                            stock_fee = round(position_values_data['stock_fee'], 2)
                            stock_capital = round(position_values_data['stock_capital'], 2)
                            stock_cost = round(stock_capital / stock_amount * -1, 2)
                            stock_position_gain_loss = round((stock_amount * stock_close + stock_capital), 2)
                            stock_open_date = TradeDailyReport.objects.filter(
                                code=stock_code, date__gt=check_date, date__lte=date_cursor,
                                account_id=account_surplus_account_id).earliest().date
                    # 避免重复写数据Positions
                    check_positions = Positions.objects.filter(
                        account_id=account_surplus_account_id, code=stock_code, date=date_cursor)
                    if check_positions:
                        pass
                    else:
                        positions_id_cursor = positions_id_cursor + 1
                        Positions.objects.create(id=positions_id_cursor, account_id=account_surplus_account_id,
                                                 code=stock_code, market_capital=stock_market_capital,
                                                 name=stock_name, cost=stock_cost, amount=stock_amount, fee=stock_fee,
                                                 gain_loss=stock_position_gain_loss, date=date_cursor,
                                                 open_date=stock_open_date, final_cost=stock_capital)
                else:  # Clearance清仓股票计算。
                    invest_capital_r = 0
                    invest_capital_b = 0
                    profit = 0
                    if Clearance.objects.exists():
                        clearance_id_cursor = Clearance.objects.last().id
                    else:
                        clearance_id_cursor = 0
                    # 判断是否已结算过，避免重复写数据。
                    flag = Clearance.objects.filter(
                        code=stock_code, account_id=account_surplus_account_id, clear_date=date_cursor)
                    if flag:
                        pass
                    else:
                        # 建仓日期
                        open_date = TradeDailyReport.objects.filter(
                            account_id=account_surplus_account_id, code=stock_code).earliest().date
                        # 清仓日期
                        clear_date = TradeDailyReport.objects.filter(
                            account_id=account_surplus_account_id, code=stock_code, date__lte=date_cursor).latest().date
                        # 判断是否为二次建仓
                        check_flag = Clearance.objects.filter(code=stock_code, account_id=account_surplus_account_id)
                        if check_flag:
                            check_date = Clearance.objects.filter(
                                code=stock_code, account_id=account_surplus_account_id).latest().clear_date
                            open_flag = TradeDailyReport.objects.filter(
                                account_id=account_surplus_account_id, code=stock_code, date__lte=date_cursor,
                                date__gt=check_date)
                            if open_flag:
                                open_date = TradeDailyReport.objects.filter(
                                    account_id=account_surplus_account_id, code=stock_code, date__lte=date_cursor,
                                    date__gt=check_date).earliest().date
                            else:
                                open_date = TradeDailyReport.objects.filter(
                                    account_id=account_surplus_account_id, code=stock_code,
                                    date__lte=date_cursor).earliest().date
                        # 获取一个交易周期区间数据
                        clearance_data = TradeDailyReport.objects.filter(
                            code=stock_code, account_id=account_surplus_account_id, date__gte=open_date,
                            date__lte=date_cursor).values('code').annotate(
                            transfer_fee=Sum('total_fee'), profit=Sum('total_capital'))
                        # 计算利润和总费用
                        if clearance_data.exists():
                            profit = round(clearance_data[0]['profit'], 2)
                            total_fee = round(clearance_data[0]['transfer_fee'], 2)

                        # 计算股票总投入 invest_capital
                        # 按照普通买入-B来计算
                        clearance_data = TradeLists.objects.filter(
                            account_id=account_surplus_account_id, flag='B', code=stock_code, date__gte=open_date,
                            date__lte=clear_date).values('code').annotate(invest_capital=Sum('total_capital'))
                        if clearance_data.exists():
                            invest_capital_b = clearance_data[0]['invest_capital']
                        # 按照融资买入-R来计算
                        clearance_data = TradeLists.objects.filter(
                            account_id=account_surplus_account_id, flag='R', code=stock_code, date__gte=open_date,
                            date__lte=clear_date).values('code').annotate(invest_capital=Sum('total_capital'))
                        if clearance_data.exists():
                            invest_capital_r = clearance_data[0]['invest_capital']
                        # 计算总投入资金数
                        invest_capital = round((invest_capital_b + invest_capital_r) * -1, 2)
                        # 记录清仓股票数据
                        clearance_id_cursor = clearance_id_cursor + 1
                        if not Clearance.objects.exists():
                            Clearance.objects.create(id=clearance_id_cursor, code=stock_code, name=stock_name,
                                                     open_date=open_date, clear_date=clear_date, fee=total_fee,
                                                     invest_capital=invest_capital, profit=profit,
                                                     account_id=account_surplus_account_id)
                        else:
                            clear_flag = Clearance.objects.filter(
                                clear_date=clear_date, code=stock_code, account_id=account_surplus_account_id)
                            if clear_flag:
                                pass
                            else:
                                Clearance.objects.create(id=clearance_id_cursor, code=stock_code, name=stock_name,
                                                         open_date=open_date, clear_date=clear_date, fee=total_fee,
                                                         invest_capital=invest_capital, profit=profit,
                                                         account_id=account_surplus_account_id)

            # 期初资产
            initial_capital = CapitalAccount.objects.filter(
                broker_id=account_surplus_account_id, date__lte=date_cursor).latest().initial_capital
            fund_balance = round((initial_capital + total_capital), 2)  # 资金余额
            # 总资产
            total_assets = round(fund_balance + market_capital, 2)
            update_flag = True
            account_surplus_id_cursor = account_surplus_id_cursor + 1  # 该表单 id自动加1

            AccountSurplus.objects.create(id=account_surplus_id_cursor, total_assets=total_assets, total_fee=total_fee,
                                          account_id=account_surplus_account_id, market_capital=market_capital,
                                          fund_balance=fund_balance, position_gain_loss=position_gain_loss,
                                          final_cost=total_capital, initial_capital=initial_capital, date=date_cursor,
                                          update_flag=update_flag)

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

    """全市场综合排名"""
    # smr计算
    # 1、提取财务数据。原则：完整三年年报+最新两期季报，包括期间所有的季报数据。
    prepare_data = pd.DataFrame()
    high_data = pd.DataFrame()
    for query_date in ['20161231',
                       '20170331', '20170630', '20170930', '20171231',
                       '20180331', '20180630', '20180930', '20181231',
                       '20190331', '20190630', '20190930', '20191231',
                       '20200331']:
        query_data = pro.query('fina_indicator_vip', start_date=query_date, end_date=query_date)
        prepare_data = prepare_data.append(query_data, ignore_index=True)
    # 2、财务数据清洗，删除roe为空值的行。
    df = prepare_data[prepare_data['roe'].notna()]
    df.sort_values(by=['ts_code', 'end_date'], ascending=[True, False], inplace=True)
    df.fillna(value=0, inplace=True)
    df.reset_index(drop=True, inplace=True)

    # 3、数据切片，完成个股eps标准差计算，评估每股收益稳定性。
    df = df.groupby('ts_code').filter(lambda g: g.ts_code.count() > 12)
    df.to_csv('/Users/flowerhost/securityproject/data/orginal.csv')
    eps_stability = df.groupby('ts_code')['basic_eps_yoy'].std().rank(ascending=True)  # 按照季报收益稳定性进行排名。值越小越稳定。

    # 4、取每组第一个值求和smr,并排名。
    smr = df.groupby('ts_code', as_index=False)[
        'roe', 'dt_netprofit_yoy', 'q_sales_yoy', 'grossprofit_margin', 'end_date', 'ann_date'].first()
    smr['smr'] = smr.iloc[:, 1:5].sum(axis=1).rank(ascending=True)

    # 5、数据联结组合。
    data_join = pd.merge(eps_stability, smr, on='ts_code')

    # 6、smr和eps稳定性排名转化为百分制。
    x = data_join['ts_code'].count()
    data_join['smr'] = round(100 * data_join['smr'] / x, 1)
    data_join['eps_stability'] = round(100 * data_join['basic_eps_yoy'] / x, 1)

    # 7、eps排名，计算公式：最新两季度季报权重1.5，三年年报权重1.0，求5者之和eps。
    data_quarter_new = df.groupby('ts_code')['ts_code', 'basic_eps_yoy'].head(1)
    data_quarter_new['new_quarter_eps'] = round(data_quarter_new['basic_eps_yoy'], 2)
    data_quarter_new.to_csv('/Users/flowerhost/securityproject/data/debugeps.csv')
    data_quarter = df.groupby('ts_code')['ts_code', 'basic_eps_yoy'].head(2)
    data_quarter.to_csv('/Users/flowerhost/securityproject/data/debug.csv')
    data_quarter = data_quarter.groupby('ts_code').sum() * 1.5  # 最近两个季度的eps权重1.5
    df['end_date'] = df['end_date'].astype('str')  # 转化为str型，为下条语句使用。
    data_year = df[df['end_date'].str.contains('1231')].groupby('ts_code').head(3)
    data_year = data_year[['end_date', 'ts_code', 'basic_eps_yoy']].groupby('ts_code').sum()
    data_year = pd.merge(data_quarter, data_year, on='ts_code')
    data_year['eps'] = data_year.iloc[:, 1:3].sum(axis=1).rank(ascending=True)

    # 8、数据联合
    eps_smr_stability = pd.merge(data_join, data_year, on='ts_code')
    eps_smr_stability = pd.merge(eps_smr_stability, data_quarter_new, on='ts_code')
    eps_smr_stability['eps'] = round(100 * eps_smr_stability['eps'] / x, 1)
    eps_smr_stability = eps_smr_stability[['ts_code', 'new_quarter_eps', 'eps', 'smr', 'eps_stability', 'end_date',
                                           'ann_date']]

    # rps强度计算
    # 9、获取交易日期,取最新的交易日，推算出前250日的日期。
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(weeks=60)
    trade_date = pro.query('trade_cal', start_date=start_date.strftime("%Y%m%d"),
                           end_date=end_date.strftime("%Y%m%d"), is_open=1, fields=['cal_date'])

    # 判断时间，当前提取时间17：00以后，取当日数据，否则取前一日数据。
    check_time = datetime.datetime.strptime(str(datetime.date.today()) + '17:00', '%Y-%m-%d%H:%M')
    now_time = datetime.datetime.now()
    if now_time > check_time:
        daily_end_date = trade_date.tail(1)['cal_date'].values[0]
    else:
        daily_end_date = trade_date.tail(2)['cal_date'].values[0]

    daily_start_date = trade_date.tail(250)['cal_date'].values[0]
    industry_start_date = trade_date.tail(20)['cal_date'].values[0]

    # 10、获得最新日的交易数据收盘价和成交量比.
    df_volume_ratio = pro.daily_basic(
        ts_code='', trade_date=daily_end_date, fields=['ts_code', 'volume_ratio'])
    df_history = pro.daily(trade_date=daily_start_date, fields=['ts_code', 'close'])
    df_current = pro.daily(trade_date=daily_end_date, fields=['ts_code', 'close'])
    data_rps = pd.merge(df_history, df_current, on='ts_code')

    # 获取行业板块L3指数行情,计算行业RPS排名。
    l3_current = pro.sw_daily(trade_date=daily_end_date)
    l3_history = pro.sw_daily(trade_date=industry_start_date)
    l3_rps = pd.merge(l3_history, l3_current, on='ts_code')
    l3_rps = l3_rps.tail(227)
    l3_rps['index_code'] = l3_rps['ts_code']
    member_count = l3_rps['index_code'].count()
    l3_rps['industry_rps'] = l3_rps.apply(lambda x: round((x['close_y']-x['close_x'])/x['close_x'], 2), axis=1).rank(
        ascending=True)
    l3_rps['industry_rps'] = round(100 * l3_rps['industry_rps']/member_count, 1)
    l3_rps['industry_name'] = l3_rps['name_x']
    l3_rps = l3_rps[['index_code', 'industry_rps', 'industry_name']]

    # 个股与行业指数L3相关联
    industry_member = pd.DataFrame()
    l3 = pro.index_classify(level='L3', src='SW')
    for l_code in l3['index_code']:
        index_member = pro.index_member(index_code=l_code)
        industry_member = industry_member.append(index_member, ignore_index=True)
    industry_member['ts_code'] = industry_member['con_code']
    industry_member = pd.merge(industry_member, l3_rps, on='index_code')
    industry_member = industry_member[['ts_code', 'index_code', 'industry_name', 'industry_rps']]

    # 11、获取52周最高价
    for query_date in daily_start_date:
        query_data = pro.monthly(trade_date=query_date, fields=['trade_date', 'ts_code', 'high'])
        high_data = high_data.append(query_data, ignore_index=True)

    first_date = '%d%2d01' % (end_date.year, end_date.month)
    daily_date = pro.query('trade_cal', start_date=first_date,
                           end_date=end_date.strftime("%Y%m%d"), is_open=1, fields=['cal_date'])

    for query_date in daily_date['cal_date']:
        query_data = pro.daily(trade_date=query_date, fields=['trade_date', 'ts_code', 'high'])
        high_data = high_data.append(query_data, ignore_index=True)
    high_data = high_data.groupby('ts_code')['high'].max()

    # 12、数据联合
    data_rps = pd.merge(data_rps, high_data, on='ts_code')
    data_rps = pd.merge(data_rps, df_volume_ratio, on='ts_code')
    data_rps.sort_values(by='ts_code', ascending=True, inplace=True)
    data_rps.reset_index(drop=True, inplace=True)

    # 13、计算RPS排名，计算52周最高价与当前价的下降幅度。
    data_rps['rps'] = data_rps.apply(lambda x: round((x['close_y'] - x['close_x']) / x['close_x'], 2), axis=1).rank(
        ascending=True)
    x = data_rps['ts_code'].count()
    data_rps['rps'] = round(100 * data_rps['rps'] / x, 1)
    data_rps['decline_range'] = data_rps.apply(lambda x: round(100 * (x['close_y'] - x['high']) / x['high'], 1),
                                               axis=1)

    # 14、数据联合,计算综合排名。
    data_cumulative_rank = pd.merge(eps_smr_stability, data_rps, on='ts_code')
    data_cumulative_rank = pd.merge(data_cumulative_rank, high_data, on='ts_code')
    data_cumulative_rank = pd.merge(data_cumulative_rank, industry_member, on='ts_code')
    data_cumulative_rank['cumulative_rank'] = data_cumulative_rank.apply(
        lambda x: round(x['eps'] * 2 + x['rps'] * 2 + x['smr'] + x['industry_rps'] + x['decline_range'], 2),
        axis=1).rank(ascending=True)
    x = data_cumulative_rank['ts_code'].count()
    data_cumulative_rank['cumulative_rank'] = round(100 * data_cumulative_rank['cumulative_rank'] / x, 1)
    data_cumulative_rank.reset_index(drop=True, inplace=True)
    data_cumulative_rank['period_date'] = pd.to_datetime(data_cumulative_rank['end_date'], dayfirst=True)
    data_cumulative_rank['period_date'] = data_cumulative_rank['period_date'].dt.strftime('%Y-%m-%d')
    data_cumulative_rank['ann_date'] = pd.to_datetime(data_cumulative_rank['ann_date'], dayfirst=True)
    data_cumulative_rank['ann_date'] = data_cumulative_rank['ann_date'].dt.strftime('%Y-%m-%d')
    data_cumulative_rank['code'] = data_cumulative_rank['ts_code']
    data_cumulative_rank = data_cumulative_rank[
        ['code', 'cumulative_rank', 'new_quarter_eps', 'eps', 'rps', 'smr', 'eps_stability', 'decline_range',
         'volume_ratio', 'industry_name', 'industry_rps', 'period_date', 'ann_date']]

    # 15、写数据库
    con = sqlite3.connect('/Users/flowerhost/securityproject/db.sqlite3')
    data_cumulative_rank.to_sql("capital_management_cumulativerank", con, if_exists="replace", index=False)
    data_cumulative_rank.to_csv('/Users/flowerhost/securityproject/data/RPS_SMR.csv')

    return redirect('capital_management:index')


def capital_manage(request):
    """资金和仓位管理 以月为计算周期
        监控和约束仓位功能
        1、计算月初资金总额 AccountSurplus的总资产
        2、6%为账户承受的最大损失；2%为每笔交易承受的最大损失
        3、计算交易标的物的止损价 30天周期，安全区域止损法则--《走进我的交易室》
        4、计算最大购买数：2%总资产/（买入价-止损价）
        5、每天计算自动计算一次，公布敞口至月末。
    """
    if CapitalManagement.objects.exists():
        management_id_cursor = CapitalManagement.objects.last().id
        start_date = CapitalManagement.objects.last().date
    else:
        management_id_cursor = 0
        start_date = Positions.objects.earliest().date

    gain_loss_date = start_date - datetime.timedelta(days=30)
    calculate_date = datetime.date.today()

    # 局部变量
    calendar = []
    day_count = 11
    sum_values = 0
    count_number = 0
    gain_loss = {}
    for _ in range(3):

        try:
            calendar = pro.query('trade_cal', start_date=start_date.strftime("%Y%m%d"),
                                 end_date=calculate_date.strftime("%Y%m%d"), is_open=1, fields=['cal_date'])
        except:
            time.sleep(1)
    for cal_date in calendar.values:
        date_cursor = datetime.datetime.strptime(cal_date[0], "%Y%m%d")

        positions_data = Positions.objects.filter(  # annotate 对于相同的名字的股票 叠加计算，出现错误。
            date=date_cursor).values('code', 'name').annotate(final_cost=Sum('final_cost'), amount=Sum('amount'))

        for position in positions_data:
            stock_name = position['name']
            stock_code = position['code']
            stock_amount = position['amount']
            buy = round(position['final_cost'] / position['amount'] * -1, 2)
            # 计算止损点, 先拿到计算日前30天的交易日历，便于计算前10日最低价。
            gain_loss_date = date_cursor - datetime.timedelta(days=30)
            cal = pro.query('trade_cal', start_date=gain_loss_date.strftime("%Y%m%d"),
                            end_date=cal_date[0], is_open=1, fields=['cal_date'])
            stop_loss_data = ts.pro_bar(ts_code=stock_code, adj='qfq', start_date=cal['cal_date'].values[-11],
                                        end_date=cal['cal_date'].values[-1], ma=[10])
            print(stop_loss_data.head())
            stop_loss_data = stop_loss_data.sort_values(by=['trade_date'], ascending=[True])
            stop_loss_data = stop_loss_data[['trade_date', 'low', 'close', 'ma10']].values.tolist()
            # 比较前一交易日的最低价
            for i in range(day_count):
                if i == 0:
                    pass
                else:
                    latest_low = stop_loss_data[i][1]
                    for j in range(2):
                        early_low = stop_loss_data[i - j][1]
                        if early_low > latest_low:
                            count_number = count_number + 1
                            sum_values = sum_values + early_low - latest_low
                        else:
                            # 极特殊情况，健帆生物20200414。个股强力拉升不回调，除0错误。
                            ma10 = stop_loss_data[i][3]

            if count_number == 0:
                result = ma10
            else:
                result = round((stop_loss_data[-2][1] - 3 * sum_values / count_number), 2)

            if CapitalManagement.objects.exists():
                last_loss_date = cal['cal_date'].values[-2]
                last_loss_date = datetime.datetime.strptime(last_loss_date, "%Y%m%d")
                last_stop_loss = CapitalManagement.objects.filter(
                    date=last_loss_date, stock_name=stock_name).values('stop_loss')
                if last_stop_loss.exists():
                    last_loss = last_stop_loss[0]['stop_loss']
                else:
                    last_loss = 0
            else:
                last_loss = 0
            # 比较前一交易日的止损点，取大值，避免止损点下滑, 如果跌破买入价的8%则无条件止损，表明买点不好。
            stop_loss = round(max(result, last_loss, buy * 0.92), 2)

            stock_close = stop_loss_data[-1][2]
            if buy > 0:
                gain_loss_rate = round(100*(stock_close - buy) / buy, 2)
            else:
                gain_loss_rate = round(-100*(stock_close - buy)/buy, 2)
            # 获取月初资产*6%
            assets = AccountSurplus.objects.get(date=date_cursor).total_assets
            current_month = datetime.datetime.strptime(cal_date[0], "%Y%m%d").month
            current_id = AccountSurplus.objects.get(date=date_cursor).id
            if current_id == 1:
                check_month = current_month
            else:
                check_month = AccountSurplus.objects.get(id=current_id - 1).date.month

            # 判断资金的风险敞口
            # 最多3个交易标的。每个交易标的不得超过capital_2，总风险敞口不超过capital_6
            risk_2 = round(assets * 0.02, -2)
            risk_6 = round(assets * 0.06, -2)

            if buy > stop_loss:
                max_volume = round(risk_2 / (buy - stop_loss) - stock_amount, -2)
            else:
                max_volume = stock_amount

            if CapitalManagement.objects.exists():
                # 计算月初第一个交易日风险敞口，每月第一天完成资金账户进出转账更新。
                if check_month < current_month:
                    current_month_risk = round(assets * 0.06, 2)
                else:
                    current_month_risk = CapitalManagement.objects.last().month_risk_6
                # 避免数据重复
                flag = CapitalManagement.objects.filter(date=date_cursor, stock_name=stock_name)
                if flag:
                    pass
                else:
                    management_id_cursor = management_id_cursor + 1
                    CapitalManagement.objects.create(id=management_id_cursor, risk_6=risk_6, stock_name=stock_name,
                                                     stop_loss=stop_loss, positions=stock_amount,
                                                     stock_close=stock_close,
                                                     max_volume=max_volume, buy=buy, gain_loss=gain_loss_rate,
                                                     date=date_cursor, month_risk_6=current_month_risk)
            else:
                management_id_cursor = management_id_cursor + 1
                current_month_risk = risk_6
                CapitalManagement.objects.create(id=management_id_cursor, risk_6=risk_6, stock_name=stock_name,
                                                 stop_loss=stop_loss, positions=stock_amount, stock_close=stock_close,
                                                 max_volume=max_volume, buy=buy, gain_loss=gain_loss_rate,
                                                 date=date_cursor, month_risk_6=current_month_risk)
            # 网页端展示数据准备
            query_date = CapitalManagement.objects.latest().date
            capital_management = CapitalManagement.objects.filter(date=query_date).values(
                'month_risk_6', 'risk_6', 'stock_name', 'stop_loss', 'stock_close', 'buy', 'gain_loss', 'positions',
                'max_volume', 'date')
            # 剩余敞口资金数
            current_risk_measurement = round(risk_6 - current_month_risk, -2)
            if current_risk_measurement > 0:
                message = {'risk_message': "趋势向好！敞口增加"}
                risk_exposure = current_risk_measurement
            elif current_risk_measurement < -current_month_risk * 0.06:
                message = {'risk_message': "交易结束！本月损失"}
                risk_exposure = round(current_risk_measurement / 0.06, -2)
            else:
                message = {'risk_message': "趋势向坏，敞口减少"}
                risk_exposure = current_risk_measurement

    return render(request, 'capital_management/management.html', locals())


def investor(request):
    """股票基本面评价
        1、获取rps：股票强度指标大于87%以上。通过通达信软件获取。
        2、获取行业rps：行业强度位于前6位。参考值：>= 90
        3、通过tushare接口fina_indicator获得数据，写入EvaluateStocks表中。股票代码为通达信导入。
        4、计算eps: 最近三个年度增长率25%以上，下一年度25%以上的预测值；最近三个季度的增长率有大幅上涨，25%-30%以上为佳。
        5、计算sales：or_yoy 最近三个季度营业收入增速趋势，或者上一季度的增长率25%以上。TODO：错误
        6、计算ROE：每股净资产收益率大于17%以上，一般在25%---50%之间为优秀。
        7、计算q_op_qoq： 最近一个季度的营业利润是增长的（环比增长率为正），而且是接近此股最高点时营业利润增长率。TODO：错误
        8、计算吸筹/出货：未考虑好，待进一步研究学习。
        9、监控量比变化：当日成交量显著地放大50%以上。
        10、计算沪深港通交易占比。tushare接口：k_hold。
        11、计算股票综合排名。便于及时浏览关注。
            以上指标分配不同的权重，然后进行排名。对排名靠前的股票进行四项指标独立研究：eps、ROE、smr和吸筹/出货，同时发现量比变化。
        12、大盘处于上升趋势。
    """
    if EvaluateStocks.objects.exists():
        id_cursor = EvaluateStocks.objects.last().id
    else:
        id_cursor = 0
    query_date = datetime.date.today()
    start_query_date = query_date - datetime.timedelta(weeks=200)
    if request.method == "POST":
        stock_code = request.POST.get("stock_code")

        query_result = pro.query('fina_indicator', ts_code=stock_code, strart_date=start_query_date.strftime("%Y%m%d"),
                                 end_date=query_date.strftime("%Y%m%d"))
        express_query_result = pro.express(ts_code=stock_code, start_date=start_query_date.strftime("%Y%m%d"),
                                           end_date=query_date.strftime("%Y%m%d"),
                                           fields='ts_code, end_date, diluted_roe')

        query_result = query_result[['end_date', 'basic_eps_yoy', 'or_yoy', 'roe', 'q_op_qoq']]
        express_query_result = express_query_result[['end_date', 'diluted_roe']]

        end_date = query_result['end_date'][0]
        period_cursor = datetime.datetime.strptime(end_date, '%Y%m%d').date()

        if period_cursor.month == 12:
            front_y1_eps_rate = round(query_result['basic_eps_yoy'][4], 2)
            front_y2_eps_rate = round(query_result['basic_eps_yoy'][8], 2)
            front_y3_eps_rate = round(query_result['basic_eps_yoy'][12], 2)
            roe = round(query_result['roe'][0])
        elif period_cursor.month == 9:
            front_y1_eps_rate = round(query_result['basic_eps_yoy'][7], 2)
            front_y2_eps_rate = round(query_result['basic_eps_yoy'][11], 2)
            front_y3_eps_rate = round(query_result['basic_eps_yoy'][15], 2)
            roe = round(query_result['roe'][3])
        elif period_cursor.month == 6:
            front_y1_eps_rate = round(query_result['basic_eps_yoy'][6], 2)
            front_y2_eps_rate = round(query_result['basic_eps_yoy'][10], 2)
            front_y3_eps_rate = round(query_result['basic_eps_yoy'][14], 2)
            roe = round(query_result['roe'][2])
        else:
            front_y1_eps_rate = round(query_result['basic_eps_yoy'][5], 2)
            front_y2_eps_rate = round(query_result['basic_eps_yoy'][9], 2)
            front_y3_eps_rate = round(query_result['basic_eps_yoy'][13], 2)
            roe = round(query_result['roe'][1])
        forecast_eps_rate = 0

        eps_rate = round(query_result['basic_eps_yoy'][0], 2)
        front_q1_eps_rate = round(query_result['basic_eps_yoy'][1], 2)
        front_q2_eps_rate = round(query_result['basic_eps_yoy'][2], 2)
        front_q3_eps_rate = round(query_result['basic_eps_yoy'][3], 2)

        front_q1_sales_rate = round(query_result['or_yoy'][0], 2)
        front_q2_sales_rate = round(query_result['or_yoy'][1], 2)
        front_q3_sales_rate = round(query_result['or_yoy'][2], 2)

        q_op_qoq = round(query_result['q_op_qoq'][0], 2)
        # 业绩快报
        if not express_query_result.empty:
            express_diluted_roe = round(express_query_result['diluted_roe'][0], 2)
            express_date = express_query_result['end_date'][0]
            express_date = datetime.datetime.strptime(express_date, '%Y%m%d').date()
        else:
            express_diluted_roe = 0
            express_date = query_date

        period_date = period_cursor
        date = query_date

        if EvaluateStocks.objects.filter(period_date=period_date, code=stock_code):
            pass
        else:
            id_cursor = id_cursor + 1
            EvaluateStocks.objects.create(id=id_cursor, code=stock_code, front_q1_eps_rate=front_q1_eps_rate,
                                          front_q2_eps_rate=front_q2_eps_rate, front_q3_eps_rate=front_q3_eps_rate,
                                          front_y1_eps_rate=front_y1_eps_rate, front_y2_eps_rate=front_y2_eps_rate,
                                          front_y3_eps_rate=front_y3_eps_rate, forecast_eps_rate=forecast_eps_rate,
                                          front_q1_sales_rate=front_q1_sales_rate, q_op_qoq=q_op_qoq, date=query_date,
                                          front_q2_sales_rate=front_q2_sales_rate, period_date=period_cursor,
                                          front_q3_sales_rate=front_q3_sales_rate, eps_rate=eps_rate, roe=roe,
                                          express_diluted_roe=express_diluted_roe, express_date=express_date)

    evaluate_query_result = EvaluateStocks.objects.all().order_by('-date')

    return render(request, 'capital_management/evaluate.html', locals())


def evaluate(request):
    """日监控指标体系 2020-04-04
        目标：动态可量化地评估监控股票的表现。接口名称fina_indicator。
        方法：建立评估指标体系：eps、rps、smr、量比变化追踪、主力吸筹/派发（待研究）、ROE、行业强度（待研究）、52周最高价股价下降幅度
        1、rps计算思路：
        （当日收盘价-前250日收盘价）/前250日收盘价，即250日股价涨跌幅度，然后全市场来按照涨跌幅度来计算排名（1-99）。
        2、smr计算思路：
        4部分：Sales growth rate over the last three quarters（季度销售同比增长率）; After-tax profit margins(季度税后净利率);
        Pre-tax profit margins（年报税前毛利率）; Return on equity(ROE).
        其中：Sales growth rate和 after-tax margins使用季报数据，ROE和pre-tax margins使用年报数据。
        计算结果按照数值大小进行档次排名：A B C D E五档。每档占比20%。数值不全的，计算结果输出N/A。
        对应tushare接口：分别是q_sales_yoy(季度销售同比增长率)、dt_netprofit_yoy（季度扣非税后净利率）、grossprofit_margin（毛利率）
        和roe。
        3、eps计算思路：
        @1评估过去3年间年度收益增长的稳定性和一致性：将过去3-5年中的季度收益点标出，然后用一条上涨趋势线连接，用以明确该股票偏离基本上涨趋势的程度。
        即基本每股收益增长率非常稳定，相互之间的差值非常小。basic_eps_yoy之间差值变化很小，求其标准差。pandas.std()
        @2至少连续8个季度的收益为正，否则输出结果为N/A。
        @3计算最近2个季度收益同比增长率+3年收益增长率，季报同比增长率赋予更多的权重，需要考虑其标准差因素。
        @4对每个股票的数值按照大小进行排名（1-99）。
        4、量比变化追踪计算思路：Volume Percent Change. 求MA10日股票交易数值，计算（当日股票交易数值-MA10值）/MA10值。
        5、52周最高价股价下降幅度。计算（52周股价最高价-当日收盘价）/52周最高价
        6、综合排名计算思路：
        eps和rps对股价的表现影响最大，所以赋予2倍权重，smr、行业组相对强度和吸筹/出货百分比赋予单倍权重。按照数值大小进行排名（1-99）。
        综合值 = eps*2 + rps*2 + smr + 量比变化 - 52周股价下降幅度。缺少行业强度、主力吸筹/派发2个值。
    """
    # 页面展示
    cumulative_ranks = CumulativeRank.objects.values(
        'code', 'eps', 'eps_stability', 'smr', 'period_date', 'rps', 'cumulative_rank', 'decline_range', 'volume_ratio',
        'ann_date', 'new_quarter_eps', 'industry_name', 'industry_rps').order_by('-cumulative_rank')

    return render(request, 'capital_management/evaluate.html', locals())
