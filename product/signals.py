from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ProductVariant, Stock


@receiver(post_save, sender=ProductVariant)
def create_stock(sender, instance, created, **kwargs):
    if created:
        Stock.objects.get_or_create(
            variant=instance,
            defaults={"quantity": 0}
        )