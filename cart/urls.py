from django.urls import path
from .views import CartAPIView, CartItemDetailAPIView, CartSummaryAPIView

urlpatterns = [
    path('cart/', CartAPIView.as_view(), name='cart'),
    path('summary/', CartSummaryAPIView.as_view(), name='cart-summary'),
    path('items/<int:item_id>/', CartItemDetailAPIView.as_view(), name='cart-item-detail'),
]