from django.db import transaction
from .models import Cart, CartItem

def add_to_cart_safely(user, product_variant, quantity=1):
    """Safe method to add item to cart with stock validation"""
    with transaction.atomic():
        cart, _ = Cart.objects.get_or_create(user=user)
        
        # Check stock
        if quantity > product_variant.stock.quantity:
            return None, f"Insufficient stock. Available: {product_variant.stock.quantity}"
        
        # Add or update item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product_variant=product_variant,
            defaults={'quantity': quantity}
        )
        
        if not created:
            new_quantity = cart_item.quantity + quantity
            if new_quantity > product_variant.stock.quantity:
                return None, f"Insufficient stock. Available: {product_variant.stock.quantity}"
            cart_item.quantity = new_quantity
            cart_item.save()
        
        return cart_item, None


def get_cart_summary(user):
    """Get user's cart summary"""
    try:
        cart = Cart.objects.get(user=user)
        return {
            'success': True,
            'total_quantity': cart.total_quantity,
            'total_price': float(cart.total_price),
            'item_count': cart.items.count()
        }
    except Cart.DoesNotExist:
        return {
            'success': False,
            'error': 'Cart not found',
            'total_quantity': 0,
            'total_price': 0,
            'item_count': 0
        }


def validate_cart_items(user):
    """Validate all items in user's cart"""
    try:
        cart = Cart.objects.get(user=user)
        issues = []
        
        for item in cart.items.all():
            if not item.product_variant.is_active:
                issues.append({
                    'item_id': str(item.id),
                    'product': item.product_variant.product.name,
                    'issue': 'product_inactive',
                    'message': 'Product is no longer available'
                })
            elif item.quantity > item.product_variant.stock.quantity:
                issues.append({
                    'item_id': str(item.id),
                    'product': item.product_variant.product.name,
                    'issue': 'insufficient_stock',
                    'message': f'Requested: {item.quantity}, Available: {item.product_variant.stock.quantity}'
                })
        
        return {
            'has_issues': len(issues) > 0,
            'issues': issues,
            'cart_valid': len(issues) == 0
        }
        
    except Cart.DoesNotExist:
        return {
            'has_issues': True,
            'issues': [{'message': 'Cart not found'}],
            'cart_valid': False
        }