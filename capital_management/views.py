# Create your views here.

from django.shortcuts import render, redirect
from .models import TradeLists, TradeDailyReport, CapitalAccount, AccountSurplus, Clearance, TradePerformance, Broker
from .models import Positions, CapitalManagement, CumulativeRank, MonitorIndustry
from .form import BrokerForm, TradeListsForm, CapitalAccountForm

from django.db.models import Sum, Q

import sqlite3
import time
import datetime
import pandas as pd
import numpy as np

import talib

import json
from django.http import HttpResponse
from rest_framework.views import APIView
from django.template import loader, RequestContext
from random import randrange

from typing import List, Sequence, Union

from pyecharts.charts import Kline, Line, Bar, Grid
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode


"""tushare类数据接口"""
import tushare as ts

ts.set_token('033ad3c72aef8ce38d29d34482058b87265b32d788fb6f24d2e0e8d6')
pro = ts.pro_api()


def index(request):
    stocks = TradeLists.objects.values(
        'code', 'name', 'price', 'flag', 'date', 'trade_resource', 'quantity', 'total_capital',
        'account__name', 'tradeperformance__close', 'tradeperformance__moving_average',
        'tradeperformance__performance', 'tradeperformance__trade_performance').order_by('-date')

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
    start_query_date = query_date - datetime.timedelta(weeks=20)

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
            new_trade.clear_flag = 1

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
    # 如果是16:15之前，提取前一交易日数据
    check_time = datetime.datetime.strptime(str(datetime.date.today()) + '16:15', '%Y-%m-%d%H:%M')
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
                elif performance_flag == 'Bingo':
                    p_flag = False
                else:
                    p_flag = False

                for _ in range(3):
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
                        print(query_result['ma10'][0])
                        if np.isnan(query_result['ma10'][0]):
                            moving_average = close
                        else:
                            moving_average = round(query_result['ma10'].values[0], 2)

                        boll_up = round(moving_average * 1.09, 2)
                        boll_down = round(moving_average * 0.91, 2)

                        performance = round((performance_price - low_price) / (high_price - low_price), 2)
                        # 换算买入表现分值，使得其意义与卖入表现分值所代表的意义一致，分值越高，其表现越好。
                        if p_flag:
                            performance = round((1 - performance), 2)
                            trade_performance = 0
                        else:
                            trade_price = TradeLists.objects.filter(
                                code=performance_code, flag='B', date__lt=performance_score_date).values(
                                'price', 'tradeperformance__boo_down').latest()
                            trade_performance = round((performance_price - trade_price['price']) /
                                                      (boll_up - trade_price['tradeperformance__boo_down']), 2)

                if not TradePerformance.objects.exists():
                    TradePerformance.objects.create(id=performance_id_cursor, close=close,
                                                    moving_average=moving_average,
                                                    high_price=high_price, low_price=low_price, boll_up=boll_up,
                                                    boo_down=boll_down, performance=performance,
                                                    trade_id=performance_trade_id,
                                                    trade_performance=trade_performance,
                                                    date=performance_score_date)
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
    # smr计算
    # 1、提取财务数据。原则：完整三年年报+最新两期季报，包括期间所有的季报数据。
    prepare_data = pd.DataFrame()
    high_data = pd.DataFrame()
    for query_date in ['20161231',
                       '20170331', '20170630', '20170930', '20171231',
                       '20180331', '20180630', '20180930', '20181231',
                       '20190331', '20190630', '20190930', '20191231',
                       '20200331', '20200630']:
        query_data = pro.query('fina_indicator_vip', start_date=query_date, end_date=query_date)
        prepare_data = prepare_data.append(query_data, ignore_index=True)
    # 2、财务数据清洗，删除roe为空值的行。
    df = prepare_data[prepare_data['roe'].notna()]
    df.sort_values(by=['ts_code', 'end_date'], ascending=[True, False], inplace=True)
    df.fillna(value=0, inplace=True)
    df.reset_index(drop=True, inplace=True)

    # 3、数据切片，完成个股eps标准差计算，评估每股收益稳定性。
    df = df.groupby('ts_code').filter(lambda g: g.ts_code.count() > 12)
    eps_stability = df.groupby('ts_code')['basic_eps_yoy'].std().rank(ascending=True)  # 按照季报收益稳定性进行排名。值越小越稳定。
    # 4、取每组第一个值求和smr,并排名。
    smr = df.groupby('ts_code', as_index=False)[
        'roe', 'dt_netprofit_yoy', 'q_sales_yoy', 'grossprofit_margin', 'end_date', 'ann_date'].first()
    smr['smr'] = smr.iloc[:, 1:5].sum(axis=1).rank(ascending=True)
    # 取年报roe数据.
    this_year_start = datetime.datetime(datetime.datetime.now().year, 1, 1)
    last_year_end = this_year_start - datetime.timedelta(days=1)
    report_date = datetime.datetime.strftime(last_year_end, '%Y%m%d')
    print("年报日期：", report_date)
    roe = df[['ts_code', 'end_date', 'roe']]
    roe['flag'] = roe.apply(lambda x: 1 if x['end_date'] == report_date else None, axis=1)
    roe = roe[roe['flag'].notna()]
    roe = roe[['ts_code', 'roe']]

    # 5、数据联结组合。
    data_join = pd.merge(eps_stability, smr, on='ts_code')
    # 6、smr和eps稳定性排名转化为百分制。
    x = data_join['ts_code'].count()
    data_join['smr'] = round(100 * data_join['smr'] / x, 1)
    data_join['eps_stability'] = round(100 * data_join['basic_eps_yoy'] / x, 1)
    data_join = pd.merge(data_join, roe, on='ts_code')

    # 7、eps排名，计算公式：最新两季度季报权重1.5，三年年报权重1.0，求5者之和eps。
    data_quarter_new = df.groupby('ts_code')['ts_code', 'basic_eps_yoy'].head(1)
    data_quarter_new['new_quarter_eps'] = round(data_quarter_new['basic_eps_yoy'], 2)
    data_quarter = df.groupby('ts_code')['ts_code', 'basic_eps_yoy'].head(2)
    data_quarter = data_quarter.groupby('ts_code').sum() * 1.5  # 最近两个季度的eps权重1.5
    df['end_date'] = df['end_date'].astype('str')  # 转化为str型，为下条语句使用。
    data_year = df[df['end_date'].str.contains('1231')].groupby('ts_code').head(3)
    data_year = data_year[['end_date', 'ts_code', 'basic_eps_yoy']].groupby('ts_code').sum()
    data_year = pd.merge(data_quarter, data_year, on='ts_code')
    data_year['eps'] = data_year.iloc[:, 1:3].sum(axis=1).rank(ascending=True)
    # 最新的业绩预告数据
    forecast = pro.forecast_vip(period='20200630', fields='ts_code, type, p_change_min, p_change_max')

    data_year = pd.merge(data_year, forecast, how='left', on='ts_code')
    data_year.rename(columns={'type': 'forecast'}, inplace=True)

    # 8、数据联合
    eps_smr_stability = pd.merge(data_join, data_year, on='ts_code')
    eps_smr_stability = pd.merge(eps_smr_stability, data_quarter_new, on='ts_code')
    eps_smr_stability['eps'] = round(100 * eps_smr_stability['eps'] / x, 1)
    eps_smr_stability = eps_smr_stability[['ts_code', 'new_quarter_eps', 'eps', 'smr', 'eps_stability', 'roe_y',
                                           'end_date', 'ann_date', 'forecast', 'p_change_min', 'p_change_max']]
    eps_smr_stability.rename(columns={'roe_y': 'roe'}, inplace=True)

    # rps强度计算
    # 9、获取交易日期,取最新的交易日，推算出前250日的日期。
    end_date = datetime.date.today()
    year = str(end_date.year)  # 本年
    last_year = str(end_date.year - 1)
    week_first_day = end_date - datetime.timedelta(days=end_date.weekday())  # 本周第一天
    start_date = end_date - datetime.timedelta(weeks=60)
    trade_date = pro.query('trade_cal', start_date=start_date.strftime("%Y%m%d"),
                           end_date=end_date.strftime("%Y%m%d"), is_open=1, fields=['cal_date'])

    # 判断时间，当前提取时间18：00以后，取当日数据，否则取前一日数据。
    check_time = datetime.datetime.strptime(str(datetime.date.today()) + '18:00', '%Y-%m-%d%H:%M')
    now_time = datetime.datetime.now()
    if now_time > check_time:
        daily_end_date = trade_date.tail(1)['cal_date'].values[0]
        daily_start_date = trade_date.tail(250)['cal_date'].values[0]
        industry_20_days = trade_date.tail(20)['cal_date'].values[0]
        industry_1_weeks = trade_date.tail(5)['cal_date'].values[0]
        industry_3_weeks = trade_date.tail(15)['cal_date'].values[0]
        industry_6_weeks = trade_date.tail(30)['cal_date'].values[0]
        industry_7_months = trade_date.tail(140)['cal_date'].values[0]

        # 获取本年度第一个交易日
        trade_date['cal_date'] = trade_date['cal_date'].astype('str')  # 转化为str型，为下条语句使用。
        new_year_date = trade_date[trade_date['cal_date'].str.contains(year)].head(1).values[0][0]
        # 获取上一年度最后一个交易日
        last_year_date = trade_date[trade_date['cal_date'].str.contains(last_year)].tail(1).values[0][0]
        # 获取本周第一个交易日
        week_date = pro.query('trade_cal', start_date=week_first_day.strftime("%Y%m%d"),
                              end_date=end_date.strftime("%Y%m%d"), is_open=1, fields=['cal_date'])
        week_first_date = week_date.head(1)['cal_date'].values[0]
        # 获取前一交易日
        front_date = trade_date.tail(2)['cal_date'].values[0]
    else:
        daily_end_date = trade_date.tail(2)['cal_date'].values[0]
        daily_start_date = trade_date.tail(251)['cal_date'].values[0]
        industry_20_days = trade_date.tail(21)['cal_date'].values[0]
        industry_1_weeks = trade_date.tail(6)['cal_date'].values[0]
        industry_3_weeks = trade_date.tail(16)['cal_date'].values[0]
        industry_6_weeks = trade_date.tail(31)['cal_date'].values[0]
        industry_7_months = trade_date.tail(141)['cal_date'].values[0]

        # 获取本年度第一个交易日
        trade_date['cal_date'] = trade_date['cal_date'].astype('str')  # 转化为str型，为下条语句使用。
        new_year_date = trade_date[trade_date['cal_date'].str.contains(year)].head(1).values[0][0]
        # 获取上一年度最后一个交易日
        last_year_date = trade_date[trade_date['cal_date'].str.contains(last_year)].tail(1).values[0][0]
        # 获取本周第一个交易日
        week_date = pro.query('trade_cal', start_date=week_first_day.strftime("%Y%m%d"),
                              end_date=end_date.strftime("%Y%m%d"), is_open=1, fields=['cal_date'])
        week_first_date = week_date.head(1)['cal_date'].values[0]
        # 获取前一交易日
        front_date = trade_date.tail(3)['cal_date'].values[0]

    # 周六、日执行数据提取时的时间设置。
    weekend = datetime.datetime.today().weekday()
    if weekend in [5, 6]:
        daily_end_date = trade_date.tail(1)['cal_date'].values[0]
        daily_start_date = trade_date.tail(250)['cal_date'].values[0]
        industry_20_days = trade_date.tail(20)['cal_date'].values[0]
        industry_1_weeks = trade_date.tail(5)['cal_date'].values[0]
        industry_3_weeks = trade_date.tail(15)['cal_date'].values[0]
        industry_6_weeks = trade_date.tail(30)['cal_date'].values[0]
        industry_7_months = trade_date.tail(140)['cal_date'].values[0]

        # 获取本年度第一个交易日
        trade_date['cal_date'] = trade_date['cal_date'].astype('str')  # 转化为str型，为下条语句使用。
        new_year_date = trade_date[trade_date['cal_date'].str.contains(year)].head(1).values[0][0]
        # 获取上一年度最后一个交易日
        last_year_date = trade_date[trade_date['cal_date'].str.contains(last_year)].tail(1).values[0][0]
        # 获取本周第一个交易日
        week_date = pro.query('trade_cal', start_date=week_first_day.strftime("%Y%m%d"),
                              end_date=end_date.strftime("%Y%m%d"), is_open=1, fields=['cal_date'])
        week_first_date = week_date.head(1)['cal_date'].values[0]
        # 获取前一交易日
        front_date = trade_date.tail(2)['cal_date'].values[0]

    # 10、获得最新的股票交易数据收盘价和成交量比.
    df_volume_ratio = pro.daily_basic(
        ts_code='', trade_date=daily_end_date, fields=['ts_code', 'volume_ratio'])
    df_history = pro.daily(trade_date=daily_start_date, fields=['ts_code', 'close'])
    df_current = pro.daily(trade_date=daily_end_date, fields=['ts_code', 'close', 'high', 'change', 'pct_chg'])
    data_rps = pd.merge(df_history, df_current, on='ts_code')

    # 获得最新的港股通持股比例 如果当日23：00提取数据，只能提取前一天沪港通数据
    check_hk_time = datetime.datetime.strptime(str(datetime.date.today()) + '22:00', '%Y-%m-%d%H:%M')
    if now_time > check_hk_time:
        hk_date = front_date
    else:
        hk_date = daily_end_date

    if weekend in [5, 6]:
        hk_date = daily_end_date

    hk_hold = pro.hk_hold(trade_date=hk_date, fields=['ts_code', 'ratio'])

    data_rps = pd.merge(data_rps, hk_hold, how='left')

    # 获取最新的行业板块L3指数行情,计算行业RPS排名。
    l3_last_year = pro.sw_daily(trade_date=last_year_date)
    l3_current = pro.sw_daily(trade_date=daily_end_date)
    l3_front = pro.sw_daily(trade_date=front_date)
    l3_year = pro.sw_daily(trade_date=new_year_date)
    l3_week = pro.sw_daily(trade_date=industry_1_weeks)

    l3_20_days = pro.sw_daily(trade_date=industry_20_days)
    l3_3_weeks = pro.sw_daily(trade_date=industry_3_weeks)
    l3_6_weeks = pro.sw_daily(trade_date=industry_6_weeks)
    l3_7_months = pro.sw_daily(trade_date=industry_7_months)
    print(week_first_date, daily_end_date, last_year_date, new_year_date, front_date, industry_3_weeks,
          industry_6_weeks, hk_date)
    print("industry_1_week:", industry_1_weeks)

    # 20日板块强度
    l3_rps = pd.merge(l3_20_days, l3_current, on='ts_code')
    l3_rps = l3_rps.tail(227)
    l3_rps['index_code'] = l3_rps['ts_code']
    member_count = l3_rps['index_code'].count()
    l3_rps['industry_rps'] = l3_rps.apply(lambda m: (m['close_y'] - m['close_x']) / m['close_x'],
                                          axis=1).rank(ascending=True)
    l3_rps['industry_rps'] = round(100 * l3_rps['industry_rps'] / member_count, 1)
    l3_rps['industry_name'] = l3_rps['name_x']
    l3_rps = l3_rps[['index_code', 'industry_rps', 'industry_name']]

    # 年度板块强度基准值，即新年第一个交易日的强度排名和强度值
    l3_base_rps = pd.merge(l3_last_year, l3_year, on='ts_code')
    l3_base_rps = l3_base_rps.tail(227)
    l3_base_rps['index_code'] = l3_base_rps['ts_code']
    l3_base_rps['industry_base_rps'] = l3_base_rps.apply(lambda m: (m['close_y'] - m['close_x']) / m['close_x'],
                                                         axis=1).rank(ascending=True)
    l3_base_rps['industry_base_rank'] = round(100 * l3_base_rps['industry_base_rps'] / member_count, 1)
    l3_base_rps = l3_base_rps[['index_code', 'industry_base_rank', 'industry_base_rps']]

    # 与前一交易日比较板块强度 TODO: 完成前一交易日强度与今日强度的变化值
    l3_front_rps = pd.merge(l3_front, l3_current, on='ts_code')
    l3_front_rps = l3_front_rps.tail(227)
    l3_front_rps['index_code'] = l3_front_rps['ts_code']
    l3_front_rps['industry_front_rps'] = l3_front_rps.apply(lambda m: (m['close_y'] - m['close_x']) / m['close_x'],
                                                            axis=1).rank(ascending=True)
    l3_front_rps['industry_front_rank'] = round(100 * (l3_front_rps['industry_front_rps'] / member_count), 2)
    l3_front_rps = l3_front_rps[['index_code', 'industry_front_rank', 'industry_front_rps']]

    # 本周板块强度
    l3_week_rps = pd.merge(l3_week, l3_current, on='ts_code')
    l3_week_rps = l3_week_rps.tail(227)
    l3_week_rps['index_code'] = l3_week_rps['ts_code']
    l3_week_rps['industry_week_rps'] = l3_week_rps.apply(lambda m: (m['close_y'] - m['close_x']) / m['close_x'],
                                                         axis=1).rank(ascending=True)
    l3_week_rps['industry_week_rank'] = round(100 * l3_week_rps['industry_week_rps'] / member_count, 2)
    l3_week_rps = l3_week_rps[['index_code', 'industry_week_rank', 'industry_week_rps']]

    # 与年初比较板块强度 TODO： 完成前一交易日与今日强度的变化值
    l3_year_rps = pd.merge(l3_year, l3_current, on='ts_code')
    l3_year_rps = l3_year_rps.tail(227)
    l3_year_rps['index_code'] = l3_year_rps['ts_code']
    l3_year_rps['industry_year_rps'] = l3_year_rps.apply(
        lambda m: (m['close_y'] - m['close_x']) / m['close_x'], axis=1).rank(ascending=True)
    l3_year_rps['industry_year_rank'] = round(100 * l3_year_rps['industry_year_rps'] / member_count, 1)
    l3_year_rps = l3_year_rps[['index_code', 'industry_year_rank', 'industry_year_rps']]

    # 3周板块强度
    l3_3_weeks_rps = pd.merge(l3_3_weeks, l3_current, on='ts_code')
    l3_3_weeks_rps = l3_3_weeks_rps.tail(227)
    l3_3_weeks_rps['index_code'] = l3_3_weeks_rps['ts_code']
    l3_3_weeks_rps['industry_3_rps'] = l3_3_weeks_rps.apply(lambda m: (m['close_y'] - m['close_x']) / m['close_x'],
                                                            axis=1).rank(ascending=True)
    l3_3_weeks_rps['industry_3_rank'] = round(100 * l3_3_weeks_rps['industry_3_rps'] / member_count, 1)
    l3_3_weeks_rps['industry_name'] = l3_3_weeks_rps['name_x']
    l3_3_weeks_rps = l3_3_weeks_rps[['index_code', 'industry_3_rank', 'industry_3_rps', 'industry_name']]

    # 6周板块强度
    l3_6_weeks_rps = pd.merge(l3_6_weeks, l3_current, on='ts_code')
    l3_6_weeks_rps = l3_6_weeks_rps.tail(227)
    l3_6_weeks_rps['index_code'] = l3_6_weeks_rps['ts_code']
    l3_6_weeks_rps['industry_6_rps'] = l3_6_weeks_rps.apply(lambda m: (m['close_y'] - m['close_x']) / m['close_x'],
                                                            axis=1).rank(ascending=True)
    l3_6_weeks_rps['industry_6_rank'] = round(100 * l3_6_weeks_rps['industry_6_rps'] / member_count, 1)
    l3_6_weeks_rps = l3_6_weeks_rps[['index_code', 'industry_6_rank', 'industry_6_rps']]

    # 7个月板块强度
    l3_7_months_rps = pd.merge(l3_7_months, l3_current, on='ts_code')
    l3_7_months_rps = l3_7_months_rps.tail(227)
    l3_7_months_rps['index_code'] = l3_7_months_rps['ts_code']
    l3_7_months_rps['industry_7_rps'] = l3_7_months_rps.apply(lambda m: (m['close_y'] - m['close_x']) / m['close_x'],
                                                              axis=1).rank(ascending=True)
    l3_7_months_rps['industry_7_rank'] = round(100 * l3_7_months_rps['industry_7_rps'] / member_count, 1)
    l3_7_months_rps = l3_7_months_rps[['index_code', 'industry_7_rank', 'industry_7_rps']]

    # 行业指数聚合， 年度基准数据、前一交易日、年初、本周、3周、6周、7个月数据
    total_industry_rps = pd.merge(l3_base_rps, l3_front_rps, on='index_code')
    total_industry_rps = pd.merge(total_industry_rps, l3_year_rps, on='index_code')
    total_industry_rps = pd.merge(total_industry_rps, l3_week_rps, on='index_code')
    total_industry_rps = pd.merge(total_industry_rps, l3_3_weeks_rps, on='index_code')
    total_industry_rps = pd.merge(total_industry_rps, l3_6_weeks_rps, on='index_code')
    total_industry_rps = pd.merge(total_industry_rps, l3_7_months_rps, on='index_code')
    total_industry_rps['date'] = datetime.datetime.strptime(daily_end_date, "%Y%m%d").date()

    # 个股与行业指数L3相关联
    industry_member = pd.DataFrame()
    l3 = pro.index_classify(level='L3', src='SW')
    for l_code in l3['index_code']:
        index_member = pro.index_member(index_code=l_code)
        industry_member = industry_member.append(index_member, ignore_index=True)
    industry_member['ts_code'] = industry_member['con_code']
    l3_rps = pd.merge(industry_member, l3_rps, on='index_code')
    l3_rps = l3_rps[['ts_code', 'index_code', 'industry_name', 'industry_rps']]
    l3_stock_totality = l3_rps.groupby('index_code')['ts_code'].count()
    total_industry_rps = pd.merge(total_industry_rps, l3_stock_totality, on='index_code')
    total_industry_rps.rename(columns={'ts_code': 'stock_totality'}, inplace=True)

    """行业板块强度监控数据处理
        1、计算行业板块强度，并取前20名和后20名，计算周期：本周、3周、6周和7个月（28周）
           内容：本周、3周、6周和7个月的排名；强度值；年初涨幅；日升降幅度。
        2、创新高股票的行业组群，按照行业中创新高的股票数量由多到少展示。
        3、市场指数展示图，特殊标示年初至今前4指数、昨天表现前4指数。
        4、领头羊行情表：按照L2申万分类行业板块强度从强到弱进行降序展示沪深股市行情表，黑体加粗提醒涨幅1 % 以及创新高的股票。
        5、全市场综合排名前20股票，股价上涨和下跌的排名20的股票。
    """
    # 11、获取52周最高价，拼接成完整的年度数据。
    # 1.取历史月数据 TODO: 轮询过多，造成时间过长，应该只做每月最后一个交易日的数据提取即可。
    month_date = pro.query('trade_cal', start_date=daily_start_date, end_date=daily_end_date, is_open=1,
                           fields=['cal_date'])
    for query_date in month_date['cal_date']:
        query_data = pro.monthly(trade_date=query_date, fields=['trade_date', 'ts_code', 'high'])
        high_data = high_data.append(query_data, ignore_index=True)
    # 2.取当月的日数据
    first_date = '%d%d01' % (end_date.year, end_date.month)
    first_date = datetime.datetime.strptime(first_date, "%Y%m%d").date()
    daily_date = pro.query('trade_cal', start_date=first_date.strftime("%Y%m%d"), end_date=daily_end_date, is_open=1,
                           fields=['cal_date'])
    for query_date in daily_date['cal_date']:
        query_data = pro.daily(trade_date=query_date, fields=['trade_date', 'ts_code', 'high'])
        high_data = high_data.append(query_data, ignore_index=True)
    # 4.获得完整的52周最高价数据
    high_data = high_data.groupby('ts_code')['high'].max()
    # 5.获得复权数据 不精确。
    adj_factor1 = pro.adj_factor(trade_date=new_year_date)
    adj_factor = pro.adj_factor(trade_date=daily_end_date)
    adj_factor = pd.merge(adj_factor, adj_factor1, on='ts_code')
    adj_factor['adj_factor'] = adj_factor['adj_factor_y']/adj_factor['adj_factor_x']
    # 6.前复权最高价
    high_data = pd.merge(high_data, adj_factor, on='ts_code')
    high_data['high'] = round(high_data['high']*high_data['adj_factor'], 2)
    high_data = high_data[['ts_code', 'high']]

    # 12、数据联合
    data_rps = pd.merge(data_rps, high_data, on='ts_code')
    data_rps = pd.merge(data_rps, df_volume_ratio, on='ts_code')
    data_rps.sort_values(by='ts_code', ascending=True, inplace=True)
    data_rps.reset_index(drop=True, inplace=True)

    # 13、TODO:计算RPS排名，计算52周最高价与当前价的下降幅度，判断当日是否突破年新高价格。
    data_rps['rps'] = data_rps.apply(lambda m: round((m['close_y'] - m['close_x']) / m['close_x'], 2), axis=1).rank(
        ascending=True)
    x = data_rps['ts_code'].count()
    data_rps['rps'] = round(100 * data_rps['rps'] / x, 1)
    data_rps['decline_range'] = data_rps.apply(lambda m: round(100 * (m['close_y'] - m['high_y']) / m['high_y'], 1),
                                               axis=1)
    # 修正新高数据不准确，因复权因子影响的结果。
    data_rps['decline_range_0'] = data_rps['decline_range']
    data_rps.loc[data_rps['decline_range_0'] >= 0, 'decline_range'] = 0

    data_rps['new_high'] = data_rps.apply(lambda m: round(m['high_x']-m['high_y'], 2), axis=1)

    # 判断当日是否突破年新高价格。
    data_rps['new_high_flag'] = data_rps['new_high']
    data_rps.loc[data_rps['new_high'] < 0, 'new_high_flag'] = 0
    data_rps.loc[data_rps['new_high'] >= 0, 'new_high_flag'] = 1
    # 计算涨幅超过5%的股票
    data_rps['percent_7_rise'] = data_rps['pct_chg']
    data_rps.loc[data_rps['pct_chg'] >= 5, 'percent_7_rise'] = 1
    data_rps.loc[data_rps['pct_chg'] < 5, 'percent_7_rise'] = 0

    # 14、数据联合,计算综合排名。
    data_cumulative_rank = pd.merge(eps_smr_stability, data_rps, on='ts_code')
    data_cumulative_rank = pd.merge(data_cumulative_rank, high_data, on='ts_code')
    data_cumulative_rank = pd.merge(data_cumulative_rank, l3_rps, on='ts_code')
    data_cumulative_rank['cumulative_rank'] = data_cumulative_rank.apply(
        lambda m: round(m['eps'] * 2 + m['rps'] * 2 + m['smr'] + m['industry_rps'] + m['decline_range'], 2),
        axis=1).rank(ascending=True)
    x = data_cumulative_rank['ts_code'].count()
    data_cumulative_rank['cumulative_rank'] = round(100 * data_cumulative_rank['cumulative_rank'] / x, 1)
    data_cumulative_rank['pct_chg'] = round(data_cumulative_rank['pct_chg'], 2)
    data_cumulative_rank.reset_index(drop=True, inplace=True)
    data_cumulative_rank['period_date'] = pd.to_datetime(data_cumulative_rank['end_date'], dayfirst=True)
    data_cumulative_rank['period_date'] = data_cumulative_rank['period_date'].dt.strftime('%Y-%m-%d')
    data_cumulative_rank['ann_date'] = pd.to_datetime(data_cumulative_rank['ann_date'], dayfirst=True)
    data_cumulative_rank['ann_date'] = data_cumulative_rank['ann_date'].dt.strftime('%Y-%m-%d')
    data_cumulative_rank['code'] = data_cumulative_rank['ts_code']
    data_cumulative_rank['hk_hold'] = data_cumulative_rank['ratio']
    # TODO: 计算年内新高。
    new_high = data_cumulative_rank.groupby('industry_name')['new_high_flag'].sum()
    # TODO: 计算涨幅超过5%的股票
    percent_7_rise = data_cumulative_rank.groupby('industry_name')['percent_7_rise'].sum()


    # 获取股票名称
    symobl_name = pro.query('stock_basic', exchange='', list_status='L', fields='ts_code, name')
    data_cumulative_rank = pd.merge(data_cumulative_rank, symobl_name, on='ts_code')
    data_cumulative_rank = data_cumulative_rank[
        ['code', 'name', 'cumulative_rank', 'new_quarter_eps', 'eps', 'rps', 'smr', 'eps_stability', 'roe', 'decline_range',
         'volume_ratio', 'index_code', 'industry_name', 'industry_rps', 'period_date', 'ann_date', 'hk_hold', 'pct_chg',
         'forecast', 'p_change_min', 'p_change_max']]

    # 行业强度监控数据和个股聚合。
    total_industry_rps = pd.merge(total_industry_rps, new_high, on='industry_name')
    total_industry_rps = pd.merge(total_industry_rps, percent_7_rise, on='industry_name')
    # 15、写数据库
    con = sqlite3.connect('/Users/flowerhost/securityproject/db.sqlite3')
    data_cumulative_rank.to_sql("capital_management_cumulativerank", con, if_exists="replace", index=False)
    data_cumulative_rank.to_csv('/Users/flowerhost/securityproject/data/RPS_SMR.csv')
    total_industry_rps.to_sql('capital_management_monitorindustry', con, if_exists="replace", index=False)
    total_industry_rps.to_csv('/Users/flowerhost/securityproject/data/industry_rps.csv')

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
    ma10 = 0
    result = 0
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
                                        end_date=cal_date[0], ma=[10])

            stop_loss_data = stop_loss_data.sort_values(by=['trade_date'], ascending=[True])
            stop_loss_data = stop_loss_data[['trade_date', 'low', 'close', 'ma10']].values.tolist()

            # 比较前一交易日的最低价
            check_flag = TradeLists.objects.filter(code=stock_code).latest().flag
            print(stock_code, check_flag)
            print(stop_loss_data[-1][2])
            if check_flag == 'Bingo':
                result = stop_loss_data[-1][2]
                ma10 = stop_loss_data[-1][2]
            else:

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
                    count_number = 0  # 避免该变量无限循环相加
                    sum_values = 0  # 避免该变量无限循环相加

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
                gain_loss_rate = round(100 * (stock_close - buy) / buy, 2)
            else:
                gain_loss_rate = round(-100 * (stock_close - buy) / buy, 2)
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
            boll_up = round(ma10*1.09, 2)

            if buy > stop_loss:
                max_volume = round(risk_2 / (buy - stop_loss) - stock_amount, -2)
            else:
                max_volume = stock_amount

            if CapitalManagement.objects.exists():
                # 计算月初第一个交易日风险敞口，每月第一天完成资金账户进出转账更新。
                if check_month < current_month:
                    current_month_risk = round(AccountSurplus.objects.get(id=current_id-1).total_assets * 0.06, 2)
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
                                                     stock_close=stock_close, boll_up=boll_up,
                                                     max_volume=max_volume, buy=buy, gain_loss=gain_loss_rate,
                                                     date=date_cursor, month_risk_6=current_month_risk)
            else:
                management_id_cursor = management_id_cursor + 1
                current_month_risk = risk_6
                CapitalManagement.objects.create(id=management_id_cursor, risk_6=risk_6, stock_name=stock_name,
                                                 stop_loss=stop_loss, positions=stock_amount, stock_close=stock_close,
                                                 max_volume=max_volume, buy=buy, gain_loss=gain_loss_rate,
                                                 date=date_cursor, month_risk_6=current_month_risk, boll_up=boll_up)
            # 网页端展示数据准备
            query_date = CapitalManagement.objects.latest().date
            capital_management = CapitalManagement.objects.filter(date=query_date).values(
                'month_risk_6', 'risk_6', 'stock_name', 'stop_loss', 'stock_close', 'buy', 'gain_loss', 'positions',
                'max_volume', 'date', 'boll_up')
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


