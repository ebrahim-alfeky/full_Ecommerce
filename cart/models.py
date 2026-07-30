from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from product.models import ProductVariant
import uuid

User = get_user_model()

class Cart(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f'Cart of {self.user.username}'
    
    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())
    
    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())
    
    def clear(self):
        self.items.all().delete()
        return self
    
    def get_item(self, product_variant):
        try:
            return self.items.get(product_variant=product_variant)
        except CartItem.DoesNotExist:
            return None


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    product_variant = models.ForeignKey(
        ProductVariant, 
        on_delete=models.CASCADE, 
        related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-added_at']
        unique_together = ['cart', 'product_variant']
    
    def __str__(self):
        return f'{self.quantity} × {self.product_variant.product.name}'
    
    @property
    def total_price(self):
        return self.quantity * self.product_variant.discounted_price
    '''
    discounted_price => function in product_variant class
    '''
    
    
    def increase_quantity(self, amount=1):
        self.quantity += amount
        self.save()
    
    def decrease_quantity(self, amount=1):
        if self.quantity > amount:
            self.quantity -= amount
            self.save()
        else:
            self.delete()