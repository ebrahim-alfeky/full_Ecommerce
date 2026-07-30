from rest_framework import viewsets, filters
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Brand, Product, ProductImage, ProductVariant, Stock
from .serializers import (
    CategorySerializer, BrandSerializer, ProductSerializer,
    ProductImageSerializer, ProductVariantSerializer, StockSerializer
)
from .filters import (
    CategoryFilter, BrandFilter, ProductFilter,
    ProductImageFilter, ProductVariantFilter, StockFilter
)
from .pagination import CustomPagination 


# ---------------- Category ----------------
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = CategoryFilter
    search_fields = ['name']
    pagination_class = CustomPagination


# ---------------- Brand ----------------
class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = BrandFilter
    search_fields = ['name']
    pagination_class = CustomPagination
    


# ---------------- Product ----------------
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description']
    pagination_class = CustomPagination

# ---------------- ProductVariant ----------------
class ProductVariantViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProductVariant.objects.filter(is_active=True)
    serializer_class = ProductVariantSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = ProductVariantFilter
    search_fields = ['name']
    pagination_class = CustomPagination

# ---------------- ProductImage ----------------
class ProductImageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = ProductImageFilter
    search_fields = ['product__name']
    pagination_class = CustomPagination

# ---------------- Stock ----------------
class StockViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = StockFilter
    search_fields = ['variant__name']
    pagination_class = CustomPagination


