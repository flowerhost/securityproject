"""为应用程序users定义URLS模式"""

from django.urls import path
from django.urls import include

from . import views

app_name = 'users'

urlpatterns = [
    # 登录界面
    path('', views.login, name='login'),
    path('register', views.register, name='register'),
    path('share/', views.share, name='share'),

]
