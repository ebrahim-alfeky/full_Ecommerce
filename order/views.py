from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from cart.models import Cart, CartItem
from .models import Order, OrderItem, OrderAddress
from .serializers import OrderSerializer
from address.models import Address
from django.db import transaction
from rest_framework.exceptions import ValidationError
from django.conf import settings
from product.models import Product,ProductVariant
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ObjectDoesNotExist


class CreateOrderAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    
    #تحسب مدة انتظار  بعد ما يحصل عدد معين من المحاولات الفاشلة أو المنتهية 
    def calculate_cooling_period(self, expired_count):
        base = settings.COOLING_PERIOD_AFTER_EXPIRY
        cooling = base * (2 ** (expired_count - 1))  # exponential backoff
        max_cooling = 60 * 24 # 24 hours in minutes
        return min(cooling, max_cooling)
    
    
    def post(self, request):
        user = request.user
        
        try:
            shipping_address = request.data.get("shipping_address_id")
            shipping_address= Address.objects.get(id=shipping_address, user=user)
        except Address.DoesNotExist:
            return Response(
                {"detail": "You must have a shipping address to place an order."},
                status=status.HTTP_400_BAD_REQUEST
            )
          
            
        unpaid_order_count = Order.objects.filter(user=user, is_paid=False).exclude(payment_status='expired').count()
        if unpaid_order_count >= settings.MAX_UNPAID_ORDERS_PER_USER:
            return Response({
                "detail": f"You have reached the maximum of {settings.MAX_UNPAID_ORDERS_PER_USER} unpaid orders. please pay for existing orders before creating new ones. or wait for them to expire."
            }, status=status.HTTP_400_BAD_REQUEST)
            
            
        expired_count = Order.objects.filter(
            user = user,
            payment_status = 'expired'
        ).count()
        if expired_count > 0:
            cooling_minutes = self.calculate_cooling_period(expired_count)
            last_expired = Order.objects.filter(
                user = user,
                payment_status = 'expired'
            ).order_by('-updated_at').first()
            cooling_time = last_expired.updated_at + timedelta(minutes=cooling_minutes)
            if timezone.now() < cooling_time:
                remaining_seconds = int((cooling_time - timezone.now()).total_seconds())
                minutes, seconds = divmod(remaining_seconds, 60)

                return Response({
                    "message": (
                        f"Your recent orders have expired. To prevent system abuse, "
                        f"please wait {minutes} minutes and {seconds} seconds before placing a new order."
                    ),
                    "retry_after_seconds": remaining_seconds,
                    "cooling_period_minutes": minutes,
                    "cooling_period_seconds": seconds
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
                
                
        cart = get_object_or_404(Cart, user=user)
        cart_items = cart.items.select_related("product_variant","product_variant__product").all()
        if not cart_items.exists():
            return Response({"detail": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with transaction.atomic():
                product_variant_ids = [item.product_variant.id for item in cart.items.all()]
                product_variants = (
                    ProductVariant.objects
                    .select_related("stock")      # يحمل الـ Stock مع الـ Variant
                    .select_for_update()
                    .filter(id__in=product_variant_ids)
                )
                product_variant_map = {p.id: p for p in product_variants}
                
                
                payment_method = request.data.get("payment_method", "")
                print(payment_method)
                print(type(payment_method))
                method_key = request.data.get('payment_method', '').upper()
                if method_key not in [k[0] for k in settings.AVAILABLE_PAYMENT_METHODS]:
                    return Response({"detail": "Invalid payment method."}, status=status.HTTP_400_BAD_REQUEST)
                
                order = Order.objects.create(
                    user = user,
                    payment_method = method_key
                )
                OrderAddress.objects.create(
                    order=order,
                    label = shipping_address.label,
                    full_name = shipping_address.full_name,
                    phone = shipping_address.phone,
                    street = shipping_address.street,
                    city = shipping_address.city,
                    postal_code = shipping_address.building_number,
                    country = shipping_address.country
                )
                
                order_items = []
                for item in cart_items :
                    product_variant = product_variant_map[item.product_variant.id]
                    if not product_variant:
                        raise ValidationError(f"Product variant {item.product_variant.id} no longer exists.")
                    
                    if item.quantity > settings.MAX_QTY_PER_ITEM:
                        raise ValidationError( f"The maximum quantity per product is {settings.MAX_QTY_PER_ITEM}.")
                    
                    try:
                        stock = product_variant.stock
                    except ObjectDoesNotExist:
                        raise ValidationError({
                            "detail": f"Stock record not found for variant {product_variant.id}."
                        })
                    
                    if stock.quantity < item.quantity:
                        raise ValidationError(
                            {"detail": f"Only {product_variant.stock.quantity} items available in stock for product {product_variant.name}."}
                        )
                        
                    if item.quantity < 1:
                        raise ValidationError("Invalid quantity.")
                    
                    stock.quantity -= item.quantity
                    stock.save()
                    main_image = product_variant.product.images.filter(is_main=True).first()
                    order_items.append(OrderItem(
                        order = order ,
                        product = product_variant,
                        p_name = product_variant.product.name,
                        p_description = product_variant.product.description,
                        variant_name = product_variant.name,
                        p_image = main_image.image if main_image else None,
                        quantity = item.quantity,
                        price_at_purchase = product_variant.discounted_price
                    ))
                OrderItem.objects.bulk_create(order_items)
                order.calculate_total()
                cart_items.delete()

                serializer = OrderSerializer(order)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)


class UserOrdersAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        # جلب جميع الأوردرات الخاصة بالمستخدم، ترتيب من الأحدث
        orders = Order.objects.filter(user=user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class PaymentMethodsAPIView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]  # لو عايز أي حد يشوفها

    def get(self, request):
        # إرجاع قائمة الـ choices
        methods = getattr(settings, "AVAILABLE_PAYMENT_METHODS", [
            ("COD", "Cash on Delivery"),
            ("EPAY", "E-payment"),
        ])
        return Response([
            {"value": key, "display": label} for key, label in methods
        ], status=status.HTTP_200_OK)