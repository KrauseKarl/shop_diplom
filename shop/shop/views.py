from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponseNotFound, Http404, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.template import RequestContext
from django.views.generic import TemplateView
from django.conf.urls import handler400, handler403, handler404, handler500
from app_item.services.item_services import ItemHandler, AddItemToReview
from app_order.services import order_services
from app_item.services import comment_services
from django.views.defaults import permission_denied, page_not_found, server_error
from app_user import models as auth_modals
from app_store import models as store_modals
from app_item import models as item_models
from utils.my_utils import CustomerOnlyMixin


class MainPage(TemplateView):
    """Класс-представление для отображения главной страницы."""
    template_name = 'main_page.html'

    def get_template_names(self):
        super(MainPage, self).get_template_names()
        templates_dict = {
            'customer': 'main_page.html',
            'seller': 'main_page.html',
            'admin': 'app_settings/admin/dashboard.html',
        }
        if not self.request.user.is_authenticated:
            user_group = 'customer'
        else:
            user_group = self.request.user.groups.first().name
        name = templates_dict[user_group]
        return name

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        if request.user.groups.filter(name__in=('customer', 'seller')).exists() or not self.request.user.is_authenticated:
            context['favorites'] = AddItemToReview().get_best_price_in_category(request.user)
            context['popular'] = ItemHandler.get_popular_items()[:8]
            context['limited_edition_items'] = ItemHandler.get_limited_edition_items()
        elif request.user.groups.filter(name='admin').exists():
            return redirect('app_settings:dashboard')

        return self.render_to_response(context)


def my_permission_denied(request, exception):
    return render(request=request, template_name='errors/error403.html', status=403)


def my_page_not_found(request, exception):
    return render(request=request, template_name='errors/error404.html', context={'exception': exception}, status=404)


def my_server_error(request):
    return render(request=request, template_name='errors/error500.html', status=500)
