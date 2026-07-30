from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.conf import settings

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('trader', 'Trader'),
        ('buyer', 'Buyer'),
        ('none', 'None'),
    )
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='none')
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # def get_total_orders(self):
    #     return self.orders.filter(is_paid=True).count()

    # def get_total_spent(self):
    #    return sum(order.total_price for order in self.orders.filter(is_paid=True))
    
    # def total_products(self):
    #     return sum(
    #         item.quantity
    #         for order in self.orders.filter(is_paid=True)
    #         for item in order.items.all()
    #     )
    def __str__(self):
        return self.username
    
    


def default_expiry():
    return timezone.now() + timedelta(minutes=2)  # الكود ينتهي بعد 2 دقيقة

class Code(models.Model):
    PURPOSE_CHOICES = [
    ('verify_email', 'Verify Email'),
    ('reset_password', 'Reset Password'),
    ('change_email', 'Change Email'),
    ('verify_phone', 'Verify Phone'),  # مستقبل SMS
    ('two_factor_auth', 'Two Factor Authentication'),  # 2FA
    ('delete_account', 'Delete Account Confirmation'),
    ('change_password', 'Change Password (Logged-In)'),
    ('confirm_transaction', 'Confirm Sensitive Transaction'),
    ('verify_new_device', 'Verify New Device Login'),
]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="codes"
    )
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_expiry)  


    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.user.email} - {self.purpose} - {self.code}"
