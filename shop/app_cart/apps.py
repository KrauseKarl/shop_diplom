from django.apps import AppConfig


class AppCartConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_cart'

    # def ready(self):
    #     from app_cart.signals import post_save_refresh_cache
