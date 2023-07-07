import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import Group
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse

from app_cart.services import cart_services

from app_user.models import Profile

"""
    Сервисы работы с группами, созданием и редактированием пользователя и верификаии профиля

    #1 GroupHandler - класс для работы с группами пользователей.
    #2 ProfileHandler - класс для работы с профилем пользователя.
    #3 SendVerificationMail - класс для верификации пользователя. Отправка письма.

"""


class GroupHandler:
    """ Класс для работы с группами пользователей."""

    @staticmethod
    def get_group(group):
        """ Функция возвращет экземпляр группы по имени групп."""
        return Group.objects.get(name=group)

    @staticmethod
    def set_group(user, group):
        """ Функция добавляет пользователя в группу."""
        group = GroupHandler().get_group(group)
        user.groups.add(group)
        user.save()
        return user


class ProfileHandler:
    """ Класс для работы с профилем пользователя."""

    @staticmethod
    def create_user(request, form):
        """ Функция создает пользователя."""
        # создание пользователя
        user = form.save()
        user.first_name = form.cleaned_data.get('first_name')
        user.last_name = form.cleaned_data.get('last_name')
        group = form.cleaned_data.get('group')
        # присвоение группы для пользователя
        user.save(update_fields=['first_name', 'last_name'])

        GroupHandler().set_group(user=user, group=group)

        # создание расширенного профиля пользователя
        ProfileHandler().create_profile(
            user=user,
            telephone=form.cleaned_data.get('telephone'),
        )
        # SendVerificationMail.send_mail(self.request, user.email)
        cart_services.identify_cart(request)
        user = authenticate(
            request,
            username=form.cleaned_data.get('username'),
            password=form.cleaned_data.get('password1')
        )
        login(request, user)
        next_page = request.GET.get('next')
        if next_page:
            path = next_page
        else:
            path = reverse('app_user:account', kwargs={'pk': user.pk})
        # удаление данных об анонимной корзине из COOKIES  при создании нового пользователя
        response = cart_services.delete_cart_cookies(request, path)
        return response

    @staticmethod
    def create_profile(user, telephone):
        """ Функция создает расширенный профиль пользователя."""
        profile = Profile.objects.create(
            user=user,
            telephone=ProfileHandler.telephone_formatter(telephone),
            is_active=True,
        )
        return profile

    @staticmethod
    def telephone_formatter(telephone):
        """ Функция форматирует номер телефона (оставляет только цифры)."""
        if str(telephone).startswith('+7'):
            telephone = str(telephone).split('+7')[1].replace('(', '').replace(')', '').replace(' ', '')
        return telephone

    @staticmethod
    def update_profile(request):
        """ Функция обновляет базовый и расширенный профиль пользователя."""
        from app_user.forms import UpdateProfileForm, UpdateUserForm

        user_form = UpdateUserForm(
            data=request.POST,
            instance=request.user
        )
        profile_form = UpdateProfileForm(
            data=request.POST,
            files=request.FILES,
            instance=request.user.profile
        )
        user_form.save()
        profile_form.save()


class SendVerificationMail:
    """ Класс для верификации пользователя. Отправка письма."""
    @staticmethod
    def get_current_site(request):
        """ Функция возвращет доменное имя сайта."""
        return get_current_site(request).domain

    @staticmethod
    def send_mail(request, email):
        """ Функция отправляет письмо для верификации профиля."""
        domain = SendVerificationMail.get_current_site(request)
        username = os.environ.get('FROM_MAIL')
        password = os.environ.get('PASSWORD')
        code = f'<p> Ваша учетная запись на сайте {domain} успешно создана.</p>'
        user_email = email

        try:
            msg = MIMEMultipart()
            msg['subject'] = 'Verification code'
            msg['from'] = username
            msg['to'] = user_email
            msg.attach(MIMEText(code, 'plain', 'utf-8'))

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(username, password)
                smtp.send_message(msg)
                smtp.quit()
        except Exception as e:
            print(e)
