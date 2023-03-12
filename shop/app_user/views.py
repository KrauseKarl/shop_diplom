import logging

from urllib.parse import quote
from django.contrib import messages
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordChangeView, \
    PasswordChangeDoneView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView, TemplateView, ListView
from django.contrib.auth.models import User, Group

from app_item.services.item_services import ItemHandler

from app_user.services.user_services import is_customer
from utils.my_utils import MixinPaginator
from app_cart.models import Cart
from app_cart.services.cart_services import get_current_cart, merge_anon_cart_with_user_cart, delete_cart_cookies, \
    get_items_in_cart
from app_item.models import Comment
from app_item.services.comment_services import CommentHandler
from app_user.forms import RegisterUserForm, UpdateUserForm, UpdateProfileForm, RegisterUserFormFromOrder
from app_user.models import Profile
from app_user.services.register_services import SendVerificationMail, GroupHandler, ProfileHandler


# CREATE & UPDATE PROFILE #
class CreateProfile(SuccessMessageMixin, CreateView):
    """Класс-представление для создания профиля пользователя."""
    model = User
    second_model = Profile
    template_name = 'registrations/register.html'
    form_class = RegisterUserForm

    def get_success_url(self):
        return reverse('app_user:account', kwargs={'pk': self.request.user.pk})

    def form_valid(self, form):
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

        if is_customer(user):
            if self.request.session.session_key:
                session_key = self.request.session.session_key
                cart = Cart.objects.filter(session_key=session_key).first()
                if cart:
                    cart.session_key = ''
                    cart.is_anonymous = False
                    cart.user = user
                    for cart_item in cart.items.all():
                        cart_item.user = user
                        cart_item.save()
                    cart.save()
        user = authenticate(
            self.request,
            username=form.cleaned_data.get('username'),
            password=form.cleaned_data.get('password1')
        )
        login(self.request, user)
        if self.request.GET.get('next'):
            path = self.request.GET.get('next')
        else:
            path = self.get_success_url()
        response = delete_cart_cookies(self.request, path)
        return response

    def form_invalid(self, form):
        form = RegisterUserForm(self.request.POST)
        return super(CreateProfile, self).form_invalid(form)


