from django.db import models
from django.contrib.auth.models import User


# Create your models here.
from django.utils.html import format_html


class Broker(models.Model):
    """券商列表"""
    name = models.CharField(max_length=80, verbose_name='证券公司')
    nick_name = models.CharField(max_length=80, unique=True, verbose_name='昵称')

    rate = models.FloatField(verbose_name='券商佣金')
    stamp_duty = models.FloatField(verbose_name='印花税费')
    transfer_fee = models.FloatField(verbose_name='过户费')

    date_added = models.DateTimeField(auto_now_add=True, verbose_name='注册时间')
    introduction = models.TextField(verbose_name='简介')

    def __str__(self):
        """返回模型的券商名"""
        return self.nick_name

    class Meta:
        verbose_name = '证券公司'
        verbose_name_plural = '证券公司'


class CapitalAccount(models.Model):
    """证券资金账户"""

    # name = models.CharField(max_length=80, unique=True, verbose_name='账户名称')
    broker = models.ForeignKey(Broker, on_delete=models.CASCADE, verbose_name='证券公司')

    total_assets = models.FloatField(verbose_name='总资产')
    market_capital = models.FloatField(verbose_name='总市值')
    fund_balance = models.FloatField(verbose_name='资金余额')
    position_gain_loss = models.FloatField(verbose_name='浮动盈亏')
    initial_capital = models.FloatField(verbose_name='期初资产')

    date = models.DateField(verbose_name='记账日')

    class Meta:
        verbose_name = '券资金账户'
        verbose_name_plural = '证券资金账户'

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
    )
    flag = models.CharField(max_length=20, verbose_name='操作方向', choices=OPERATION_CHOICE)

    price = models.FloatField(verbose_name='买卖价格')
    quantity = models.IntegerField(verbose_name='买卖数量')
    transaction_date = models.DateField(verbose_name='交易日期')
    brokerage = models.FloatField(verbose_name='交易佣金')
    stamp_duty = models.FloatField(verbose_name='印花税')
    transfer_fee = models.FloatField(verbose_name='过户费')
    total_fee = models.FloatField(verbose_name='手续费用')
    total_capital = models.FloatField(verbose_name='交易总额')

    clear_flag = models.CharField(max_length=100, verbose_name='清仓标识---清仓股票表_ID')

    account = models.ForeignKey(CapitalAccount, on_delete=models.CASCADE, verbose_name='交易账户')

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

    # 设置后台管理的时间格式：2019年9月23日 而不是2019年9月23日 20：33
    def transact_date(self):
        return self.transaction_date.strftime('%Y年%m月%d日')

    transact_date.short_description = u'交易日期'
    transact_date.admin_order_field = '-transaction_date'

    class Meta:
        verbose_name = '股票交易记录'
        verbose_name_plural = '股票交易记录'

    def __str__(self):
        return self.name


class Positions(models.Model):
    """持仓情况表"""

    name = models.CharField(max_length=20, verbose_name='股票名称')
    code = models.CharField(max_length=10, verbose_name='股票代码')

    date = models.DateTimeField(verbose_name='结算日期')

    cost = models.FloatField(verbose_name='成本价')
    amount = models.FloatField(verbose_name='持股数量')
    market_value = models.FloatField(verbose_name='股票市值')
    gain_loss = models.FloatField(verbose_name='浮动盈亏')
    account = models.ForeignKey(CapitalAccount, on_delete=models.CASCADE, verbose_name='证券账户')
    update_flag = models.BooleanField(verbose_name='数据更新标志')

    class Meta:
        verbose_name = '股票持仓情况'
        verbose_name_plural = '股票持仓情况'


class Clearance(models.Model):
    """清仓股票情况表"""

    name = models.CharField(max_length=80, verbose_name='股票名称')
    code = models.CharField(max_length=10, verbose_name='股票代码')

    open_date = models.DateTimeField(verbose_name='建仓日期')
    clear_date = models.DateTimeField(verbose_name='清仓日期')

    invest_capital = models.FloatField(verbose_name='累计投入金额')
    accumulate_capital = models.FloatField(verbose_name='累计收入金额')

    fee = models.FloatField(verbose_name='交易费用')
    profit = models.FloatField(verbose_name='盈亏金额')

    account = models.ForeignKey(CapitalAccount, on_delete=models.CASCADE, verbose_name='证券账户')

    class Meta:
        verbose_name = '清仓股票情况'
        verbose_name_plural = '清仓股票情况'


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

    account = models.ForeignKey(CapitalAccount, on_delete=models.CASCADE,
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


class MyStockLists(models.Model):
    """自选股"""

    code = models.CharField(max_length=10, verbose_name='股票代码')
    name = models.CharField(max_length=80, verbose_name='股票名称')

    change_rate = models.FloatField(verbose_name='涨跌幅度')
    price = models.FloatField(verbose_name='现价')
    change_amount = models.FloatField(verbose_name='涨跌额')
    buy = models.FloatField(verbose_name='买价')
    sell = models.FloatField(verbose_name='卖价')
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

    trade_date = models.DateField(verbose_name='交易日期')


class StockBasis(models.Model):
    """股票基本情况"""
    name = models.CharField(max_length=80, verbose_name='股票名称')
    code = models.CharField(max_length=10, verbose_name='股票代码')

    industry_group = models.CharField(max_length=80, verbose_name='所属行业')
    is_HS = models.CharField(max_length=10, verbose_name='沪深通标的')
    area = models.CharField(max_length=20, verbose_name='地区')

    market = models.CharField(max_length=20, verbose_name='市场类型')
    exchange = models.CharField(max_length=20, verbose_name='交易所代码')
