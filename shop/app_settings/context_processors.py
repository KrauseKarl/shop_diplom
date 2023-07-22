"""Модуль содержит контекст-процессоры настроек сайта."""
from .models import SiteSettings


def load_settings(request):
    return {"site_settings": SiteSettings.load()}
