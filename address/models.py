from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your models here.
from django.conf import settings

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=50)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    street = models.CharField(max_length=255)
    building_number = models.CharField(max_length=50, blank=True, null=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'label')

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(
                user=self.user,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.label} - {self.city} - {self.street}"
