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

    def get_group(self, group):
        return Group.objects.get(name=group)

    def set_group(self, user, group):
        group = self.get_group(group)
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
        if str(telephone).startswith('+7'):
            telephone = str(telephone).split('+7')[1].replace('(', '').replace(')', '').replace(' ', '')
        return telephone

    @staticmethod
    def create_profile(user, telephone):
        profile = Profile.objects.create(
            user=user,
            telephone=ProfileHandler.telephone_formatter(telephone),
            is_active=True,
        )
        return profile

    @staticmethod
    def create_user(request, form, get_success_url):

        # создание пользователя
        user = form.save()
        user.first_name = form.cleaned_data.get('first_name')
        user.last_name = form.cleaned_data.get('last_name')
        group = form.cleaned_data.get('group')
        # присвоение группы для пользователя
        user.save(update_fields=['first_name', 'last_name'])
        user = GroupHandler().set_group(user=user, group=group)

        # создание расширенного профиля пользователя
        ProfileHandler().create_profile(
            user=user,
            telephone=form.cleaned_data.get('telephone'),
        )
        # SendVerificationMail.send_mail(self.request, user.email)
        identify_cart(request)
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
        user = request.user
        profile = request.user.profile
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
        # if user_form.has_changed():
        #     fields_for_update_user = []
        #     for field in user_form.changed_data:
        #         print('@@@@@@@', field)
        #         if user_form.data[field] != '' and user_form.data[field]:
        #             fields_for_update_user.append(field)
        #             user.i = user_form.data[field]
        #             user.__setattr__(field, user_form.data[field])
        #     print('++++++++ USER ', fields_for_update_user)
        #     user.save(update_fields=fields_for_update_user)
        # if profile_form.has_changed():
        #     fields_for_update_profile = []
        #     for field in profile_form.changed_data:
        #         if profile_form.data[field] != '' and profile_form.data[field]:
        #             fields_for_update_profile.append(field)
        #             profile.i = profile_form.data[field]
        #             profile.__setattr__(field, profile_form.data[field])
        #     print('++++++++ PROFILE ', fields_for_update_profile)
        #     profile.save(update_fields=fields_for_update_profile)


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
