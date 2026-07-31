from rest_framework import serializers
from .models import Review

from django.contrib.auth import get_user_model
User = get_user_model()

from product.models import ProductVariant

class MiniUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']
    
class MiniProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'name']

class ReviewSerializer(serializers.ModelSerializer):
    user = MiniUserSerializer(read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'comment', 'product', 'created_at']
    
class UserReviewSerializer(serializers.ModelSerializer):
    user = MiniUserSerializer(read_only=True)
    product = MiniProductSerializer(read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'comment', 'product', 'created_at']