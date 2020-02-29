# Generated by Django 2.1.4 on 2020-02-29 11:51

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AccountSurplus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_assets', models.FloatField(verbose_name='总资产')),
                ('market_capital', models.FloatField(verbose_name='总市值')),
                ('fund_balance', models.FloatField(verbose_name='资金余额')),
                ('position_gain_loss', models.FloatField(verbose_name='浮动盈亏')),
                ('total_fee', models.FloatField(verbose_name='总费用')),
                ('final_cost', models.FloatField(verbose_name='总投入')),
                ('initial_capital', models.FloatField(verbose_name='期初资产')),
                ('update_flag', models.BooleanField(verbose_name='数据更新标识')),
                ('date', models.DateField(default=datetime.datetime(2020, 2, 29, 11, 51, 10, 976443), verbose_name='结算日期')),
            ],
            options={
                'verbose_name': '账户盈余表',
                'verbose_name_plural': '账户盈余表',
                'get_latest_by': 'date',
            },
        ),
        migrations.CreateModel(
            name='Broker',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, verbose_name='证券公司')),
                ('nick_name', models.CharField(max_length=80, unique=True, verbose_name='昵称')),
                ('rate', models.FloatField(verbose_name='券商佣金')),
                ('stamp_duty', models.FloatField(verbose_name='印花税费')),
                ('transfer_fee', models.FloatField(verbose_name='过户费')),
                ('date_added', models.DateField(auto_now_add=True, verbose_name='注册时间')),
                ('introduction', models.TextField(verbose_name='简介')),
            ],
            options={
                'verbose_name': '证券公司',
                'verbose_name_plural': '证券公司',
                'get_latest_by': 'date_added',
            },
        ),
        migrations.CreateModel(
            name='CapitalAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, verbose_name='账户名称')),
                ('initial_capital', models.FloatField(verbose_name='期初资产')),
                ('date', models.DateField(default=datetime.datetime(2020, 2, 29, 11, 51, 10, 975943), verbose_name='创建日期')),
                ('broker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='capital_management.Broker', verbose_name='证券公司')),
            ],
            options={
                'verbose_name': '证券资金账户',
                'verbose_name_plural': '证券资金账户',
                'get_latest_by': 'date',
            },
        ),
        migrations.CreateModel(
            name='CapitalManagement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assets_6', models.FloatField(verbose_name='总资产')),
                ('stock_name', models.CharField(max_length=80, verbose_name=' 交易标的物')),
                ('stop_loss', models.FloatField(verbose_name=' 止损点')),
                ('buy', models.FloatField(verbose_name='买入价')),
                ('max_volume', models.FloatField(verbose_name='可买股数')),
                ('date', models.DateField(verbose_name='建仓日期')),
            ],
            options={
                'verbose_name': '仓位管理',
                'verbose_name_plural': ' 仓位管理',
                'get_latest_by': 'date',
            },
        ),
        migrations.CreateModel(
            name='Clearance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, verbose_name='股票名称')),
                ('code', models.CharField(max_length=10, verbose_name='股票代码')),
                ('open_date', models.DateField(verbose_name='建仓日期')),
                ('clear_date', models.DateField(verbose_name='清仓日期')),
                ('invest_capital', models.FloatField(verbose_name='累计投入金额')),
                ('fee', models.FloatField(verbose_name='交易费用')),
                ('profit', models.FloatField(verbose_name='盈亏金额')),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='capital_management.CapitalAccount', verbose_name='证券账户')),
            ],
            options={
                'verbose_name': '清仓股票情况',
                'verbose_name_plural': '清仓股票情况',
            },
        ),
        migrations.CreateModel(
            name='EventLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, verbose_name='事件名')),
                ('event_type', models.CharField(choices=[(0, '其他'), (1, '股票买卖'), (2, '证券账户维护')], default=1, max_length=40, verbose_name='事件类型')),
                ('detail', models.TextField(verbose_name='事件详情')),
                ('memo', models.TextField(blank=True, null=True, verbose_name='备注')),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='capital_management.CapitalAccount', verbose_name='资金账户变化')),
            ],
            options={
                'verbose_name': '事件日志',
                'verbose_name_plural': '事件日志',
            },
        ),
        migrations.CreateModel(
            name='MarketQuotation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, verbose_name='股票名称')),
                ('code', models.CharField(max_length=10, verbose_name='股票代码')),
                ('open', models.FloatField(verbose_name='开盘价')),
                ('close', models.FloatField(verbose_name='收盘价')),
                ('high', models.FloatField(verbose_name='最高价')),
                ('low', models.FloatField(verbose_name='最低价')),
                ('volume', models.FloatField(verbose_name='成交数量')),
                ('value', models.FloatField(verbose_name='成交金额')),
                ('date', models.DateField(verbose_name='交易日期')),
            ],
            options={
                'verbose_name': '行情记录',
                'verbose_name_plural': '行情记录',
            },
        ),
        migrations.CreateModel(
            name='MyStockLists',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=10, verbose_name='股票代码')),
                ('name', models.CharField(max_length=80, verbose_name='股票名称')),
                ('change_rate', models.FloatField(verbose_name='涨跌幅度')),
                ('price', models.FloatField(verbose_name='现价')),
                ('change_amount', models.FloatField(verbose_name='涨跌额')),
                ('buy', models.FloatField(verbose_name='买价')),
                ('sell', models.FloatField(verbose_name='卖价')),
                ('close', models.FloatField(verbose_name='收盘价')),
                ('industry_group', models.CharField(max_length=80, verbose_name='细分行业')),
                ('market_capitalization', models.FloatField(verbose_name='总市值')),
                ('circulation_capitalization', models.FloatField(verbose_name='流通市值')),
                ('net_profit_cut', models.FloatField(verbose_name='扣非净利润')),
                ('total_quantity', models.FloatField(verbose_name='总量')),
                ('quantity', models.FloatField(verbose_name='现量')),
                ('turnover_rate', models.FloatField(verbose_name='换手率')),
                ('change_rate_20_day', models.FloatField(verbose_name='20日涨幅')),
                ('earning_rate_from_list', models.FloatField(verbose_name='自选收益率')),
                ('RPS50', models.FloatField(verbose_name='RPS50强度')),
                ('RPS120', models.FloatField(verbose_name='RPS120强度')),
                ('RPS250', models.FloatField(verbose_name='RPS250强度')),
                ('reversal_month_line', models.BinaryField(verbose_name='月线反转')),
                ('trade_date', models.DateField(default=datetime.datetime(2020, 2, 29, 11, 51, 10, 981922), verbose_name='交易日期')),
            ],
        ),
        migrations.CreateModel(
            name='Positions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=10, verbose_name='股票代码')),
                ('name', models.CharField(max_length=80, verbose_name='股票名称')),
                ('cost', models.FloatField(verbose_name='每股成本')),
                ('amount', models.FloatField(verbose_name='股票数量')),
                ('fee', models.FloatField(verbose_name=' 费用')),
                ('gain_loss', models.FloatField(verbose_name='浮动盈亏')),
                ('final_cost', models.FloatField(verbose_name='总投入')),
                ('market_capital', models.FloatField(verbose_name='市值')),
                ('open_date', models.DateField(verbose_name=' 建仓日期')),
                ('date', models.DateField(default=datetime.datetime(2020, 2, 29, 11, 51, 10, 979308), verbose_name='结算日起')),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='capital_management.CapitalAccount', verbose_name='资金账号')),
            ],
            options={
                'get_latest_by': 'date',
            },
        ),
        migrations.CreateModel(
            name='StockBasis',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, verbose_name='股票名称')),
                ('code', models.CharField(max_length=10, verbose_name='股票代码')),
                ('industry_group', models.CharField(max_length=80, verbose_name='所属行业')),
                ('is_HS', models.CharField(max_length=10, verbose_name='沪深通标的')),
                ('area', models.CharField(max_length=20, verbose_name='地区')),
                ('market', models.CharField(max_length=20, verbose_name='市场类型')),
                ('exchange', models.CharField(max_length=20, verbose_name='交易所代码')),
            ],
        ),
        migrations.CreateModel(
            name='TradeDailyReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, verbose_name='股票名称')),
                ('code', models.CharField(max_length=10, verbose_name='股票代码')),
                ('cost', models.FloatField(verbose_name='成本价')),
                ('amount', models.FloatField(verbose_name='买卖股数')),
                ('total_capital', models.FloatField(verbose_name='交易总额')),
                ('total_fee', models.FloatField(verbose_name='手续费')),
                ('date', models.DateField(default=datetime.datetime(2020, 2, 29, 11, 51, 10, 978709), verbose_name='结算日期')),
                ('update_flag', models.BooleanField(verbose_name='数据更新标志')),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='capital_management.CapitalAccount', verbose_name='证券账户')),
            ],
            options={
                'verbose_name': '股票持仓情况',
                'verbose_name_plural': '股票持仓情况',
                'get_latest_by': 'date',
            },
        ),
        migrations.CreateModel(
            name='TradeLists',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, verbose_name='股票名称')),
                ('code', models.CharField(max_length=10, verbose_name='股票代码')),
                ('flag', models.CharField(choices=[('B', '普通买入'), ('S', '普通卖出'), ('R', '融资买入'), ('T', '融券卖出')], max_length=20, verbose_name='操作方向')),
                ('price', models.FloatField(verbose_name='买卖价格')),
                ('quantity', models.IntegerField(verbose_name='买卖数量')),
                ('date', models.DateField(default=datetime.datetime(2020, 2, 29, 11, 51, 10, 977407), verbose_name='交易日期')),
                ('brokerage', models.FloatField(verbose_name='交易佣金')),
                ('stamp_duty', models.FloatField(verbose_name='印花税')),
                ('transfer_fee', models.FloatField(verbose_name='过户费')),
                ('total_fee', models.FloatField(verbose_name='手续费用')),
                ('total_capital', models.FloatField(verbose_name='交易总额')),
                ('clear_flag', models.CharField(max_length=100, verbose_name='清仓标识---清仓股票表_ID')),
                ('trade_resource', models.CharField(max_length=80, verbose_name='信息源头')),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='capital_management.CapitalAccount', verbose_name='交易账户')),
            ],
            options={
                'verbose_name': '股票交易记录',
                'verbose_name_plural': '股票交易记录',
                'get_latest_by': 'date',
            },
        ),
        migrations.CreateModel(
            name='TradePerformance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('close', models.FloatField(verbose_name='收盘价')),
                ('moving_average', models.FloatField(verbose_name='十日均线')),
                ('high_price', models.FloatField(verbose_name='最高价')),
                ('low_price', models.FloatField(verbose_name='最低价')),
                ('boll_up', models.FloatField(verbose_name='BOLL线上轨')),
                ('boo_down', models.FloatField(verbose_name='BOLL线下轨')),
                ('performance', models.FloatField(verbose_name='买卖评价')),
                ('trade_performance', models.FloatField(verbose_name='总体评价')),
                ('date', models.DateField(default=datetime.datetime(2020, 2, 29, 11, 51, 10, 978178), verbose_name='评价日期')),
                ('trade', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='capital_management.TradeLists', verbose_name='交易记录')),
            ],
            options={
                'verbose_name': '交易表现评价',
                'verbose_name_plural': '交易表现评价',
                'get_latest_by': 'date',
            },
        ),
        migrations.AddField(
            model_name='eventlog',
            name='trade_details',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='capital_management.TradeLists', verbose_name='股票买卖变化'),
        ),
        migrations.AddField(
            model_name='accountsurplus',
            name='account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='capital_management.CapitalAccount', verbose_name='账户名称'),
        ),
    ]
