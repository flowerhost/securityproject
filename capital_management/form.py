from .models import Broker, StockDetails
from django.forms import ModelForm


class BrokerForm(ModelForm):
    """券商表单"""
    class Meta:
        model = Broker
        fields = ['name', 'rate', 'stamp_duty', 'transfer_fee', 'introduction']


class StockDetailsForm(ModelForm):
    """交易流水"""
    class Meta:
        model = StockDetails

        fields = ['name', 'code', 'flag', 'price', 'quantity', 'transaction_date', 'brokerage', 'stamp_duty',
                  'transfer_fee', 'total_capital', 'account']
