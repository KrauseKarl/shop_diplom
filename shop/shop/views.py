from django.shortcuts import render, redirect
from django.views.generic import TemplateView

from app_item.services import item_services


class MainPage(TemplateView):
    """Класс-представление для отображения главной страницы."""
    template_name = 'main.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.user.groups.filter(name='seller').exists():
            return redirect('app_store:dashboard')
        elif request.user.groups.filter(name='admin').exists():
            return redirect('app_settings:dashboard')
        else:
            context['favorites'] = item_services.AddItemToReview().get_best_price_in_category(request.user)
            context['popular'] = item_services.ItemHandler.get_popular_items()[:8]
            context['limited_edition_items'] = item_services.ItemHandler.get_limited_edition_items()

        return self.render_to_response(context)


def my_permission_denied(request, exception):
    return render(request=request, template_name='errors/error403.html', status=403)


def my_page_not_found(request, exception):
    return render(request=request, template_name='errors/error404.html', context={'exception': exception}, status=404)


def my_server_error(request):
    return render(request=request, template_name='errors/error500.html', status=500)
