import os
from django.contrib.auth.models import User
from app_user.models import Profile

if User.objects.all().count() < 1:
    admin = User.objects.create_superuser(
        username=os.getenv("DJANGO_SUPERUSER_USERNAME", "admin"),
        email=os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@mail.com"),
        password=os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin"),
    )
    Profile.objects.create(
        user=admin,
        is_active=True,
        telephone="1111111111",
    )