def fetch_data(stock_code):
    """抽取tushare数据"""
    query_date = datetime.date.today()
    start_query_date = query_date - datetime.timedelta(weeks=200)

    line_data = ts.pro_bar(ts_code=stock_code, freq='D', start_date=start_query_date.strftime("%Y%m%d"),
                           end_date=query_date.strftime("%Y%m%d"), adj='qfq', ma=[5, 10, 20, 50])
    origin_data = line_data.sort_values(by=['trade_date'], ascending=[True])

    close = [float(x) for x in origin_data['close']]
    origin_data['DIFF'], origin_data['DEA'], origin_data['MACD'] = talib.MACDEXT(
            np.array(close), fastperiod=12, fastmatype=1, slowperiod=26, slowmatype=1, signalperiod=9, signalmatype=1)
    origin_data['MACD'] = round(origin_data['MACD'] * 2, 2)
    origin_data['DIFF'] = round(origin_data['DIFF'], 2)
    origin_data['DEA'] = round(origin_data['DEA'], 2)
    origin_data = origin_data.tail(100)

    origin_data = origin_data[['trade_date', 'open', 'close', 'low', 'high', 'amount', 'ma5', 'ma10', 'ma20', 'ma50',
                               'MACD', 'DIFF', 'DEA']].values.tolist()

    return origin_data


