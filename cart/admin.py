from django.contrib import admin
from .models import Cart, CartItem

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_quantity', 'total_price', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product_variant', 'quantity', 'total_price', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('product_variant__product__name', 'cart__user__username')
    readonly_fields = ('added_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cart', 'product_variant')