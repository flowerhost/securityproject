# Generated by Django 2.1.4 on 2020-02-09 16:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Broker',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, verbose_name='证券公司')),
                ('nick_name', models.CharField(max_length=80, unique=True, verbose_name='昵称')),
                ('rate', models.FloatField(verbose_name='券商佣金')),
                ('stamp_duty', models.FloatField(verbose_name='印花税费')),
                ('transfer_fee', models.FloatField(verbose_name='过户费')),
                ('date_added', models.DateTimeField(auto_now_add=True, verbose_name='注册时间')),
                ('introduction', models.TextField(verbose_name='简介')),
            ],
            options={
                'verbose_name': '证券公司',
                'verbose_name_plural': '证券公司',
            },
        ),
        migrations.CreateModel(
            name='CapitalAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_assets', models.FloatField(verbose_name='总资产')),
                ('market_capital', models.FloatField(verbose_name='总市值')),
                ('fund_balance', models.FloatField(verbose_name='资金余额')),
                ('position_gain_loss', models.FloatField(verbose_name='浮动盈亏')),
                ('initial_capital', models.FloatField(verbose_name='期初资产')),
                ('date', models.DateField(verbose_name='记账日')),
                ('broker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='capital_management.Broker', verbose_name='证券公司')),
            ],
            options={
                'verbose_name': '券资金账户',
                'verbose_name_plural': '证券资金账户',
            },
        ),
        migrations.CreateModel(
            name='Clearance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, verbose_name='股票名称')),
                ('code', models.CharField(max_length=10, verbose_name='股票代码')),
                ('open_date', models.DateTimeField(verbose_name='建仓日期')),
                ('clear_date', models.DateTimeField(verbose_name='清仓日期')),
                ('invest_capital', models.FloatField(verbose_name='累计投入金额')),
                ('accumulate_capital', models.FloatField(verbose_name='累计收入金额')),
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
                ('trade_date', models.DateField(verbose_name='交易日期')),
            ],
        ),
        migrations.CreateModel(
            name='Positions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, verbose_name='股票名称')),
                ('code', models.CharField(max_length=10, verbose_name='股票代码')),
                ('date', models.DateTimeField(verbose_name='结算日期')),
                ('cost', models.FloatField(verbose_name='成本价')),
                ('amount', models.FloatField(verbose_name='持股数量')),
                ('update_flag', models.BooleanField(verbose_name='数据更新标志')),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='capital_management.CapitalAccount', verbose_name='证券账户')),
            ],
            options={
                'verbose_name': '股票持仓情况',
                'verbose_name_plural': '股票持仓情况',
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
            name='TradeLists',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, verbose_name='股票名称')),
                ('code', models.CharField(max_length=10, verbose_name='股票代码')),
                ('flag', models.CharField(choices=[('B', '普通买入'), ('S', '普通卖出'), ('R', '融资买入'), ('T', '融券卖出')], max_length=20, verbose_name='操作方向')),
                ('price', models.FloatField(verbose_name='买卖价格')),
                ('quantity', models.IntegerField(verbose_name='买卖数量')),
                ('transaction_date', models.DateField(verbose_name='交易日期')),
                ('brokerage', models.FloatField(verbose_name='交易佣金')),
                ('stamp_duty', models.FloatField(verbose_name='印花税')),
                ('transfer_fee', models.FloatField(verbose_name='过户费')),
                ('total_fee', models.FloatField(verbose_name='手续费用')),
                ('total_capital', models.FloatField(verbose_name='交易总额')),
                ('clear_flag', models.CharField(max_length=100, verbose_name='清仓标识---清仓股票表_ID')),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='capital_management.CapitalAccount', verbose_name='交易账户')),
            ],
            options={
                'verbose_name': '股票交易记录',
                'verbose_name_plural': '股票交易记录',
            },
        ),
        migrations.AddField(
            model_name='eventlog',
            name='trade_details',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='capital_management.TradeLists', verbose_name='股票买卖变化'),
        ),
    ]
