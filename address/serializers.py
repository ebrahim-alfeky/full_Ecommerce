from rest_framework import serializers
from .models import Address
from django.contrib.auth import get_user_model
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email','role','phone']


class AddressSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # nested serializer للـ user

    class Meta:
        model = Address
        fields = '__all__'

    def validate_label(self, value):
        user = self.context['request'].user
        if Address.objects.filter(user=user, label=value).exists():
            raise serializers.ValidationError("You already have an address with this label name.")
        return value

    def create(self, validated_data):
        validated_data.pop('user', None)  # لو موجودة، احذفها لتجنب التكرار
        user = self.context['request'].user
        return Address.objects.create(user=user, **validated_data)

