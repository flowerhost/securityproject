from django.shortcuts import render
from django.contrib import auth
from django.contrib.auth.models import User

from .forms import LoginForm, RegistrationForm

def login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = auth.authenticate(username=username, password=password)

            if user is not None and user.is_active:
                auth.login(request, user)
                return render(request, 'capital_management/index.html')

            else:
                return render(request, 'users/login.html', {'form': form, 'message': '密码错误！请重新输入。'})

    else:
        form = LoginForm()

    return render(request, 'users/login.html', {'form': form})


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password2']

            user = User.objects.create_user(username=username, password=password, email=email)

            # userprofile表的操作
            #user_profile = UserProfile(user=user)
            #user_profile.save()

            return render(request, 'users/share.html', {'form': form})
    else:
        form = RegistrationForm()

    return render(request, 'users/register.html', {'form': form})


def share(request):
    return render(request, 'users/share.html')
