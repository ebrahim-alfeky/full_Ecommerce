from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Cart, CartItem
from .serializers import (
    CartSerializer, 
    CartItemSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer
)
from product.models import ProductVariant, Stock
from django.core.exceptions import ObjectDoesNotExist


class CartAPIView(APIView):
    """Main cart API - Only for authenticated users"""
    permission_classes = [IsAuthenticated]
    
    def get_cart(self, request):
        """Get or create user's cart"""
        cart, created = Cart.objects.get_or_create(user=request.user)
        return cart
    
    def get(self, request):
        """Get cart details"""
        cart = self.get_cart(request)
        serializer = CartSerializer(cart)
        return Response({
            'success': True,
            'cart': serializer.data
        })
    
    def post(self, request):
        """Add item to cart"""
        serializer = AddToCartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        variant_id = serializer.validated_data['product_variant_id']
        quantity = serializer.validated_data['quantity']
        
        try:
            cart = self.get_cart(request)
            
            product_variant = ProductVariant.objects.get(
                id=variant_id,
                is_active=True
            )
            try:
                stock = product_variant.stock
            except ObjectDoesNotExist:
                return Response(
                    {
                        "success": False,
                        "error": "This product has no stock record."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check stock availability
            if quantity > stock.quantity:
                return Response({
                    'success': False,
                    'error': f'Insufficient stock. Available0: {product_variant.stock.quantity}',
                    'available_stock': product_variant.stock.quantity
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Add or update item
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product_variant=product_variant,
                defaults={'quantity': quantity}
            )
            
            if not created:
                new_quantity = cart_item.quantity + quantity
                if new_quantity > product_variant.stock.quantity:
                    return Response({
                        'success': False,
                        'error': f'Insufficient stock. Available: {product_variant.stock.quantity}',
                        'available_stock': product_variant.stock.quantity
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                cart_item.quantity = new_quantity
                cart_item.save()
            
            return Response({
                'success': True,
                'message': 'Product added to cart successfully',
                'cart_item': CartItemSerializer(cart_item).data,
                'cart_summary': {
                    'total_price': cart.total_price,
                    'total_quantity': cart.total_quantity
                }
            }, status=status.HTTP_201_CREATED)
            
        except ProductVariant.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Product variant not found or inactive'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request):
        """Update cart item quantity"""
        serializer = AddToCartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        variant_id = serializer.validated_data['product_variant_id']
        quantity = serializer.validated_data['quantity']
        
        try:
            cart = self.get_cart(request)
            cart_item = CartItem.objects.get(
                cart=cart,
                product_variant_id=variant_id
            )
            
            product_variant = cart_item.product_variant
            stock = Stock.objects.filter(variant=product_variant).first()
            if stock is None:
                return Response(
                    {
                        "success": False,
                        "error": "This product has no stock record."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check stock
            if quantity > stock.quantity:
                return Response({
                    'success': False,
                    'error': f'Insufficient stock. Available: {product_variant.stock.quantity}',
                    'available_stock': product_variant.stock.quantity
                }, status=status.HTTP_400_BAD_REQUEST)
            
            cart_item.quantity = quantity
            cart_item.save()
            
            return Response({
                'success': True,
                'message': 'Cart item updated successfully',
                'cart_item': CartItemSerializer(cart_item).data,
                'cart_summary': {
                    'total_price': cart.total_price,
                    'total_quantity': cart.total_quantity
                }
            })
            
        except CartItem.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Product not found in cart'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request):
        """Remove item from cart or clear cart"""
        variant_id = request.data.get('product_variant_id')
        cart = self.get_cart(request)
        
        if variant_id:
            try:
                cart_item = CartItem.objects.get(
                    cart=cart,
                    product_variant_id=variant_id
                )
                product_name = cart_item.product_variant.product.name
                cart_item.delete()
                
                return Response({
                    'success': True,
                    'message': f'"{product_name}" removed from cart',
                    'cart_summary': {
                        'total_price': cart.total_price,
                        'total_quantity': cart.total_quantity
                    }
                })
                
            except CartItem.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Product not found in cart'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            cart.clear()
            return Response({
                'success': True,
                'message': 'Cart cleared successfully'
            })


class CartItemDetailAPIView(APIView):
    """Individual cart item operations"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, item_id):
        """Get specific cart item details"""
        try:
            cart = Cart.objects.get(user=request.user)
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            serializer = CartItemSerializer(cart_item)
            return Response({
                'success': True,
                'item': serializer.data
            })
        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            return Response({
                'success': False,
                'error': 'Cart item not found'
            }, status=status.HTTP_404_NOT_FOUND)


class CartSummaryAPIView(APIView):
    """Get cart summary only"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        cart = Cart.objects.get(user=request.user)
        return Response({
            'success': True,
            'summary': {
                'total_items': cart.total_quantity,
                'total_price': float(cart.total_price),
                'item_count': cart.items.count()
            }
        })