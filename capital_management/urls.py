"""定义capital_management的URL模式"""

from django.urls import path, re_path

from . import views

# 在2.1版本中必须增加的一条代码
app_name = 'capital_management'

urlpatterns = [
    # 主页
    path('index/', views.index, name='index'),
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.dashboard, name='dashboard'),
    # 券商维护
    path('broker/', views.broker, name='broker'),
    # 交易流水
    path('trade/', views.trade, name='trade'),
    # 资金账户总体情况展现
    path('account/', views.account, name='account'),
    #  系统结算功能
    path('balance/', views.balance, name='balance'),
    # 个股均线功能
    path('line/', views.line, name='line'),
    # 风险敞口
    path('capital_management/', views.capital_manage, name='capital_management'),
    # 基本面评价
    path('evaluate/', views.evaluate, name='evaluate'),
    # 行业强度监控
    path('monitor/', views.monitor, name='monitor'),
    # 行业强度详细清单
    path('monitor_detail/', views.monitor_detail, name='monitor_detail'),
    # 持仓变化细节
    path('management_detail/', views.management_detail, name='management_detail'),
]