class UpdateProfile(UpdateView):
    """Класс-представление для обновления профиля пользователя."""
    model = User
    second_model = Profile
    template_name = 'app_user/profile_edit.html'
    form_class = UpdateUserForm
    second_form_class = UpdateProfileForm

    def form_valid(self, form):
        user_form = UpdateUserForm(
            data=self.request.POST,
            instance=self.request.user
        )
        profile_form = UpdateProfileForm(
            data=self.request.POST,
            files=self.request.FILES,
            instance=self.request.user.profile
        )
        user_form.save()
        profile = profile_form.save(commit=False)

        telephone = profile_form.cleaned_data['telephone']
        telephone = ProfileHandler.telephone_formatter(telephone)
        profile.telephone = telephone

        profile.save()
        messages.add_message(self.request, messages.SUCCESS, "Данные профиля обновлены!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, "Ошибка.Данные профиля не обновлены!")
        return super().form_valid(form)

    def get_success_url(self):
        pk = self.kwargs["pk"]
        return reverse('app_user:account', kwargs={'pk': pk})

    def get_template_names(self):
        super(UpdateProfile, self).get_template_names()
        templates_dict = {
            'CSR': 'app_user/customer/profile_edit_customer.html',
            'SLR': 'app_user/seller/profile_edit_seller.html'
        }
        user_role = self.request.user.profile.role
        name = templates_dict[user_role]
        return name


# ACCOUNT SIDE BAR PAGE #

class DetailAccount(DetailView):
    """Класс-представление для детальной страницы профиля пользователя."""
    model = User
    context_object_name = 'user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        if is_customer(user):
            from app_order.services.order_services import CustomerOrderHandler
            context['last_order'] = CustomerOrderHandler.get_last_customer_order(user)
        return context

    def get_template_names(self):
        super(DetailAccount, self).get_template_names()
        templates_dict = {
            'CSR': 'app_user/customer/account_customer.html',
            'SLR': 'app_user/seller/account_seller.html'
        }
        user_role = self.request.user.profile.role
        name = templates_dict[user_role]
        return name


class DetailProfile(DetailView):
    model = User
    template_name = 'app_user/profile.html'
    context_object_name = 'user'


class DetailHistoryView(DetailView):
    """Класс-представление список просмотренных товаров."""
    model = User
    template_name = 'app_user/customer/history_view.html'
    context_object_name = 'user'

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        user = self.get_object()
        already_in_cart = get_items_in_cart(self.request)
        queryset = ItemHandler.get_history_views(user)
        context = {
            'object_list': queryset,
            'already_in_cart': already_in_cart
        }
        return render(request, self.template_name, context=context)


class CommentList(ListView, MixinPaginator):
    """Класс-представление для отображения списка всех товаров."""
    model = Comment
    template_name = 'app_user/customer/comment_list.html'
    paginate_by = 2

    def get_queryset(self):
        super(CommentList, self).get_queryset()
        all_comments = CommentHandler.get_comment_list_by_user(self.request)
        queryset = self.my_paginator(all_comments, self.request, self.paginate_by)
        return queryset


# LOG IN & OUT #


class UserLoginView(LoginView):
    template_name = 'registrations/login.html'

    def form_valid(self, form):
        """Логинит пользователя и вызывает функцию удаления cookies['cart] & cookies['has_cart]. """
        login(self.request, form.get_user())
        response = delete_cart_cookies(self.request, path=self.get_success_url())
        return response

    def get_success_url(self):
        next_page = self.request.GET.get('next')
        if next_page is not None:
            return redirect(quote(next_page))
        return reverse('app_user:account', kwargs={'pk': self.request.user.pk})


class UserLogoutView(LogoutView):
    template_name = 'registrations/logout.html'
    next_page = reverse_lazy('app_user:login')


# ACTIVATE ACCOUNT #

def account_activate(request, uidb64, token):
    pass
    # try:
    #     uid = force_str(urlsafe_base64_decode(uidb64))
    #     user = User.objects.get(pk=uid)
    #     verified_user_group = Group.objects.get(name='Пользователь')
    #
    #     user.profile.group = verified_user_group
    #     user.profile.save()
    #     user.groups.add(verified_user_group)
    #     user.save()
    #
    # except(TypeError, ValueError, OverflowError, user.DoesNotExist):
    #     user = None
    # if user is not None and account_activation_token.check_token(user, token):
    #     user.is_active = True
    #     user.save()
    #     login(request, user)
    #     return redirect('app_user:activated_success')
    # else:
    #     return redirect('app_user:invalid_activation')


class ActivatedAccount(TemplateView):
    pass
    # model = User
    # template_name = 'registrations/activated_successfully.html'
    #
    # def get(self, request, *args, **kwargs):
    #     context = self.get_context_data(**kwargs)
    #     context['user'] = self.request.user
    #     return self.render_to_response(context)


class InvalidActivatedAccount(TemplateView):
    pass
    # model = User
    # template_name = 'registrations/activation_invalid.html'
    #
    # def get(self, request, *args, **kwargs):
    #     context = self.get_context_data(**kwargs)
    #     context['user'] = self.request.user
    #     return self.render_to_response(context)


# PASSWORD CHANGE #

class PasswordChange(PasswordChangeView):
    form_class = PasswordChangeForm
    template_name = 'registrations/password_change_form.html'
    title = 'Password change'
    success_url = reverse_lazy('app_user:password_change_done')


class PasswordChangeDone(PasswordChangeDoneView):
    template_name = 'registrations/password_change_done.html'


class PasswordReset(PasswordResetView):
    template_name = 'registrations/password_reset_form.html'
    email_template_name = 'registrations/password_reset_email.html'
    form_class = PasswordResetForm
    from_email = None
    html_email_template_name = None
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('app_user:password_reset_done')
    title = 'Password reset'
    token_generator = default_token_generator


class PasswordResetDone(PasswordResetDoneView):
    template_name = 'registrations/password_reset_done.html'


class PasswordResetConfirm(PasswordResetConfirmView):
    success_url = reverse_lazy('app_user:password_reset_complete')
    template_name = 'registrations/password_reset_confirm.html'


class PasswordResetComplete(PasswordResetCompleteView):
    template_name = 'registrations/password_reset_complete.html'
