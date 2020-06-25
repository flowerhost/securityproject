from django.db import models
from django.contrib.auth.models import User
# import select2.fields
# import select2.models

# Create your models here.
from django.utils import timezone
from django.utils.html import format_html


class Broker(models.Model):
    """券商列表"""
    name = models.CharField(max_length=80, verbose_name='证券公司')
    nick_name = models.CharField(max_length=80, unique=True, verbose_name='昵称')

    rate = models.FloatField(verbose_name='券商佣金')
    stamp_duty = models.FloatField(verbose_name='印花税费')
    transfer_fee = models.FloatField(verbose_name='过户费')

    date_added = models.DateField(auto_now_add=True, verbose_name='注册时间')
    introduction = models.TextField(verbose_name='简介')

    def __str__(self):
        """返回模型的券商名"""
        return self.name

    class Meta:
        verbose_name = '证券公司'
        verbose_name_plural = '证券公司'

        get_latest_by = 'date_added'


class CapitalAccount(models.Model):
    """证券资金流水账户"""

    name = models.CharField(max_length=80, verbose_name='账户名称')  # name = Broker.nick_name
    broker = models.ForeignKey(Broker, on_delete=models.DO_NOTHING, verbose_name='证券公司')
    initial_capital = models.FloatField(verbose_name='期初资产')

    date = models.DateField(verbose_name='创建日期', default=timezone.now())

    class Meta:
        verbose_name = '证券资金账户'
        verbose_name_plural = '证券资金账户'
        get_latest_by = 'date'

    def __str__(self):
        return self.name


class AccountSurplus(models.Model):
    """账户盈余表"""

    account = models.ForeignKey(Broker, on_delete=models.DO_NOTHING, verbose_name='账户名称')

    total_assets = models.FloatField(verbose_name='总资产')
    market_capital = models.FloatField(verbose_name='总市值')
    fund_balance = models.FloatField(verbose_name='资金余额')
    position_gain_loss = models.FloatField(verbose_name='浮动盈亏')
    total_fee = models.FloatField(verbose_name='总费用')
    final_cost = models.FloatField(verbose_name='总投入')
    initial_capital = models.FloatField(verbose_name='期初资产')
    update_flag = models.BooleanField(verbose_name='数据更新标识')

    date = models.DateField(verbose_name='结算日期', default=timezone.now())

    class Meta:
        verbose_name = '账户盈余表'
        verbose_name_plural = '账户盈余表'

        get_latest_by = 'date'

    def __str__(self):

        return self.position_gain_loss


class StockBasis(models.Model):
    """股票基本情况"""
    name = models.CharField(max_length=80, verbose_name='股票名称')
    ts_code = models.CharField(primary_key=True, max_length=10, verbose_name='股票代码')
    symbol = models.CharField(max_length=10, verbose_name='股票代码')
    industry = models.CharField(max_length=80, verbose_name='所属行业')
    area = models.CharField(max_length=20, verbose_name='地区')
    market = models.CharField(max_length=20, verbose_name='市场类型')

    def __str__(self):
        return self.name


class TradeLists(models.Model):
    """交易记录流水"""

    name = models.CharField(max_length=80, verbose_name='股票名称')
    code = models.CharField(max_length=10, verbose_name='股票代码')

    OPERATION_CHOICE = (
        (u'B', u'普通买入'),
        (u'S', u'普通卖出'),
        (u'R', u'融资买入'),
        (u'T', u'融券卖出'),
        (u'P', u'送配股')
    )
    flag = models.CharField(max_length=20, verbose_name='操作方向', choices=OPERATION_CHOICE)
    # 基础数据
    price = models.FloatField(verbose_name='买卖价格')
    quantity = models.IntegerField(verbose_name='买卖数量')
    date = models.DateField(verbose_name='交易日期', default=timezone.now())
    brokerage = models.FloatField(verbose_name='交易佣金')
    stamp_duty = models.FloatField(verbose_name='印花税')
    transfer_fee = models.FloatField(verbose_name='过户费')
    total_fee = models.FloatField(verbose_name='手续费用')
    total_capital = models.FloatField(verbose_name='交易总额')
    clear_flag = models.CharField(max_length=100, verbose_name='清仓标识---清仓股票表_ID')
    account = models.ForeignKey(Broker, on_delete=models.CASCADE, verbose_name='交易账户')
    # 操作依据，即信息源头
    trade_resource = models.CharField(max_length=80, verbose_name='信息源头')

    # 设置操作方向字段颜色，区别 普通买入、普通卖出、融资买入、融资卖出
    def colored_flag(self):
        if self.flag == 'B':
            color_code = 'red'
        elif self.flag == 'S':
            color_code = 'green'
        elif self.flag == 'R':
            color_code = 'yellow'
        else:
            color_code = 'blue'
        return format_html(
            '<span style="color:{};">{}</span>',
            color_code,
            self.get_flag_display(),
        )
    colored_flag.short_description = u"操作方向"

    # # 设置后台管理的时间格式：2019年9月23日 而不是2019年9月23日 20：33
    # # def date(self):
    # #     return self.date.strftime('%Y年%m月%d日')
    #
    # date.short_description = u'交易日期'
    # date.admin_order_field = '-transaction_date'

    class Meta:
        verbose_name = '股票交易记录'
        verbose_name_plural = '股票交易记录'

        get_latest_by = 'date'  # 获取最新的 or 最早的记录

    def __str__(self):
        return self.name


