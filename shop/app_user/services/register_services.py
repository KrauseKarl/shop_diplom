import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User, Group
from django.contrib.sites.shortcuts import get_current_site

from app_cart.services.cart_services import identify_cart, delete_cart_cookies

from app_user.models import Profile


class GroupHandler:

    def get_group(self):
        return Group.objects.get(name='unverified')

    def set_group(self, user):
        group = self.get_group()
        user.groups.add(group)
        user.save()
        return user


class RoleHandler:
    @classmethod
    def get_seller_permission(cls, profile):
        profile = Profile.objects.filter(id=profile).first()
        profile.role = 'SLR'
        profile.save()

        return profile


class ProfileHandler:
    @staticmethod
    def telephone_formatter(telephone):
        telephone = str(telephone).split('7')[1].replace('(', '').replace(')', '').replace(' ', '')
        return telephone

    @staticmethod
    def create_profile(user, telephone, role=None):
        profile = Profile.objects.create(
            user=user,
            telephone=ProfileHandler.telephone_formatter(telephone),
        )
        if role:
            profile = RoleHandler.get_seller_permission(profile.id)
        return profile

    @staticmethod
    def create_user(request, form, get_success_url):

        # создание пользователя
        user = form.save(commit=False)
        user.first_name = form.cleaned_data.get('first_name')
        user.last_name = form.cleaned_data.get('last_name')
        user.save()
        # присвоение группы для пользователя
        GroupHandler().set_group(user=user)
        # создание расширенного профиля пользователя
        ProfileHandler().create_profile(
            user=user,
            telephone=form.cleaned_data.get('telephone'),
            role=form.cleaned_data.get('role'),
        )
        # SendVerificationMail.send_mail(self.request, user.email)
        identify_cart(request, user)
        user = authenticate(
            request,
            username=form.cleaned_data.get('username'),
            password=form.cleaned_data.get('password1')
        )
        login(request, user)
        if request.GET.get('next'):
            path = request.GET.get('next')
        else:
            path = get_success_url()
        response = delete_cart_cookies(request, path)
        return response

    @staticmethod
    def update_profile(request):
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
        profile = profile_form.save(commit=False)
        telephone = profile_form.cleaned_data['telephone']
        telephone = ProfileHandler.telephone_formatter(telephone)
        profile.telephone = telephone
        profile.save()


class SendVerificationMail:
    @staticmethod
    def _get_current_site(request):
        return get_current_site(request).domain

    @staticmethod
    def send_mail(request, user_email):
        domain = SendVerificationMail._get_current_site(request)
        login = os.environ.get('FROM_MAIL')
        password = os.environ.get('PASSWORD')
        code = f'<p> Ваша учетная запись на сайте {domain} успешно создана.</p>'
        user_email = user_email

        try:
            msg = MIMEMultipart()
            msg['subject'] = 'Verification code'
            msg['from'] = login
            msg['to'] = user_email
            msg.attach(MIMEText(code, 'plain', 'utf-8'))

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(login, password)
                smtp.send_message(msg)
                smtp.quit()
        except Exception as e:
            print(e)
