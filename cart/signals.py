from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Cart, CartItem
from product.models import Stock

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_cart(sender, instance, created, **kwargs):
    """Automatically create cart when user is created"""
    if created:
        Cart.objects.create(user=instance)


@receiver(pre_save, sender=CartItem)
def validate_stock_before_save(sender, instance, **kwargs):
    """Validate stock before saving cart item"""
    if instance.pk:  # If updating existing item
        try:
            old_item = CartItem.objects.get(pk=instance.pk)
            if old_item.quantity != instance.quantity:
                if instance.quantity > instance.product_variant.stock.quantity:
                    raise ValueError(
                        f"Insufficient stock. Available: {instance.product_variant.stock.quantity}"
                    )
        except CartItem.DoesNotExist:
            pass
    else:  # If creating new item
        if instance.quantity > instance.product_variant.stock.quantity:
            raise ValueError(
                f"Insufficient stock. Available: {instance.product_variant.stock.quantity}"
            )