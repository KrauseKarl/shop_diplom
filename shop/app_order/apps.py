from django.apps import AppConfig


class AppOrderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_order'

    def ready(self):
        from app_order import signals