class TradePerformance(models.Model):
    """交易表现评价表"""
    trade = models.ForeignKey(TradeLists, on_delete=models.CASCADE, verbose_name='交易记录')
    close = models.FloatField(verbose_name='收盘价')
    moving_average = models.FloatField(verbose_name='十日均线')
    high_price = models.FloatField(verbose_name='最高价')
    low_price = models.FloatField(verbose_name='最低价')
    boll_up = models.FloatField(verbose_name='BOLL线上轨')
    boo_down = models.FloatField(verbose_name='BOLL线下轨')
    performance = models.FloatField(verbose_name='买卖评价')  # 每笔交易的评价
    trade_performance = models.FloatField(verbose_name='总体评价')  # 清仓后股票的交易总体评价

    date = models.DateField(verbose_name='评价日期', default=timezone.now())

    class Meta:
        verbose_name = '交易表现评价'
        verbose_name_plural = '交易表现评价'

        get_latest_by = 'date'  # 定位最新记录


class TradeDailyReport(models.Model):
    """交易日报表"""

    name = models.CharField(max_length=80, verbose_name='股票名称')
    code = models.CharField(max_length=10, verbose_name='股票代码')

    cost = models.FloatField(verbose_name='成本价')
    amount = models.FloatField(verbose_name='买卖股数')
    total_capital = models.FloatField(verbose_name='交易总额')
    total_fee = models.FloatField(verbose_name='手续费')

    date = models.DateField(verbose_name='结算日期', default=timezone.now())

    account = models.ForeignKey(Broker, on_delete=models.CASCADE, verbose_name='证券账户')
    update_flag = models.BooleanField(verbose_name='数据更新标志')

    class Meta:
        verbose_name = '股票持仓情况'
        verbose_name_plural = '股票持仓情况'

        get_latest_by = 'date'  # 用于获得最早和最新的记录


class Positions(models.Model):
    """持仓情况表"""
    account = models.ForeignKey(Broker, on_delete=models.DO_NOTHING, verbose_name='资金账号')

    code = models.CharField(max_length=10, verbose_name='股票代码')
    name = models.CharField(max_length=80, verbose_name='股票名称')

    cost = models.FloatField(verbose_name='每股成本')
    amount = models.FloatField(verbose_name='股票数量')
    fee = models.FloatField(verbose_name=' 费用')
    gain_loss = models.FloatField(verbose_name='浮动盈亏')
    final_cost = models.FloatField(verbose_name='总投入')
    market_capital = models.FloatField(verbose_name='市值')

    open_date = models.DateField(verbose_name=' 建仓日期')
    date = models.DateField(verbose_name='结算日起', default=timezone.now())

    class Meta:
        get_latest_by = 'date'


class Clearance(models.Model):
    """清仓股票情况表"""

    name = models.CharField(max_length=80, verbose_name='股票名称')
    code = models.CharField(max_length=10, verbose_name='股票代码')

    open_date = models.DateField(verbose_name='建仓日期')
    clear_date = models.DateField(verbose_name='清仓日期')

    invest_capital = models.FloatField(verbose_name='累计投入金额')  # 买入投入
    fee = models.FloatField(verbose_name='交易费用')
    profit = models.FloatField(verbose_name='盈亏金额')

    account = models.ForeignKey(Broker, on_delete=models.DO_NOTHING, verbose_name='证券账户')

    class Meta:
        verbose_name = '清仓股票情况'
        verbose_name_plural = '清仓股票情况'
        get_latest_by = 'clear_date'


