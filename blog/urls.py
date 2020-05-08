# -*- coding: utf-8 -*-
"""
#Python 3.6
-------------------------------------------------
   Project Name:    securityproject
   File Name:       urls.py
   Description :
   Author :         flowerhost
   date:            2020/5/6          
-------------------------------------------------
   Change Activity:
                    2020/5/6:
-------------------------------------------------
"""
__author__ = 'flowerhost'

"""定义blog的URL模式"""

from django.urls import path, re_path

from . import views

# 在2.1版本中必须增加的一条代码
app_name = 'blog'

urlpatterns = [
    # 所有文章列表
    path('', views.ArticleListView.as_view(), name='article_list'),
    # 展示文章详情
    re_path(r'^article/(?P<pk>\d+)/(?P<slug1>[-\w]+)/$', views.ArticleDetailView.as_view(), name='article_detail'),
    # 草稿箱
    path('draft/', views.ArticleDraftListView.as_view(), name='article_draft_list'),
    # 已发表文章列表（含编辑）
    path('published/', views.PublishedArticleListView.as_view(), name='published_article_list'),
    # 更新文章
    re_path(r'^article/(?P<pk>\d+)/(?P<slug1>[-\w]+)/update/$', views.ArticleUpdateView.as_view(),
            name='article_update'),
    # 创建文章
    re_path(r'^article/create/$', views.ArticleCreateView.as_view(), name='article_create'),
    # 发表文章
    re_path(r'^article/(?P<pk>\d+)/(?P<slug1>[-\w]+)/publish/$', views.article_publish, name='article_publish'),
    #  删除文章
    re_path(r'^article/(?P<pk>\d+)/(?P<slug1>[-\w]+)/delete$', views.ArticleDeleteView.as_view(),
            name='article_delete'),

    # 展示类别详情
    re_path(r'^category/(?P<slug>[-\w]+)/$',
            views.CategoryDetailView.as_view(), name='category_detail'),

]
