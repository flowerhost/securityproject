"""定义capital_management的URL模式"""

from django.urls import path

from . import views

# 在2.1版本中必须增加的一条代码
app_name = 'capital_management'

urlpatterns = [
    # 主页
    path('index/', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.dashboard, name='dashboard'),


    # 更新所有的数据表
    path('prepare_data/', views.prepare_data, name='prepare_data'),
]
