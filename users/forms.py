from django import forms
from django.contrib.auth.models import User
from captcha.fields import CaptchaField
import re


def email_check(email):
    pattern = re.compile(r"\"?([-a-zA-Z0-9.`?{}]+@\w+\.\w+)\"?")
    return re.match(pattern, email)


class RegistrationForm(forms.Form):

    username = forms.CharField(label='用户名', max_length=50)
    email = forms.EmailField(label='电子邮箱')
    password1 = forms.CharField(label='密码', widget=forms.PasswordInput)
    password2 = forms.CharField(label='密码验证', widget=forms.PasswordInput)

    username.widget.attrs.update({'style': 'width:100%', 'placeholder': '用户名'})
    email.widget.attrs.update({'style': 'width:100%', 'placeholder': '电子邮箱'})
    password1.widget.attrs.update({'style': 'width:100%', 'placeholder': '密码'})
    password2.widget.attrs.update({'style': 'width:100%', 'placeholder': '密码验证'})

    # 使用 clean类来定义用户验证规则
    def clean_username(self):
        username = self.cleaned_data.get('username')

        if len(username) < 6:
            raise forms.ValidationError("你的用户名须超过6个字符！")
        elif len(username) > 50:
            raise forms.ValidationError("你的用户名太长啦！")
        else:
            filter_result = User.objects.filter(username__exact=username)
            if len(filter_result) > 0:
                raise forms.ValidationError("你的用户名已存在！")

        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if email_check(email):
            filter_result = User.objects.filter(email__exact=email)
            if len(filter_result) > 0:
                raise forms.ValidationError("你的邮箱已存在！")
        else:
            raise forms.ValidationError("请输入有效邮箱地址！")

        return email

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')

        if len(password1) < 6:
            raise forms.ValidationError("你的密码太短啦！")
        elif len(password1) > 20:
            raise forms.ValidationError("你的密码太长啦！")

        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("密码输入不一致！请再次输入！")

        return password2


class LoginForm(forms.Form):

    username = forms.CharField(label='用户名', max_length=50)
    password = forms.CharField(label='密码', widget=forms.PasswordInput)
    captcha = CaptchaField(label='验证码')

    username.widget.attrs.update({'style': 'width:100%', 'placeholder': '用户名'})
    password.widget.attrs.update({'style': 'width:100%', 'placeholder': '密码'})
    captcha.widget.attrs.update({'style': 'width:55%'})

    # 使用 clean类来定义用户验证规则
    def clean_username(self):
        username = self.cleaned_data.get('username')

        if email_check(username):
            filter_result = User.objects.filter(email__exact=username)
            if not filter_result:
                raise forms.ValidationError("邮箱地址不存在！")
        else:
            filter_result = User.objects.filter(username__exact=username)
            if not filter_result:
                raise forms.ValidationError("用户名不存在！请注册！")

        return username
