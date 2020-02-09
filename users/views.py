from django.shortcuts import render
from django.contrib import auth
from django.contrib.auth.models import User

from .forms import LoginForm, RegistrationForm


def login(request):
    if request.method == "POST":
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            username = login_form.cleaned_data['username']
            password = login_form.cleaned_data['password']

            user = auth.authenticate(username=username, password=password)

            if user is not None and user.is_active:
                auth.login(request, user)
                return render(request, 'capital_management/index.html')

            else:
                return render(request, 'users/login.html', {'login_form': login_form, 'message': '密码错误！请重新输入。'})

    else:
        login_form = LoginForm()

    return render(request, 'users/login.html', {'login_form': login_form})


def register(request):
    if request.method == 'POST':
        register_form = RegistrationForm(request.POST)
        if register_form.is_valid():
            username = register_form.cleaned_data['username']
            email = register_form.cleaned_data['email']
            password = register_form.cleaned_data['password2']

            User.objects.create_user(username=username, password=password, email=email)

            # user profile表的操作
            # user_profile = UserProfile(user=user)
            # user_profile.save()

            return render(request, 'users/share.html', {'register_form': register_form})
    else:
        register_form = RegistrationForm()

    return render(request, 'users/register.html', {'register_form': register_form})


def share(request):
    return render(request, 'users/share.html')
