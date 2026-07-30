from rest_framework import viewsets, permissions
from .models import Address
from .serializers import AddressSerializer
from .permissions import IsOwnerOrAdmin  # لو حفظته في ملف permissions.py
from rest_framework.permissions import IsAuthenticated

class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [IsOwnerOrAdmin, IsAuthenticated]

    def get_queryset(self):
        # صاحب العنوان فقط يشوف العناوين الخاصة به
        print(self.request.COOKIES)
        print(self.request.user)
        return Address.objects.filter(user=self.request.user)


    def perform_create(self, serializer):
        # المستخدم المسجل دخول هيضاف العنوان بإسمه
        serializer.save(user=self.request.user)