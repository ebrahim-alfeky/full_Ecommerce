from django_filters.rest_framework import DjangoFilterBackend
from .models import*
import django_filters


class CategoryFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    parent = django_filters.NumberFilter(field_name='parent')

    class Meta:
        model = Category
        fields = ['name', 'parent']


class BrandFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Brand
        fields = ['name']


class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    category = django_filters.NumberFilter(field_name='category')
    brand = django_filters.NumberFilter(field_name='brand')
    min_price = django_filters.NumberFilter(field_name='variants__base_price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='variants__base_price', lookup_expr='lte')
    is_active = django_filters.BooleanFilter(field_name='is_active')

    class Meta:
        model = Product
        fields = ['name', 'category', 'brand', 'min_price', 'max_price', 'is_active']


class ProductVariantFilter(django_filters.FilterSet):
    product = django_filters.NumberFilter(field_name='product')
    is_active = django_filters.BooleanFilter(field_name='is_active')
    min_price = django_filters.NumberFilter(field_name='base_price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='base_price', lookup_expr='lte')
    
    class Meta:
        model = ProductVariant
        fields = ['product', 'is_active', 'min_price', 'max_price']



class ProductImageFilter(django_filters.FilterSet):
    product = django_filters.NumberFilter(field_name='product')
    min_price = django_filters.NumberFilter(field_name='product__base_price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='product__base_price', lookup_expr='lte')
    is_main = django_filters.BooleanFilter(field_name='is_main')

    class Meta:
        model = ProductImage
        fields = ['product', 'min_price', 'max_price', 'is_main']


class StockFilter(django_filters.FilterSet):
    variant = django_filters.NumberFilter(field_name='variant')
    quantity_min = django_filters.NumberFilter(field_name='quantity', lookup_expr='gte')
    quantity_max = django_filters.NumberFilter(field_name='quantity', lookup_expr='lte')

    class Meta:
        model = Stock
        fields = ['variant', 'quantity_min', 'quantity_max']
