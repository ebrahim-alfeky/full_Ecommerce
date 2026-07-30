from django.urls import path
from .views import InitiatePaymentAPIView, PaymentReceiptView, PaymobWebhookView

urlpatterns = [
    path('initiate/<int:order_id>/', InitiatePaymentAPIView.as_view(), name='initiate-payment'),
    path('receipt/', PaymentReceiptView.as_view(), name='payment_receipt'),
    path('webhook/', PaymobWebhookView.as_view(), name='paymob_webhook'), # المسار الجديد
]