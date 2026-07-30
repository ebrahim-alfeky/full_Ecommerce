# payments/views.py
import hmac
import hashlib
from datetime import timedelta
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.utils import timezone
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from order.models import Order
from .models import Payment
from .paymob import PaymobHelper


# ==========================================
# 1. Create Payment View
# ==========================================
class InitiatePaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    """
    Create a payment for an order.
    Handles Paymob (online) or COD (Cash on Delivery).
    """

    def post(self, request, order_id):
        order = get_object_or_404(
            Order.objects
            .select_related("shipping_address")
            .prefetch_related("items", "payments"),
            id=order_id,
            user=request.user
        )
        
        # إذا الدفع عند الاستلام
        if order.payment_method.lower() == "cod":
            return Response({
                "message": "Order is Cash on Delivery. No payment object created.",
                "order_number": order.order_number,
            }, status=status.HTTP_200_OK)

        # التحقق من حالة الدفع
        if order.payment_status == "paid" or order.is_paid:
            return Response({
                "message": "Order is already paid.",
                "order_number": order.order_number
            }, status=status.HTTP_400_BAD_REQUEST)

        # إذا كانت حالة الدفع "expired"
        elif order.payment_status == "expired":
            return Response({
                "message": "Payment window expired. You cannot pay this order anymore.",
                "order_number": order.order_number
            }, status=status.HTTP_400_BAD_REQUEST)
 
        # التحقق من وجود رابط دفع نشط
        active_payment_exists = order.payments.filter(
            status="pending",
            created_at__gte=timezone.now() - timedelta(seconds=settings.PAYMENT_LINK_LIFETIME_SECONDS)
        )

        if active_payment_exists.exists():
            return Response({
                "message": "There is already an active payment link. Please use the existing one.",
                "payment_url": active_payment_exists.first().payment_url,
                "order_number": order.order_number
            }, status=status.HTTP_200_OK)
            
        order_expired = order.created_at + timedelta(minutes=settings.ORDER_EXPIRE_MINUTES) < timezone.now()
        if order_expired:
            return Response({
                "message": "This order has passed the allowed time to request payment links.",
                "order_number": order.order_number
            }, status=status.HTTP_400_BAD_REQUEST) 

        if order.payment_method.lower() == "epay":
            shipping_address = getattr(order, 'shipping_address', None)
            
            if not shipping_address:
                return Response({
                    "detail": "Order does not have a shipping address."
                }, status=status.HTTP_400_BAD_REQUEST)

            # استدعاء الـ Helper لإنشاء الـ Intention
            paymob_data = PaymobHelper.create_payment_intention(
                order=order,
                payment_amount=order.total_price,
                shipping_address=shipping_address
            )
            
            if not paymob_data:
                return Response(
                    {"detail": "Failed to initiate payment with Paymob. Please try again later."},
                    status=status.HTTP_502_BAD_GATEWAY
                )
            
            intention_id = paymob_data.get("id")
            paymob_order_id = paymob_data.get("intention_order_id")
            client_secret = paymob_data.get("client_secret")
            
            # توليد رابط الدفع
            payment_url = (
                f"https://accept.paymob.com/unifiedcheckout/"
                f"?publicKey={settings.PAYMOB_PUBLIC_KEY}"
                f"&clientSecret={client_secret}"
            )
            
            # res_payment_methods = '--'.join([method['name'] for method in paymob_data.get('payment_methods', [])])

            # إنشاء الـ Payment object في النظام
            payment = Payment.objects.create(
                user=request.user,
                order=order,
                amount=order.total_price,
                currency=order.currency or "EGP",
                status="pending",
                provider="Paymob",
                provider_payment_id=intention_id,
                paymob_order_id=str(paymob_order_id),
                client_secret=client_secret,
                # payment_method=res_payment_methods,
                payment_method=order.payment_method,
                payment_url=payment_url
            )

            order.payment_status = "pending"
            order.save()

            return Response({
                "payment_url": payment.payment_url,
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            "message": "Unsupported payment method.",
        }, status=status.HTTP_400_BAD_REQUEST)


