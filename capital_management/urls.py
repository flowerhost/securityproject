"""定义capital_management的URL模式"""

from django.urls import path

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
    # TODO: 扩展账户结算功能
    # 更新所有的数据表
    path('prepare_data/', views.prepare_data, name='prepare_data'),
]