def split_data(origin_data) -> dict:
    datas = []
    times = []
    vols = []
    macds = []
    difs = []
    deas = []
    ma5 = []
    ma10 = []
    ma20 = []
    ma50 = []

    for i in range(len(origin_data)):
        datas.append(origin_data[i][1:])
        times.append(origin_data[i][0:1][0])
        vols.append(origin_data[i][5])
        ma5.append(origin_data[i][6])
        ma10.append(origin_data[i][7])
        ma20.append(origin_data[i][8])
        ma50.append(origin_data[i][9])
        macds.append(origin_data[i][10])
        difs.append(origin_data[i][11])
        deas.append(origin_data[i][12])
    vols = [int(v) for v in vols]

    return {
        "datas": datas,
        "times": times,
        "vols": vols,
        "MA5": ma5,
        "MA10": ma10,
        "MA20": ma20,
        "MA50":ma50,
        "macds": macds,
        "difs": difs,
        "deas": deas,
    }

# def gain_loss(day_count: int):
#     """计算安全区域止损点"""
#     result: List[Union[float, str]] = []
#     for i in range(len(data['times'])):
#         if i < day_count:
#             result.append("-")
#             continue
#         sum_values = 0.0
#         count_number = 0
#         ma10 = 0
#         stop_loss = data["datas"][i-1][2]
#
#         for k in range(day_count):
#             latest_low = data["datas"][i-k][2]
#             for j in range(2):
#                 early_low = data["datas"][i-k-j][2]
#                 if early_low > latest_low:
#                     count_number = count_number + 1
#                     sum_values = sum_values + early_low - latest_low
#                 else:
#                     ma10 = data["datas"][i-k][6]
#
#         if count_number == 0:
#             stop_loss = ma10
#         else:
#             stop_loss = round((stop_loss - 3 * sum_values / count_number), 2)
#         result.append(stop_loss)
#     return result
#


