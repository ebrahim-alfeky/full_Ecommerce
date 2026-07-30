from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.conf import settings

from order.models import Order
from .models import Payment
from .paymob import PaymobHelper
# Create your views here.


class InitiatePaymentAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, *args, **kwargs):
        user = request.user
        order_id = request.data.get("order_id")
        
        if not order_id:
            return Response({
                    "detail": "order_id is required."
                }, 
                status=status.HTTP_400_BAD_REQUEST)
        
        order = get_object_or_404(Order, id=order_id, user=user)
        if order.is_paid or order.payment_status == 'paid':
            return Response({
                    "detail": "This order is already paid."
                },
                status=status.HTTP_400_BAD_REQUEST)

        shipping_address = getattr(order, 'shipping_address', None)
        
        if not shipping_address:
            return Response({
                    "detail": "Order does not have a shipping address."}, 
                status=status.HTTP_400_BAD_REQUEST)
            
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
        
        # return Response(
        #         paymob_data,
        #         status=status.HTTP_200_OK
        #     )
        intention_id = paymob_data.get("id")
        paymob_order_id = paymob_data.get("intention_order_id")
        client_secret = paymob_data.get("client_secret")
        
        payment_url = (
            f"https://accept.paymob.com/unifiedcheckout/"
            f"?publicKey={settings.PAYMOB_PUBLIC_KEY}"
            f"&clientSecret={client_secret}"
        )        
        payment = Payment.objects.create(
            order=order,
            user=user,
            amount=order.total_price,
            currency="EGP",
            status="pending",
            provider="paymob",
            provider_payment_id=intention_id,      # الـ id الفريد للـ intention
            paymob_order_id=str(paymob_order_id), # الـ order id بتاع باي موب
            client_secret=client_secret,
            payment_url=payment_url,
            payment_method=order.payment_method
        )
        
        return Response({
            "message": "Payment initiated successfully.",
            "payment_id": payment.id,
            "payment_url": payment_url
        }, status=status.HTTP_201_CREATED)
        
        

from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.http import HttpResponse

class PaymentReceiptView(APIView):
    permission_classes = [AllowAny] # عشان أي عميل يقدر يشوف الصفحة بعد الدفع

    def get(self, request, *args, **kwargs):
        # باي موب بيبعت حالة العملية في الحقل ده جوه الـ URL: success
        # القيمة المبعوتة بتكون string إما 'true' أو 'false'
        success_param = request.GET.get('success', 'false')
        transaction_id = request.GET.get('id', 'N/A')
        order_id = request.GET.get('order', 'N/A')
        
        # تحويل القيمة لنوع Boolean للتأكد
        is_success = success_param.lower() == 'true'

        context = {
            'is_success': is_success,
            'transaction_id': transaction_id,
            'order_id': order_id,
        }

        # بناء صفحة HTML سريعة ونضيفة تظهر للعميل
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
    
    
import hmac
import hashlib
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.conf import settings

class PaymobWebhookView(APIView):
    permission_classes = [AllowAny] # الـ Webhook مفتوح لباي موب

    def clean_val(self, val):
        # لتحويل البولين لحروف صغيرة والتعامل مع القيم الفارغة بشكل سليم
        if isinstance(val, bool):
            return str(val).lower()
        return str(val) if val is not None else ""

    def post(self, request, *args, **kwargs):
        data = request.data
        
        # 1. السحب من الـ JSON اللي جاي من باي موب
        obj = data.get("obj", {})
        hmac_received = request.GET.get("hmac") or data.get("hmac") # التوقيع المبعوث
        
        if not obj or not hmac_received:
            return Response({"detail": "Missing data or HMAC"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. تجميع الحقول بالترتيب الصارم مع استدعاء self.clean_val
        hmac_fields = [
            self.clean_val(obj.get("amount_cents")),
            self.clean_val(obj.get("created_at")),
            self.clean_val(obj.get("currency")),
            self.clean_val(obj.get("error_occured")),
            self.clean_val(obj.get("has_parent_transaction")),
            self.clean_val(obj.get("id")),
            self.clean_val(obj.get("integration_id")),
            self.clean_val(obj.get("is_3d_secure")),
            self.clean_val(obj.get("is_auth")),
            self.clean_val(obj.get("is_capture")),
            self.clean_val(obj.get("is_refunded")),
            self.clean_val(obj.get("is_standalone_payment")),
            self.clean_val(obj.get("is_voided")),
            self.clean_val(obj.get("order", {}).get("id")),
            self.clean_val(obj.get("owner")),
            self.clean_val(obj.get("pending")),
            self.clean_val(obj.get("source_data", {}).get("pan")),
            self.clean_val(obj.get("source_data", {}).get("sub_type")),
            self.clean_val(obj.get("source_data", {}).get("type")),
            self.clean_val(obj.get("success")),
        ]
        print("📥 Received Data Keys & Values:")
        for key in ["amount_cents", "created_at", "currency", "error_occured", "has_parent_transaction", "id", "integration_id", "is_3d_secure", "is_auth", "is_capture", "is_refunded", "is_standalone_payment", "is_voided", "owner", "pending", "success"]:
            print(f"  {key}: {obj.get(key)} (Type: {type(obj.get(key))})")
        
        print(f"  order_id: {obj.get('order', {}).get('id') if isinstance(obj.get('order'), dict) else obj.get('order')}")
        print(f"  pan: {obj.get('source_data', {}).get('pan')}")
        print(f"  type: {obj.get('source_data', {}).get('type')}")
        print(f"  sub_type: {obj.get('source_data', {}).get('sub_type')}")
        # دمج كل الحقول كـ String واحد بدون مسافات أو فواصل
        hmac_string = "".join(hmac_fields)
        
        # 3. حساب الـ HMAC باستخدام الـ Hmac Token الخاص بيك
        hmac_secret = getattr(settings, "PAYMOB_HMAC_TOKEN", "").encode('utf-8')
        calculated_hmac = hmac.new(hmac_secret, hmac_string.encode('utf-8'), hashlib.sha512).hexdigest()

        # 4. التحقق: هل التوقيع المحسوب يطابق التوقيع المبعوث؟
        if not hmac.compare_digest(calculated_hmac, hmac_received):
            print("🚨 HMAC mismatch!")
            print(f"Calculated: {calculated_hmac}")
            print(f"Received: {hmac_received}")
            return Response({"detail": "Invalid HMAC signature. Security alert!"}, status=status.HTTP_401_UNAUTHORIZED)

        # 5. إذا كان التوقيع سليم، نقرأ حالة المعاملة الحقيقية ونحدث الداتا بيز
        transaction_success = obj.get("success") # ده True أو False فعلي
        order_id = obj.get("order", {}).get("id") if isinstance(obj.get("order"), dict) else obj.get("order")
        
        if transaction_success:
            # هنا تحدث حالة الطلب في الداتا بيز بتاعتك
            print(f"✅ Transaction {obj.get('id')} Succeeded for Order {order_id}")
        else:
            print(f"❌ Transaction {obj.get('id')} Failed for Order {order_id}")

        return Response({"status": "received"}, status=status.HTTP_200_OK)