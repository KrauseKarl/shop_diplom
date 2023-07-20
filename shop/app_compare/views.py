"""Модуль содержит классы-предстывления для работы с со списком сравнения."""
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import generic

from app_compare.compare import Comparison
from app_item import models as item_models


class AddItemComparison(generic.TemplateView):
    """Класс-представление для добавления товара в список сравнения."""

    model = item_models.Item

    def get(self, request, *args, **kwargs):
        """GET-функция для добавления товара в список сравнения."""
        Comparison(request).add(str(kwargs["pk"]))
        return redirect(request.META.get("HTTP_REFERER"))


class RemoveItemComparison(generic.TemplateView):
    """Класс-представление для удаления товара из списка сравнения."""

    model = item_models.Item

    def get(self, request, *args, **kwargs):
        """GET-функция для удаления товара в список сравнения."""
        Comparison(request).remove(kwargs["pk"])
        return redirect(request.META.get("HTTP_REFERER"))


class CompareItemView(generic.DetailView):
    """Класс-представление для сравнения товаров."""

    model = item_models.Item
    template_name = "app_compare/compare_list.html"

    def get(self, request, *args, **kwargs):
        """Функция-get для отображения списка-сравнения."""
        object_list = Comparison(request).all()
        value_list = object_list.values_list("feature_value", flat=True)
        compare_mode = bool(request.GET.get("compare"))
        if compare_mode:
            final_list = {}
            unique = []
            for val in value_list:
                final_list[val] = final_list.get(val, 0) + 1
            for k, v in final_list.items():
                if v < object_list.count():
                    try:
                        value = item_models.FeatureValue.objects.get(id=k)
                        if value.feature not in unique:
                            unique.append(value.feature)
                    except ValueError:
                        pass
        else:
            unique = item_models.Feature.objects.filter(
                values__in=value_list
            ).distinct()
        context = {"object_list": object_list, "unique": unique}
        return render(request, self.template_name, context=context)


class RemoveAllComparison(generic.TemplateView):
    """Класс-представление для удаления товара из корзины."""

    model = item_models.Item
    template_name = "app_compare/compare_list.html"

    def get(self, request, *args, **kwargs):
        """GET-функция для очистки списка товаров."""
        compares = Comparison(request)
        compares.clear()
        return redirect(reverse("app_compare:compare"))