def response_as_json(data):
    json_str = json.dumps(data)
    response = HttpResponse(
        json_str,
        content_type="application/json",
    )
    response["Access-Control-Allow-Origin"] = "*"
    return response


def json_response(data, code=200):
    data = {
        "code": code,
        "msg": "success",
        "data": data,
    }
    return response_as_json(data)


def json_error(error_string="error", code=500, **kwargs):
    data = {
        "code": code,
        "msg": error_string,
        "data": {}
    }
    data.update(kwargs)
    return response_as_json(data)


JsonResponse = json_response
JsonError = json_error


def draw_chart(stock_code) ->Grid:
    origin_data = fetch_data(stock_code)
    data = split_data(origin_data=origin_data)
    kline = (
        Kline()
        .add_xaxis(xaxis_data=data["times"])
        .add_yaxis(
            series_name="",
            y_axis=data["datas"],
            itemstyle_opts=opts.ItemStyleOpts(
                color="red",
                color0="green",
                border_color="red",
                border_color0="green",
            ),
            markpoint_opts=opts.MarkPointOpts(
                data=[
                    opts.MarkPointItem(type_="max", name="最大值"),
                    opts.MarkPointItem(type_="min", name="最小值"),
                ]
            ),
        )
        .set_global_opts(
            # title_opts=opts.TitleOpts(title="K线周期图表", pos_left="0"),
            xaxis_opts=opts.AxisOpts(
                type_="category",
                is_scale=True,
                boundary_gap=False,
                axisline_opts=opts.AxisLineOpts(is_on_zero=False),
                splitline_opts=opts.SplitLineOpts(is_show=False),
                split_number=20,
                min_="dataMin",
                max_="dataMax",
            ),
            yaxis_opts=opts.AxisOpts(
                is_scale=True, splitline_opts=opts.SplitLineOpts(is_show=True)
            ),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
            datazoom_opts=[
                opts.DataZoomOpts(
                    is_show=False, type_="inside", xaxis_index=[0, 0], range_end=100
                ),
                opts.DataZoomOpts(
                    is_show=True, xaxis_index=[0, 1], pos_top="97%", range_end=100
                ),
                opts.DataZoomOpts(is_show=False, xaxis_index=[0, 2], range_end=100),
            ],
            # 三个图的 axis 连在一块
            axispointer_opts=opts.AxisPointerOpts(
                is_show=True,
                link=[{"xAxisIndex": "all"}],
                label=opts.LabelOpts(background_color="#777"),
            ),
        )
    )

    kline_line = (
        Line()
        .add_xaxis(xaxis_data=data["times"])
        .add_yaxis(
            series_name="MA5",
            y_axis=data["MA5"],
            is_smooth=True,
            is_hover_animation=False,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="MA10",
            y_axis=data["MA10"],
            is_smooth=True,
            is_hover_animation=False,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="MA20",
            y_axis=data["MA20"],
            is_smooth=True,
            is_hover_animation=False,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="MA50",
            y_axis=data["MA50"],
            is_smooth=True,
            is_hover_animation=False,
            linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
            label_opts=opts.LabelOpts(is_show=False),
        )
        # .add_yaxis(
        #     series_name=" 止损点",
        #     y_axis=gain_loss(day_count=10),
        #     is_smooth=True,
        #     is_hover_animation=False,
        #     linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
        #     label_opts=opts.LabelOpts(is_show=False),
        # )
        .set_global_opts(xaxis_opts=opts.AxisOpts(type_="category"))
    )

    # Overlap Kline + Line
    overlap_kline_line = kline.overlap(kline_line)

    # Bar-1
    bar_1 = (
        Bar()
        .add_xaxis(xaxis_data=data["times"])
        .add_yaxis(
            series_name="Volume",
            y_axis=data["vols"],
            xaxis_index=1,
            yaxis_index=1,
            label_opts=opts.LabelOpts(is_show=False),
            # itemstyle_opts=opts.ItemStyleOpts(
            #     color=JsCode(
            #         """
            #     function(params) {
            #         var colorList;
            #         if (barData[params.dataIndex][1] > barData[params.dataIndex][0]) {
            #             colorList = 'red';
            #         } else {
            #             colorList = 'green';
            #         }
            #         return colorList;
            #     }
            #     """
            #     )
            # ),
        )
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(
                type_="category",
                grid_index=1,
                axislabel_opts=opts.LabelOpts(is_show=False),
            ),
            legend_opts=opts.LegendOpts(is_show=False),
        )
    )

    # Bar-2 (Overlap Bar + Line)
    bar_2 = (
        Bar()
        .add_xaxis(xaxis_data=data["times"])
        .add_yaxis(
            series_name="MACD",
            y_axis=data["macds"],
            xaxis_index=2,
            yaxis_index=2,
            label_opts=opts.LabelOpts(is_show=False),
            itemstyle_opts=opts.ItemStyleOpts(
                color=JsCode(
                    """
                        function(params) {
                            var colorList;
                            if (params.data >= 0) {
                              colorList = 'red';
                            } else {
                              colorList = 'green';
                            }
                            return colorList;
                        }
                        """
                )
            ),
        )
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(
                type_="category",
                grid_index=2,
                axislabel_opts=opts.LabelOpts(is_show=False),
            ),
            yaxis_opts=opts.AxisOpts(
                grid_index=2,
                split_number=4,
                axisline_opts=opts.AxisLineOpts(is_on_zero=False),
                axistick_opts=opts.AxisTickOpts(is_show=False),
                splitline_opts=opts.SplitLineOpts(is_show=False),
                axislabel_opts=opts.LabelOpts(is_show=True),
            ),
            legend_opts=opts.LegendOpts(is_show=False),
        )
    )

    line_2 = (
        Line()
        .add_xaxis(xaxis_data=data["times"])
        .add_yaxis(
            series_name="DIF",
            y_axis=data["difs"],
            xaxis_index=2,
            yaxis_index=2,
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            series_name="DEA",
            y_axis=data["deas"],
            xaxis_index=2,
            yaxis_index=2,
            label_opts=opts.LabelOpts(is_show=False),
        )
        .set_global_opts(legend_opts=opts.LegendOpts(is_show=False))
    )
    # 最下面的柱状图和折线图
    overlap_bar_line = bar_2.overlap(line_2)

    grid_chart = (
        Grid()
        .add_js_funcs("var barData = {}".format(data["datas"]))
        .add(overlap_kline_line, grid_opts=opts.GridOpts(pos_left="3%", pos_right="1%", height="60%"), )
        .add(bar_1, grid_opts=opts.GridOpts(pos_left="3%", pos_right="1%", pos_top="71%", height="10%"), )
        .add(overlap_bar_line, grid_opts=opts.GridOpts(pos_left="3%", pos_right="1%", pos_top="82%", height="14%"), )
        .dump_options_with_quotes()
    )
    return grid_chart


