# Create your views here.

from django.shortcuts import render
from .models import Broker, CapitalAccount, StockDetails, Positions, Clearance, EventLog

from django.db.models import F

from django.shortcuts import HttpResponse


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