class EventLog(models.Model):
    """日志
        在关联对象被删除时，不能一并删除，须保留日志，
        因此on_delete=models.SET_NULL,
    """

    name = models.CharField(max_length=120, verbose_name='事件名')
    event_type_choice = (
        (0, '其他'),
        (1, '股票买卖'),
        (2, '证券账户维护'),

    )

    account = models.ForeignKey(Broker, on_delete=models.DO_NOTHING,
                                blank=True, null=True, verbose_name='资金账户变化')
    trade_details = models.ForeignKey(TradeLists, on_delete=models.CASCADE,
                                      blank=True, null=True, verbose_name='股票买卖变化')
    event_type = models.CharField('事件类型', max_length=40, choices=event_type_choice, default=1)
    detail = models.TextField('事件详情')
    memo = models.TextField('备注', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '事件日志'
        verbose_name_plural = '事件日志'


class MarketQuotation(models.Model):
    """
    股票行情--以日为单位
    """

    name = models.CharField(max_length=20, verbose_name='股票名称')
    code = models.CharField(max_length=10, verbose_name='股票代码')

    open = models.FloatField(verbose_name='开盘价')
    close = models.FloatField(verbose_name='收盘价')
    high = models.FloatField(verbose_name='最高价')
    low = models.FloatField(verbose_name='最低价')

    volume = models.FloatField(verbose_name='成交数量')
    value = models.FloatField(verbose_name='成交金额')

    date = models.DateField(verbose_name='交易日期')

    class Meta:
        verbose_name = '行情记录'
        verbose_name_plural = '行情记录'


class CapitalManagement(models.Model):
    """资金管理和仓位管理"""

    risk_6 = models.FloatField(verbose_name='当日账户风险敞口')
    month_risk_6 = models.FloatField(verbose_name='月初账户风险敞口')

    stock_name = models.CharField(max_length=80, verbose_name=' 交易标的物')
    stock_close = models.FloatField(verbose_name='收盘价')
    stop_loss = models.FloatField(verbose_name=' 止损点')
    buy = models.FloatField(verbose_name='买入价')
    gain_loss = models.FloatField(verbose_name='盈亏比')
    positions = models.FloatField(verbose_name='持仓股数')
    max_volume = models.FloatField(verbose_name='可买股数')
    boll_up = models.FloatField(verbose_name='通道上限')

    date = models.DateField(verbose_name='建仓日期')

    class Meta:
        verbose_name_plural = ' 仓位管理'
        verbose_name = '仓位管理'
        get_latest_by = 'date'


class MyStockLists(models.Model):
    """自选股"""

    code = models.CharField(max_length=10, verbose_name='股票代码')
    name = models.CharField(max_length=80, verbose_name='股票名称')

    change_rate = models.FloatField(verbose_name='涨跌幅度')
    price = models.FloatField(verbose_name='现价')
    change_amount = models.FloatField(verbose_name='涨跌额')
    high_price = models.FloatField(verbose_name='最高价')
    low_price = models.FloatField(verbose_name='最低价')
    close = models.FloatField(verbose_name='收盘价')
    industry_group = models.CharField(max_length=80, verbose_name='细分行业')
    market_capitalization = models.FloatField(verbose_name='总市值')
    circulation_capitalization = models.FloatField(verbose_name='流通市值')
    net_profit_cut = models.FloatField(verbose_name='扣非净利润')
    total_quantity = models.FloatField(verbose_name='总量')
    quantity = models.FloatField(verbose_name='现量')
    turnover_rate = models.FloatField(verbose_name='换手率')
    change_rate_20_day = models.FloatField(verbose_name='20日涨幅')
    earning_rate_from_list = models.FloatField(verbose_name='自选收益率')
    RPS50 = models.FloatField(verbose_name='RPS50强度')
    RPS120 = models.FloatField(verbose_name='RPS120强度')
    RPS250 = models.FloatField(verbose_name='RPS250强度')
    reversal_month_line = models.BinaryField(verbose_name='月线反转')

    trade_date = models.DateField(verbose_name='交易日期', default=timezone.now())


class EvaluateStocks(models.Model):
    """股票基本面评价"""

    code = models.CharField(max_length=10, verbose_name='股票代码')

    express_diluted_roe = models.FloatField(verbose_name='业绩快报---净资产收益率')
    express_date = models.DateField(verbose_name='业绩快报日期')

    eps_rate = models.FloatField(verbose_name='基本每股收益增长率')

    front_q1_eps_rate = models.FloatField(verbose_name='前一单季度每股收益增长率')
    front_q2_eps_rate = models.FloatField(verbose_name='前二季度每股收益增长率')
    front_q3_eps_rate = models.FloatField(verbose_name='前三季度每股收益增长率')

    front_y1_eps_rate = models.FloatField(verbose_name='前一年每股收益增长率')
    front_y2_eps_rate = models.FloatField(verbose_name='前二年每股收益增长率')
    front_y3_eps_rate = models.FloatField(verbose_name='前三年每股收益增长率')
    forecast_eps_rate = models.FloatField(verbose_name='下年度预测每股收益增长率')

    front_q1_sales_rate = models.FloatField(verbose_name='前一季度销售增长率')
    front_q2_sales_rate = models.FloatField(verbose_name='前二季度销售增长率')
    front_q3_sales_rate = models.FloatField(verbose_name='前三季度销售增长率')

    roe = models.FloatField(verbose_name='股本回报率')

    q_op_qoq = models.FloatField(verbose_name='营业利润环比增长率')

    period_date = models.DateField(verbose_name='最新报告期')
    date = models.DateField(verbose_name='更新日期')

    class Meta:

        get_latest_by = 'date'  # 更新日期排序


class RelativePriceStrength(models.Model):
    """个股相对强度"""
    code = models.CharField(max_length=10, verbose_name='股票代码')
    name = models.CharField(max_length=80, verbose_name='股票名称')

    RPS_50 = models.FloatField(verbose_name='50日强度')
    RPS_120 = models.FloatField(verbose_name='120日强度')
    RPS_250 = models.FloatField(verbose_name='250日强度')
    RPS_industry_group = models.FloatField(verbose_name='行业强度')

    evaluation = models.ForeignKey(EvaluateStocks, on_delete=models.DO_NOTHING, verbose_name='基本面评价')

    date = models.DateField(verbose_name='计算日期')


class CumulativeRank(models.Model):
    """个股全市场综合排名"""
    code = models.CharField(max_length=10, verbose_name='股票代码')
    name = models.CharField(max_length=40, verbose_name=' 股票名称')

    cumulative_rank = models.FloatField(verbose_name='综合排名')
    new_quarter_eps = models.FloatField(verbose_name='最新季度EPS')
    eps = models.FloatField(verbose_name='EPS')
    rps = models.FloatField(verbose_name='RPS')
    smr = models.FloatField(verbose_name='SMR')
    eps_stability = models.FloatField(verbose_name='收益稳定性')
    roe = models.FloatField(verbose_name='年度ROE')
    decline_range = models.FloatField(verbose_name='250日降幅')
    volume_ratio = models.FloatField(verbose_name='成交量比')
    index_code = models.CharField(max_length=20, verbose_name='行业代码')
    industry_name = models.CharField(max_length=20, verbose_name='行业板块')
    industry_rps = models.FloatField(verbose_name='行业强度RPS')
    period_date = models.DateField(verbose_name='最新报告期')
    ann_date = models.DateField(verbose_name='公告日期')

    hk_hold = models.FloatField(verbose_name='港股通持仓比')
    pct_chg = models.FloatField(verbose_name='当日涨幅')

    forecast = models.CharField(max_length=40, verbose_name='预告类型')
    p_change_min = models.FloatField(verbose_name='最低限值')
    p_change_max = models.FloatField(verbose_name='最高限值')

    class Meta:
        verbose_name = '全市场综合排名'
        get_latest_by = 'ann_date'


class MonitorIndustry(models.Model):
    """行业强度监控"""

    index_code = models.CharField(max_length=20, verbose_name='行业代码')
    industry_base_rank = models.FloatField(verbose_name='年度基准排名')
    industry_base_rps = models.FloatField(verbose_name='年度基准RPS')
    industry_front_rank = models.FloatField(verbose_name='连续交易日强度排名')
    industry_front_rps = models.FloatField(verbose_name='连续交易日强度RPS')
    industry_year_rank = models.FloatField(verbose_name='年度强度排名')
    industry_year_rps = models.FloatField(verbose_name='年度强度RPS')
    industry_week_rank = models.FloatField(verbose_name='本周强度排名')
    industry_3_rank = models.FloatField(verbose_name='3周强度排名')
    industry_3_rps = models.FloatField(verbose_name='3周强度RPS')
    industry_name = models.CharField(max_length=80, verbose_name='行业名称')
    industry_6_rank = models.FloatField(verbose_name='6周强度排名')
    industry_6_rps = models.FloatField(verbose_name='6周强度RPS')
    industry_7_rank = models.FloatField(verbose_name='7个月强度排名')
    industry_7_rps = models.FloatField(verbose_name='7个月强度RPS')

    date = models.DateField(verbose_name='更新日期', default=timezone.now())
    stock_totality = models.FloatField(verbose_name='行业股票数量')
    new_high_flag = models.FloatField(verbose_name='新高数量')
    percent_7_rise = models.FloatField(verbose_name='涨幅超过7%')

    class Meta:

        verbose_name = '行业强度监控'
        get_latest_by = 'date'
