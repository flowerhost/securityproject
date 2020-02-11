from .models import Broker, TradeLists, CapitalAccount, Positions
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

        fields = ['code', 'flag', 'price', 'quantity', 'transaction_date', 'account']


class AccountForm(ModelForm):
    """资金账户总体情况表单"""
    class Meta:
        model = CapitalAccount

        fields = ['total_assets', 'market_capital', 'fund_balance', 'position_gain_loss', 'initial_capital']

class PositionsForm(ModelForm):
    """持仓情况表单"""
    class Meta:
        model  = Positions

        fields = ['name', 'code', 'cost', 'amount', 'market_value', 'gain_loss', 'account']