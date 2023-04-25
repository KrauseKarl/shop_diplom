from pprint import pprint

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponseNotFound, Http404
from django.shortcuts import render
from django.template import RequestContext
from django.views.generic import TemplateView
from django.conf.urls import handler400, handler403, handler404, handler500
from app_item.services.item_services import ItemHandler, AddItemToReview
from django.views.defaults import permission_denied, page_not_found, server_error


class MainPage(TemplateView):
    """Класс-представление для отображения главной страницы."""
    template_name = 'main_page.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context['favorites'] = AddItemToReview().get_best_price_in_category(request.user)
        context['popular'] = ItemHandler.get_popular_items()[:8]
        context['limited_edition_items'] = ItemHandler.get_limited_edition_items()
        return self.render_to_response(context)


def my_permission_denied(request, exception):
    return render(request=request, template_name='errors/error403.html', status=403)


def my_page_not_found(request, exception):
    return render(request=request, template_name='errors/error404.html', context={'exception': exception}, status=404)


def my_server_error(request):
    return render(request=request, template_name='errors/error500.html', status=500)
