from .models import Broker, TradeLists, CapitalAccount, TradeDailyReport
from django.forms import ModelForm


class BrokerForm(ModelForm):
    """券商表单"""
    class Meta:
        model = Broker
        fields = ['name', 'nick_name', 'rate', 'stamp_duty', 'transfer_fee', 'introduction']


class TradeListsForm(ModelForm):
    """交易流水表单"""
    class Meta:
        model = TradeLists

        fields = ['trade_resource', 'code', 'flag', 'price', 'quantity', 'date', 'account']


class CapitalAccountForm(ModelForm):
    """资金账户总体情况表单"""
    class Meta:
        model = CapitalAccount

        fields = ['name', 'broker', 'initial_capital', 'date']


class TradeDailyReportForm(ModelForm):
    """交易日报表表单"""
    class Meta:
        model = TradeDailyReport

        fields = ['name', 'code', 'cost', 'amount', 'account']

class ChartForm(ModelForm):
    """个股走势图分析"""
