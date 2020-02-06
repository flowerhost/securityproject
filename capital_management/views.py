# Create your views here.

from django.shortcuts import render, redirect
from .models import StockDetails
from .form import BrokerForm, StockDetailsForm


def index(request):
    stocks = StockDetails.objects.all()
    return render(request, 'capital_management/index.html', locals())


def dashboard(request):
    pass
    return render(request, 'capital_management/dashboard.html', locals())


def prepare_data(request):
    """
        更新所有收盘后的数据表：
           1、持股数据表:      Positions(models.Model)
           2、清仓数据表:      Clearance(models.Model)
           3、账户资产管理:    CapitalAccount(models.Model)
        :param request:
        :return:
    """
    #  首先判断:"持股数据表---Positions"的update_flag字段是否为true？如果是，则判断为数据已经更新过，否则进行更新！


def broker(request):
    if request.method != 'POST':
        broker_form = BrokerForm()
    else:
        broker_form = BrokerForm(request.POST)
        if broker_form.is_valid():
            broker_form.save()
            return redirect('capital_management:index')

    context = {'broker_form': broker_form}
    return render(request, 'capital_management/broker.html', context)

def addstock(request):
    if request.method != 'POST':
        add_stock_form = StockDetailsForm()
    else:
        add_stock_form = StockDetailsForm(request.POST)
        if add_stock_form.is_valid():
            add_stock_form.save()
            return redirect('capital_management:index')

    context = {'add_stock_form': add_stock_form}
    return render(request, 'capital_management/addstock.html', context)
