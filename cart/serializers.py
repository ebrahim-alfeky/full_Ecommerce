from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Cart, CartItem
from product.serializers import ProductVariantSerializer

User = get_user_model()

class CartItemSerializer(serializers.ModelSerializer):
    product_variant = ProductVariantSerializer(read_only=True)
    product_variant_id = serializers.UUIDField(write_only=True)
    total_price = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    
    class Meta:
        model = CartItem
        fields = [
            'id', 
            'product_variant', 
            'product_variant_id', 
            'quantity', 
            'total_price', 
            'added_at'
        ]
        read_only_fields = ['id', 'added_at']


class AddToCartSerializer(serializers.Serializer):
    product_variant_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    total_quantity = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Cart
        fields = [
            'id', 
            'user', 
            'items', 
            'total_price', 
            'total_quantity', 
            'created_at', 
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']