def bar_base() -> Bar:
    c = (
        Bar()
        .add_xaxis(["衬衫", "羊毛衫", "雪纺衫", "裤子", "高跟鞋", "袜子"])
        .add_yaxis("商家A", [randrange(0, 100) for _ in range(6)])
        .add_yaxis("商家B", [randrange(0, 100) for _ in range(6)])
        .set_global_opts(title_opts=opts.TitleOpts(title="Bar-基本示例", subtitle="我是副标题"))
        .dump_options_with_quotes()
    )
    return c


class ChartView(APIView):
    def get(self, request, *args, **kwargs):
        print(request.GET.get('code'))

        return JsonResponse(json.loads(draw_chart(stock_code='002876.SZ')))


class IndexView(APIView):
    def get(self, request, *args, **kwargs):
        return render(request, 'capital_management/line_index.html')


def monitor(request):
    """行业强度及板块领头羊前五和后五名监控 2020-04-16
            1、计算行业板块强度，并取前20名和后20名，计算周期：本周、3周、6周和7个月（28周）
                内容：本周、3周、6周和7个月的排名；强度值；年初涨幅；日升降幅度。
            2、创新高股票的行业组群，按照行业中创新高的股票数量由多到少展示。
            3、市场指数展示图，特殊标示年初至今前4指数、昨天表现前4指数。
            4、领头羊行情表：按照L2申万分类行业板块强度从强到弱进行降序展示沪深股市行情表，黑体加粗提醒涨幅1%以及创新高的股票。
            5、全市场综合排名前20股票，股价上涨和下跌的排名20的股票。

    """
    # 页面展示
    industry_ranks = MonitorIndustry.objects.filter(stock_totality__gt=3).values(
        'index_code', 'industry_name', 'industry_week_rank', 'industry_3_rank', 'industry_6_rank', 'industry_7_rank',
        'date', 'stock_totality', 'new_high_flag', 'percent_7_rise').order_by('-industry_week_rank')
    return render(request, 'capital_management/monitor.html', locals())


