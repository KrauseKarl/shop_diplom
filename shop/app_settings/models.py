from django.core.cache import cache
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.timezone import now


class SingletonModel(models.Model):
    objects = models.Manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)
        self.set_cache()

    @classmethod
    def load(cls):
        if cache.get(cls.__name__) is None:
            obj, created = cls.objects.get_or_create(pk=1)
            if not created:
                obj.set_cache()
        return cache.get(cls.__name__)

    def set_cache(self):
        cache.set(self.__class__.__name__, self)


class SiteSettings(SingletonModel):
    class Delivery(models.TextChoices):
        STANDARD = "обычная доставка"
        EXPRESS = "экспресс доставка"
        ONESELF = "самовывоз"

    STATUS = (
        ("new", "Новый"),
        ("in_progress", "в обработке"),
        ("on_the_way", "доставляется"),
        ("is_ready", "готов к выдаче"),
        ("completed", "доставлен"),
        ("deactivated", "отменен"),
    )
    DELIVERY = (
        ("standard", "обычная доставка"),
        ("express", "экспресс доставка"),
    )
    PAY_TYPE = (
        ("online", "Онлайн картой"),
        ("someone", "Онлайн со случайного чужого счета"),
    )
    express_delivery_price = models.DecimalField(
        decimal_places=2,
        max_digits=9,
        null=True,
        blank=True,
        verbose_name="стоимость экспресс доставки",
        validators=[
            MinValueValidator(0),
        ],
    )
    min_free_delivery = models.DecimalField(
        decimal_places=2,
        max_digits=9,
        null=True,
        blank=True,
        verbose_name="минимальная сумма для бесплатной доставки",
        validators=[
            MinValueValidator(0),
        ],
    )
    delivery_fees = models.DecimalField(
        decimal_places=2,
        max_digits=9,
        null=True,
        blank=True,
        verbose_name="стоимость доставки",
        validators=[
            MinValueValidator(0),
        ],
    )
    cache_detail_view = models.IntegerField(
        verbose_name="время кэширования страницы товара", default=86400
    )
    type_of_delivery = models.CharField(
        max_length=256,
        verbose_name="тип доставки",
        choices=Delivery.choices,
        default="standard",
    )
    type_of_payment = models.CharField(
        max_length=256, verbose_name="тип оплаты", choices=PAY_TYPE, default="online"
    )
    url = models.URLField(verbose_name="Website url", max_length=256)
    title = models.CharField(
        verbose_name="название сайта", max_length=256, default="Megano"
    )
    support_email = models.EmailField(
        default="Support@ninzio.com", verbose_name="электронный ящик"
    )
    phone = models.CharField(
        max_length=256, verbose_name="телефон", default="8-800-200-600"
    )
    address = models.CharField(
        max_length=256,
        verbose_name="адрес",
        default="New York, north Avenue 26/7 0057 ",
    )
    skype = models.CharField(max_length=256, verbose_name="skype", default="techno")
    facebook = models.CharField(
        max_length=256, verbose_name="facebook", default="https://facebook.com/megano"
    )
    twitter = models.CharField(
        max_length=256, verbose_name="twitter", default="https://twitter.com/megano"
    )
    linkedIn = models.CharField(
        max_length=256, verbose_name="linkedIn", default="https://linkedin.com/megano"
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name="дата создания")
    updated = models.DateTimeField(auto_now_add=True, verbose_name="дата обновления")

    class Meta:
        db_table = "app_site_settings"
        verbose_name_plural = "Настройки"

    def __str__(self):
        return "Настройки"

    def save(self, *args, **kwargs):
        self.updated = now()
        super().save(*args, **kwargs)
