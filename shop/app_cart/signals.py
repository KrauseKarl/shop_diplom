from django.core.cache import cache
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from app_cart.models import CartItem, Cart


# @receiver(post_save, sender=Cart)
# def post_save_refresh_cache(sender, instance, **kwargs):
#     cache.delete(f'cart_dict_{instance.user.id}')
