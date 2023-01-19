from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render
from django.template import RequestContext
from django.views.generic import TemplateView

from app_item.services.item_services import ItemHandler, AddItemToReview


class MainPage(TemplateView):
    """Класс-представление для отображения главной страницы."""
    template_name = 'main_page.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context['favorites'] = AddItemToReview().get_best_price_in_category(request.user)
        context['popular'] = ItemHandler.get_popular_items()[:8]
        context['limited_edition_items'] = ItemHandler.get_limited_edition_items()
        return self.render_to_response(context)