# ==========================================
# 2. Payment Receipt View
# ==========================================
class PaymentReceiptView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        success_param = request.GET.get('success', 'false')
        transaction_id = request.GET.get('id', 'N/A')
        order_id = request.GET.get('order', 'N/A')
        
        is_success = success_param.lower() == 'true'

        html_content = f"""
        <html>
        <head>
            <title>نتيجة الدفع</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; background-color: #f4f6f9; }}
                .card {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); display: inline-block; max-width: 500px; width: 100%; }}
                .success {{ color: #2ecc71; font-size: 48px; }}
                .failed {{ color: #e74c3c; font-size: 48px; }}
                h2 {{ color: #333; }}
                p {{ color: #666; font-size: 16px; margin: 10px 0; }}
                .btn {{ display: inline-block; padding: 10px 20px; background: #0056b3; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="card">
                { '<div class="success">✓</div><h2>تمت عملية الدفع بنجاح!</h2>' if is_success else '<div class="failed">✗</div><h2>عذراً، فشلت عملية الدفع</h2>' }
                <p><strong>رقم المعاملة (Paymob ID):</strong> {transaction_id}</p>
                <p><strong>رقم الطلب في النظام:</strong> {order_id}</p>
                <p>{ 'تم تحديث حالة طلبك وشحن المنتجات تلقائياً.' if is_success else 'لم يتم سحب أي مبالغ من كارتك، برجاء إعادة المحاولة.' }</p>
                <a href="/" class="btn">العودة للرئيسية</a>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html_content)


# ==========================================
# 3. Paymob Callback View (Webhook)
# ==========================================
@method_decorator(csrf_exempt, name='dispatch')
class PaymobWebhookView(APIView):
    permission_classes = [AllowAny]
    """
    Handles Paymob webhook callback for transaction updates.
    """

    def normalize_value(self, val):
        if val is None or val == "null":
            return ""
        if isinstance(val, bool):
            return str(val).lower()  # True -> "true", False -> "false"
        return str(val)

    def post(self, request):
        data = request.data
        obj = data.get("obj", {})

        # تجميع الـ Keys بنفس الترتيب المطلوب بالظبط
        keys = {
            "amount_cents": obj.get("amount_cents"),
            "created_at": obj.get("created_at"),
            "currency": obj.get("currency"),
            "error_occured": obj.get("error_occured"),
            "has_parent_transaction": obj.get("has_parent_transaction"),
            "obj.id": obj.get("id"),
            "integration_id": obj.get("integration_id"),
            "is_3d_secure": obj.get("is_3d_secure"),
            "is_auth": obj.get("is_auth"),
            "is_capture": obj.get("is_capture"),
            "is_refunded": obj.get("is_refunded"),
            "is_standalone_payment": obj.get("is_standalone_payment"),
            "is_voided": obj.get("is_voided"),
            "order.id": obj.get("order", {}).get("id") if isinstance(obj.get("order"), dict) else obj.get("order"),
            "owner": obj.get("owner"),
            "pending": obj.get("pending"),
            "source_data.pan": obj.get("source_data", {}).get("pan"),
            "source_data.sub_type": obj.get("source_data", {}).get("sub_type"),
            "source_data.type": obj.get("source_data", {}).get("type"),
            "success": obj.get("success"),
        }
            
        received_hmac = request.query_params.get("hmac") or request.GET.get("hmac") or data.get("hmac")
        if not received_hmac:
            return Response({"message": "HMAC missing"}, status=status.HTTP_400_BAD_REQUEST)

        # الترتيب المتطابق مع الـ keys بالملي
        keys_order = [
            "amount_cents",
            "created_at",
            "currency",
            "error_occured",
            "has_parent_transaction",
            "obj.id",
            "integration_id",
            "is_3d_secure",
            "is_auth",
            "is_capture",
            "is_refunded",
            "is_standalone_payment",
            "is_voided",
            "order.id",
            "owner",
            "pending",
            "source_data.pan",
            "source_data.sub_type",
            "source_data.type",
            "success",
        ]

        # بناء الـ Concatenated String
        concatenated_string = "".join([self.normalize_value(keys[k]) for k in keys_order])

        # حساب الـ HMAC باستخدام السيكرت بتاعك
        computed_hmac = hmac.new(
            settings.PAYMOB_HMAC_TOKEN.encode("utf-8"),
            concatenated_string.encode("utf-8"),
            hashlib.sha512
        ).hexdigest()

        # التحقق من المطابقة والتأكيد
        if not hmac.compare_digest(computed_hmac, received_hmac):
            print("🚨 HMAC mismatch!")
            print(f"Calculated: {computed_hmac}")
            print(f"Received: {received_hmac}")
            return Response({"message": "Invalid HMAC"}, status=status.HTTP_400_BAD_REQUEST)

        if data.get("type") != "TRANSACTION":
            return Response({"message": "Not a transaction callback"}, status=status.HTTP_400_BAD_REQUEST)

        paymob_order_id = obj.get("order", {}).get("id") if isinstance(obj.get("order"), dict) else obj.get("order")
        success = obj.get("success", False)

        payment = Payment.objects.filter(paymob_order_id=str(paymob_order_id)).first()
        if not payment:
            return Response({"message": "Payment not found"}, status=status.HTTP_202_ACCEPTED)

        payment.webhook_received = True
        payment.webhook_payload = data
        payment.save()

        order = payment.order
        if not order:
            return Response({"message": "Order not found"}, status=status.HTTP_202_ACCEPTED)

        if order.is_paid:
            return Response({"message": "Order already marked as paid"}, status=status.HTTP_200_OK)

        # تحديث الحالات بالـ Methods بتاعتك في الـ Models
        if success:
            order.set_status("paid")
            payment.mark_as_paid()
            print(f"✅ Transaction {obj.get('id')} Succeeded. Order {order.order_number} marked as Paid.")
        else:
            payment.mark_as_failed()
            print(f"❌ Transaction {obj.get('id')} Failed for Order {order.order_number}")

        return Response({"message": "Callback processed successfully"}, status=status.HTTP_200_OK)