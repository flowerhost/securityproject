# -*- coding: utf-8 -*-
"""
#Python 3.6
-------------------------------------------------
   Project Name:    securityproject
   File Name:       forms.py
   Description :
   Author :         flowerhost
   date:            2020/5/7          
-------------------------------------------------
   Change Activity:
                    2020/5/7:
-------------------------------------------------
"""
__author__ = 'flowerhost'

from django import forms
from .models import Article
from ckeditor_uploader.widgets import CKEditorUploadingWidget


class ArticleForm(forms.ModelForm):

    class Meta:
        model = Article
        exclude = ['author', 'views', 'slug', 'pub_date']

        widgets = dict(title=forms.TextInput(attrs={'class': 'form-control'}),
                       body=CKEditorUploadingWidget(attrs={'class': 'form-control'}),
                       status=forms.Select(attrs={'class': 'form-control'}),
                       category=forms.Select(attrs={'class': 'form-control'}),
                       tags=forms.CheckboxSelectMultiple(attrs={'class': 'multi-checkbox'}))
