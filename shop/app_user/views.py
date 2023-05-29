from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import forms as password_form
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import views as auth_views
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy, reverse
from django.views import generic
from django.contrib.auth.models import User
from django.contrib.auth import mixins

# modals
from app_cart import models as cart_modals
from app_item import models as item_modals
from app_user import models as user_modals
# form
from app_user import forms as user_form
# services
from app_cart.services import cart_services
from app_item.services import comment_services
from app_item.services import item_services
from app_user.services import register_services
from app_user.services import user_services
# other
from utils.my_utils import MixinPaginator, CustomerOnlyMixin


# CREATE & UPDATE PROFILE #
class CreateProfile(SuccessMessageMixin, generic.CreateView):
    """Класс-представление для создания профиля пользователя."""
    model = User
    second_model = user_modals.Profile
    template_name = 'registrations/register.html'
    form_class = user_form.RegisterUserForm

    def get_success_url(self):
        return reverse('app_user:account', kwargs={'pk': self.request.user.pk})

    def form_valid(self, form):
        response = register_services.ProfileHandler.create_user(
            self.request,
            form,
            self.get_success_url
        )
        return response

    def form_invalid(self, form):
        form = user_form.RegisterUserForm(self.request.POST)
        return super(CreateProfile, self).form_invalid(form)


class UpdateProfile(generic.UpdateView):
    """Класс-представление для обновления профиля пользователя."""
    model = User
    second_model = user_modals.Profile
    template_name = 'app_user/profile_edit.html'
    form_class = user_form.UpdateProfileForm
    # second_form_class = user_form.UpdateProfileForm

    def form_valid(self, form):
        register_services.ProfileHandler.update_profile(self.request)
        messages.add_message(self.request, messages.SUCCESS, "Данные профиля обновлены!")
        return super().form_valid(form)

    def form_invalid(self, form):
        form = user_form.UpdateProfileForm(self.request.POST)
        messages.add_message(self.request, messages.ERROR, "Ошибка.Данные профиля не обновлены!")
        return super(UpdateProfile, self).form_invalid(form)

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

class DetailAccount(mixins.LoginRequiredMixin, mixins.UserPassesTestMixin, generic.DetailView):
    """Класс-представление для детальной страницы профиля пользователя."""
    model = User
    context_object_name = 'user'

    def test_func(self):
        if self.request.user == self.get_object():
            return True
        return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        if user_services.is_customer(user):
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


class DetailProfile(generic.DetailView):
    model = User
    template_name = 'app_user/profile.html'
    context_object_name = 'user'


class HistoryDetailView(CustomerOnlyMixin, generic.ListView, MixinPaginator):
    """Класс-представление список просмотренных товаров."""
    model = User
    template_name = 'app_user/customer/history_view.html'
    context_object_name = 'user'
    paginate_by = 8

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        user = self.request.user
        already_in_cart = cart_services.get_items_in_cart(self.request)
        queryset = item_services.ItemHandler.get_history_views(user)
        queryset = MixinPaginator(queryset, self.request, self.paginate_by).my_paginator()
        context = {
            'object_list': queryset,
            'already_in_cart': already_in_cart
        }
        return render(request, self.template_name, context=context)


class CommentList(generic.ListView, MixinPaginator):
    """Класс-представление для отображения списка всех товаров."""
    model = item_modals.Comment
    template_name = 'app_user/customer/comment_list.html'
    paginate_by = 2

    def get_queryset(self):
        super(CommentList, self).get_queryset()
        object_list = comment_services.CommentHandler.get_comment_list_by_user(self.request)
        queryset = MixinPaginator(object_list, self.request, self.paginate_by).my_paginator()
        return queryset


# LOG IN & OUT #


class UserLoginView(auth_views.LoginView):
    template_name = 'registrations/login.html'

    def form_valid(self, form):
        """Логинит пользователя и вызывает функцию удаления cookies['cart] & cookies['has_cart]. """
        login(self.request, form.get_user())
        if user_services.user_in_group(self.request.user, 'customer'):
            response = cart_services.delete_cart_cookies(
                self.request,
                path=reverse('app_user:account', kwargs={'pk': self.request.user.pk})
            )
            return response
        if self.request.GET.get('next'):
            return HttpResponseRedirect(reverse(self.request.GET.get('next')))
        return HttpResponseRedirect(reverse('app_user:account', kwargs={'pk': self.request.user.pk}))


class UserLogoutView(auth_views.LogoutView):
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


class ActivatedAccount(generic.TemplateView):
    pass
    # model = User
    # template_name = 'registrations/activated_successfully.html'
    #
    # def get(self, request, *args, **kwargs):
    #     context = self.get_context_data(**kwargs)
    #     context['user'] = self.request.user
    #     return self.render_to_response(context)


class InvalidActivatedAccount(generic.TemplateView):
    pass
    # model = User
    # template_name = 'registrations/activation_invalid.html'
    #
    # def get(self, request, *args, **kwargs):
    #     context = self.get_context_data(**kwargs)
    #     context['user'] = self.request.user
    #     return self.render_to_response(context)


# PASSWORD CHANGE #

class PasswordChange(auth_views.PasswordChangeView):
    form_class = password_form.PasswordChangeForm
    template_name = 'registrations/password_change_form.html'
    title = 'Password change'
    success_url = reverse_lazy('app_user:password_change_done')


class PasswordChangeDone(auth_views.PasswordChangeDoneView):
    template_name = 'registrations/password_change_done.html'


class PasswordReset(auth_views.PasswordResetView):
    template_name = 'registrations/password_reset_form.html'
    email_template_name = 'registrations/password_reset_email.html'
    form_class = password_form.PasswordResetForm
    from_email = None
    html_email_template_name = None
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('app_user:password_reset_done')
    title = 'Password reset'
    token_generator = default_token_generator


class PasswordResetDone(auth_views.PasswordResetDoneView):
    template_name = 'registrations/password_reset_done.html'


class PasswordResetConfirm(auth_views.PasswordResetConfirmView):
    success_url = reverse_lazy('app_user:password_reset_complete')
    template_name = 'registrations/password_reset_confirm.html'


class PasswordResetComplete(auth_views.PasswordResetCompleteView):
    template_name = 'registrations/password_reset_complete.html'
