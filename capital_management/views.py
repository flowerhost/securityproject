# Create your views here.

from django.shortcuts import render, redirect
from .models import TradeLists, TradeDailyReport, CapitalAccount, AccountSurplus, Clearance, TradePerformance, Broker
from .models import Positions, CapitalManagement, EvaluateStocks
from .form import BrokerForm, TradeListsForm, CapitalAccountForm

from django.db.models import Sum

import time
import datetime

"""tushare类数据接口"""
import tushare as ts

ts.set_token('033ad3c72aef8ce38d29d34482058b87265b32d788fb6f24d2e0e8d6')
pro = ts.pro_api()


def stock_basic(request):
    """股票列表"""
    query_data = pro.query('stock_basic', exchange='', list_status='L')
    for data in query_data:
        name = data['name'].values[0]


def index(request):
    stocks = TradeLists.objects.values(
        'code', 'name', 'price', 'flag', 'date', 'trade_resource', 'quantity', 'total_capital',
        'account__broker__capitalaccount__name', 'tradeperformance__close', 'tradeperformance__moving_average',
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
    start_query_date = query_date - datetime.timedelta(days=250)

    if request.method == "POST":
        stock_code = request.POST.get("stock_code")
        for _ in range(3):
            try:
                query_result = pro.query('stock_basic', ts_code=stock_code, fields='name')
                line_data = ts.pro_bar(ts_code=stock_code, start_date=start_query_date.strftime("%Y%m%d"),
                                       end_date=query_date.strftime("%Y%m%d"))
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
            return redirect('capital_management:trade')

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
            return redirect('capital_management:index')
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
        daily_report_date_cursor = TradeDailyReport.objects.latest().date
        # daily_report_end_date = TradeLists.objects.latest().date
        trade_daily_id_cursor = TradeDailyReport.objects.last().id
    else:
        daily_report_date_cursor = TradeLists.objects.earliest().date
        # daily_report_end_date = TradeLists.objects.latest().date
        trade_daily_id_cursor = 0
    # 2.运算解析数据
    new_value_set = TradeLists.objects.filter(
        date__gte=daily_report_date_cursor).values('date', 'account_id', 'code').annotate(
        amount_num=Sum('quantity'), capital_num=Sum('total_capital'), fee_num=Sum('total_fee'))
    for new_value in new_value_set:
        trade_daily_date = new_value['date']
        trade_daily_code = new_value['code']
        trade_daily_account_id = new_value['account_id']  # 资金账户_id

        flag = TradeDailyReport.objects.filter(
            date=trade_daily_date, code=trade_daily_code, account_id=trade_daily_account_id)
        if flag:
            pass
        else:

            trade_daily_id_cursor = trade_daily_id_cursor + 1
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

    # 1.判断Positions状态
    if Positions.objects.exists():
        positions_id_cursor = Positions.objects.last().id  # 只能取最新日期的第一条记录 latest().id

    else:
        positions_id_cursor = 0

    total_fee = 0
    clearance_stock_list = {}  # 清仓股票名单
    statistic_date = datetime.date.today()
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
        clearance_stock_list = {}  # 清仓股票名单

        date_cursor = datetime.datetime.strptime(cal[0], "%Y%m%d").strftime("%Y-%m-%d")
        flag = AccountSurplus.objects.filter(date=date_cursor)
        if flag:
            pass
        else:
            account_surplus_data = TradeDailyReport.objects.filter(date__lte=date_cursor).values(
                'account_id', 'code').annotate(stock_amount=Sum('amount'), stock_fee=Sum('total_fee'),
                                               stock_capital=Sum('total_capital'))

            for account_surplus in account_surplus_data:
                stock_code = account_surplus['code']
                stock_name = TradeDailyReport.objects.filter(code=stock_code).values('name').latest()['name']
                # 记录清仓股票和账号 字典{stock_code:account_id}
                if account_surplus['stock_amount'] == 0:  # 一个大坑！害得我抓狂！
                    clearance_stock_list[stock_code] = account_surplus['account_id']

                # tushare 获取股票当日收盘价
                for _ in range(3):
                    try:
                        query_result = pro.query('daily', ts_code=stock_code, start_date=cal[0], end_date=cal[0])
                    except:
                        time.sleep(1)
                    else:
                        stock_close = query_result['close'].values[0]
                account_surplus_account_id = account_surplus['account_id']
                # 账户总市值= 个股市值之和；close 收盘价，计算个股市值
                stock_amount = account_surplus['stock_amount']
                stock_market_capital = round(stock_amount * stock_close, 2)
                market_capital = round(market_capital + stock_market_capital, 2)
                # 账户总费用= 每个股票费用之和
                stock_fee = round(account_surplus['stock_fee'], 2)
                total_fee = round(total_fee + stock_fee, 2)
                # 账户总交易金额
                stock_capital = round(account_surplus['stock_capital'], 2)  # 个股投入资金成本，有正负号区分，买入为负，卖出为正。
                if stock_amount == 0:
                    stock_cost = 0
                else:
                    stock_cost = round(stock_capital / stock_amount * -1, 2)
                total_capital = round((total_capital + account_surplus['stock_capital']), 2)
                # 账户浮动盈亏
                stock_position_gain_loss = round((stock_amount * stock_close + stock_capital), 2)
                position_gain_loss = round((position_gain_loss + stock_position_gain_loss), 2)
                stock_open_date = TradeDailyReport.objects.filter(code=stock_code).earliest().date

                # 股票持仓情况更新
                if stock_amount == 0:
                    pass
                else:
                    positions_id_cursor = positions_id_cursor + 1
                    Positions.objects.create(id=positions_id_cursor, account_id=account_surplus_account_id,
                                             code=stock_code,
                                             name=stock_name, cost=stock_cost, amount=stock_amount, fee=stock_fee,
                                             gain_loss=stock_position_gain_loss, market_capital=stock_market_capital,
                                             open_date=stock_open_date, final_cost=stock_capital, date=date_cursor)
            # 期初资产
            initial_capital = CapitalAccount.objects.get(id=account_surplus_account_id).initial_capital
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

    """清仓股票结算"""
    if Clearance.objects.exists():
        clearance_id_cursor = Clearance.objects.last().id
    else:
        clearance_id_cursor = 0

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
            profit = round(clearance_data[0]['profit'], 2)
            total_fee = round(clearance_data[0]['transfer_fee'], 2)

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
    cal = pro.query('trade_cal', start_date=gain_loss_date.strftime("%Y%m%d"),
                    end_date=calculate_date.strftime("%Y%m%d"), is_open=1, fields=['cal_date'])
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
        date_cursor = datetime.datetime.strptime(cal_date[0], "%Y%m%d").strftime("%Y-%m-%d")

        positions_data = Positions.objects.filter(  # annotate 对于相同的名字的股票 叠加计算，出现错误。
            date=date_cursor).values('code', 'name').annotate(final_cost=Sum('final_cost'), amount=Sum('amount'))

        for position in positions_data:
            stock_name = position['name']
            stock_code = position['code']
            stock_amount = position['amount']
            buy = round(position['final_cost'] / position['amount'] * -1, 2)

            # 计算止损点
            stop_loss_data = ts.pro_bar(ts_code=stock_code, adj='qfq', start_date=cal['cal_date'].values[-11],
                                        end_date=cal['cal_date'].values[-1])
            stop_loss_data = stop_loss_data.sort_values(by=['trade_date'], ascending=[True])
            stop_loss_data = stop_loss_data[['trade_date', 'low', 'close']].values.tolist()
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

            result = round((stop_loss_data[-2][1] - 3 * sum_values / count_number), 2)
            if CapitalManagement.objects.exists():
                last_stop_loss = CapitalManagement.objects.filter(
                    date=date_cursor, stock_name=stock_name).values('stop_loss')
                if last_stop_loss.exists():
                    last_loss = last_stop_loss[0]['stop_loss']
                else:
                    last_loss = 0
            else:
                last_loss = 0
            # 比较前一交易日的止损点，取大值，避免止损点下滑, 如果跌破买入价的8%则无条件止损，表明买点不好。
            stop_loss = round(max(result, last_loss, buy * 0.92), 2)

            stock_close = stop_loss_data[-1][2]
            gain_loss_rate = round((stock_close - buy) / buy, 2)
            # 获取月初资产*6%
            assets = AccountSurplus.objects.get(date=date_cursor).total_assets
            current_month = datetime.datetime.strptime(cal_date[0], "%Y%m%d").month
            current_id = AccountSurplus.objects.get(date=date_cursor).id
            if current_id == 1:
                check_month = current_month
            else:
                check_month = AccountSurplus.objects.get(id=current_id-1).date.month

            # 判断资金的风险敞口
            risk_2 = round(assets * 0.02, -2)
            risk_6 = round(assets * 0.06, -2)
            # 最多3个交易标的。每个交易标的不得超过capital_2，总风险敞口不超过capital_6
            # while capital_6:
            #     object_number = CapitalManagement.objects.filter(date=caculate_date_cursor).Count()
            #     if object_number < 3:
            #
            if buy > stop_loss:
                max_volume = round(risk_2 / (buy - stop_loss) - stock_amount, -2)
            else:
                max_volume = stock_amount

            if CapitalManagement.objects.exists():
                # 计算月初风险敞口
                if check_month < current_month:
                    current_month_risk = round(assets * 0.06, 2)
                else:
                    current_month_risk = CapitalManagement.objects.last().month_risk_6
                flag = CapitalManagement.objects.filter(date=date_cursor, stock_name=stock_name)
                if flag:
                    pass
                else:
                    management_id_cursor = management_id_cursor + 1
                    CapitalManagement.objects.create(id=management_id_cursor, risk_6=risk_6, stock_name=stock_name,
                                                     stop_loss=stop_loss, positions=stock_amount, stock_close=stock_close,
                                                     max_volume=max_volume, buy=buy, gain_loss=gain_loss_rate,
                                                     date=date_cursor, month_risk_6=current_month_risk)
            else:
                management_id_cursor = management_id_cursor + 1
                current_month_risk = risk_6
                CapitalManagement.objects.create(id=management_id_cursor, risk_6=risk_6, stock_name=stock_name,
                                                 stop_loss=stop_loss, positions=stock_amount, stock_close=stock_close,
                                                 max_volume=max_volume, buy=buy, gain_loss=gain_loss_rate,
                                                 date=date_cursor, month_risk_6=current_month_risk)

            query_date = CapitalManagement.objects.latest().date
            capital_management = CapitalManagement.objects.filter(date=query_date).values(
                'month_risk_6', 'risk_6', 'stock_name', 'stop_loss', 'stock_close', 'buy', 'gain_loss', 'positions',
                'max_volume', 'date')
            # TODO：剩余敞口资金数
            current_risk_measurement = round(risk_6 - current_month_risk, -2)
            if current_risk_measurement > 0:
                message = {'risk_message': "趋势向好！敞口增加"}
                risk_exposure = current_risk_measurement
            elif current_risk_measurement < -current_month_risk*0.06:
                message = {'risk_message': "交易结束！本月损失"}
                risk_exposure = round(current_risk_measurement/0.06, -2)
            else:
                message = {'risk_message': "趋势向坏，敞口减少"}
                risk_exposure = round(current_risk_measurement/0.06, -2)

    return render(request, 'capital_management/management.html', locals())


def evaluate(request):
    """股票基本面评价
        1、获取RPS：股票强度指标大于87%以上。通过通达信软件获取。
        2、获取行业RPS：行业强度位于前6位。参考值：>= 90
        3、通过tushare接口fina_indicator获得数据，写入EvaluateStocks表中。股票代码为通达信导入。
        4、计算eps: 最近三个年度增长率25%以上，下一年度25%以上的预测值；最近三个季度的增长率有大幅上涨，25%-30%以上为佳。
        5、计算sales：or_yoy 最近三个季度营业收入增速趋势，或者上一季度的增长率25%以上。
        6、计算ROE：每股净资产收益率大于17%以上，一般在25%---50%之间为优秀。
        7、计算q_op_qoq： 最近一个季度的营业利润是增长的（环比增长率为正），而且是接近此股最高点时营业利润增长率。
        8、计算吸筹/出货：未考虑好，待进一步研究学习。
        9、监控量比变化：当日成交量显著地放大50%以上。
        10、计算沪深港通交易占比。tushare接口：k_hold。
        11、计算股票综合排名。便于及时浏览关注。
            以上指标分配不同的权重，然后进行排名。对排名靠前的股票进行四项指标独立研究：EPS、ROE、SMR和吸筹/出货，同时发现量比变化。
        12、大盘处于上升趋势。
    """
    # query_date = CapitalManagement.objects.last().date
    # stock_code = '000001.SZ'
    # price_strengthh_query_data = RelativePriceStrength.objects.values(
    #     'RPS_50', 'RPS_120', 'RPS_industry_group', 'date', 'evaluation__eps_rate', 'evaluation__front_q1_eps_rate',
    #     'evaluation__front_y1_eps_rate', 'evaluation__front_q1_sales_rate', 'evaluation__roe', 'evaluation__q_op_qoq',
    #     'evaluation__period_date')
    # RelativePriceStrength.objects.create(evaluation=EvaluateStocks.objects.get(code=stock_code))  # 增加关联
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
        query_result = query_result[['end_date', 'basic_eps_yoy', 'or_yoy', 'roe', 'q_op_qoq']]

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
                                          front_q3_sales_rate=front_q3_sales_rate, eps_rate=eps_rate, roe=roe)

    evaluate_query_result = EvaluateStocks.objects.all().order_by('-date')

    return render(request, 'capital_management/evaluate.html', locals())