def evaluate(request):
    """全市场综合排名"""
    # 页面展示
    cumulative_ranks = CumulativeRank.objects.filter(cumulative_rank__gt=80, roe__gt=15, decline_range__gt=-35, p_change_min__gt=40).values(
        'code', 'name', 'eps', 'eps_stability', 'smr', 'period_date', 'rps', 'cumulative_rank', 'decline_range', 'volume_ratio',
        'ann_date', 'new_quarter_eps', 'industry_name', 'industry_rps', 'hk_hold', 'pct_chg', 'p_change_min',
        'p_change_max', 'forecast').order_by('-cumulative_rank')

    return render(request, 'capital_management/evaluate.html', locals())


def monitor_detail(request):
    """行业板块强度细化"""
    index_code = request.GET.get('index_code')
    cumulative_ranks = CumulativeRank.objects.filter(index_code=index_code, cumulative_rank__gt=79).values(
        'code', 'name', 'eps', 'eps_stability', 'smr', 'period_date', 'rps', 'cumulative_rank', 'decline_range', 'volume_ratio',
        'ann_date', 'new_quarter_eps', 'industry_name', 'industry_rps', 'hk_hold', 'pct_chg', 'p_change_min',
        'p_change_max', 'forecast').order_by('-pct_chg')
    return render(request, 'capital_management/evaluate.html', locals())


def management_detail(request):
    """ 持仓股票变动细化"""
    stock_name = request.GET.get('stock_name')
    stocks = TradeLists.objects.filter(name=stock_name).values(
        'code', 'name', 'price', 'flag', 'date', 'trade_resource', 'quantity', 'total_capital',
        'account__name', 'tradeperformance__close', 'tradeperformance__moving_average',
        'tradeperformance__performance', 'tradeperformance__trade_performance').order_by('-date')

    return render(request, 'capital_management/index.html', locals())

