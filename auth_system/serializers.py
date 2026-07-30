# serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model

from address.models import Address
from .models import Code
from django.utils import timezone
User = get_user_model()

class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role', 'phone']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.is_active = False  # الحساب غير مفعل لحد التحقق
        user.save()
        return user

class AddressSerializerNesting(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = ['label', 'full_name', 'phone', 'country', 'city', 'street','building_number', 'is_default']

    

class UserSerializer(serializers.ModelSerializer):
    addresses = AddressSerializerNesting(many=True, read_only=True)
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email','role','phone', 'addresses']

