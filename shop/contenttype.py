from django.contrib.contenttypes.models import ContentType
ContentType.objects.all().delete()
ContentType.objects.clear_cache()