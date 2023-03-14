from django.core.cache import cache
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from app_order.models import Order


@receiver(post_save, sender=Order)
def post_save_refresh_cache(sender, instance, created, **kwargs):
    if created:
        cache.delete(f'order_list_{instance.user.get_full_name()}')
