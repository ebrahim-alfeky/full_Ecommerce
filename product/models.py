from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model
User = get_user_model()
from decimal import Decimal

from django.db import models, transaction
from django.db.models import Q
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    parent = models.ForeignKey(
        "self",
        related_name="children",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def save(self, *args, **kwargs):
        if self.parent == self:
            raise ValueError("Category cannot be parent of itself.")

        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to="brands/", blank=True, null=True)

    def __str__(self):
        return self.name

# class Seller(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     store_name = models.CharField(max_length=150)
#     logo = models.ImageField(upload_to="sellers/", null=True, blank=True)
#     is_active = models.BooleanField(default=True)

#     def __str__(self):
#         return self.store_name
    


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    category = models.ForeignKey(
        Category,
        related_name="products",
        on_delete=models.PROTECT,
    )

    brand = models.ForeignKey(
        Brand,
        related_name="products",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name



class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        related_name="images",
        on_delete=models.CASCADE,
    )

    image = models.ImageField(upload_to="products/")
    is_main = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product"],
                condition=Q(is_main=True),
                name="unique_main_image_per_product",
            )
        ]

    @transaction.atomic
    def save(self, *args, **kwargs):
        if self.is_main:
            ProductImage.objects.filter(
                product=self.product,
                is_main=True,
            ).exclude(pk=self.pk).update(is_main=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image of {self.product.name}"


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        related_name="variants",
        on_delete=models.CASCADE,
    )

    name = models.CharField(max_length=100)

    sku = models.CharField(
        max_length=50,
        unique=True,
    )

    barcode = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )

    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    is_active = models.BooleanField(default=True, db_index=True)

    @property
    def discounted_price(self):
        if self.discount_percent > 0:
            return self.base_price * (
                Decimal("1") - self.discount_percent / Decimal("100")
            )
        return self.base_price

    def __str__(self):
        return f"{self.product.name} ({self.name})"


class Stock(models.Model):
    variant = models.OneToOneField(
        ProductVariant,
        related_name="stock",
        on_delete=models.CASCADE,
    )

    quantity = models.PositiveIntegerField(default=0)

    low_stock_threshold = models.PositiveIntegerField(default=5)

    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold

    @transaction.atomic
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        variant_should_be_active = self.quantity > 0

        if self.variant.is_active != variant_should_be_active:
            self.variant.is_active = variant_should_be_active
            self.variant.save(update_fields=["is_active"])

        product = self.variant.product

        product_should_be_active = product.variants.filter(
            is_active=True
        ).exists()

        if product.is_active != product_should_be_active:
            product.is_active = product_should_be_active
            product.save(update_fields=["is_active"])

    def __str__(self):
        return f"{self.variant.name} - {self.quantity}"