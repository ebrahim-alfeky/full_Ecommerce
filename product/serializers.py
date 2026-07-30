from rest_framework import serializers
from .models import Category, Brand, Product, ProductImage, ProductVariant, Stock





class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = '__all__'
        

class ProductImageSerializerNesting(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', ]

    # def to_representation(self, instance):
    #     data = super().to_representation(instance)

    #     # لو is_main = False -> نحذف الحقل من الـ response
    #     if data.get("is_main") is False:
    #         data.pop("is_main")

    #     return data


class StockSerializerNesting(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ["quantity", "low_stock_threshold"]


class ProductVariantSerializer(serializers.ModelSerializer):
    stock = StockSerializerNesting(read_only=True)
    price = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "name",
            "sku",
            "barcode",
            "is_active",
            "stock",
            "price",
        ]

    def get_price(self, obj):
        if obj.discount_percent > 0:
            return {
                "base_price": obj.base_price,
                "discount_percent": obj.discount_percent,
                "final_price": obj.discounted_price,
            }

        return {
            "final_price": obj.base_price
        }

class ProductSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "category",
            "brand",
            "is_active",
            "created_at",
            "updated_at",
            "images",
            "variants",
        ]
    
    def get_images(self, obj):
        # نجيب الصورة الرئيسية
        main_image = obj.images.filter(is_main=True).first()
        main = ProductImageSerializerNesting(main_image).data if main_image else None

        # نجيب الباقي
        others_qs = obj.images.filter(is_main=False)
        others = ProductImageSerializerNesting(others_qs, many=True).data

        return {
            "main": main,
            "others": others
        }

    


class ProductVariantSerializerNesting(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "name",
            "sku",
            "barcode",
            "is_active",
            "price",
        ]

    def get_price(self, obj):
        if obj.discount_percent > 0:
            return {
                "base_price": obj.base_price,
                "discount_percent": obj.discount_percent,
                "final_price": obj.discounted_price,
            }
        return {
            "final_price": obj.base_price
        }

class StockSerializer(serializers.ModelSerializer):
    variant = ProductVariantSerializerNesting(read_only=True)

    class Meta:
        model = Stock
        fields = '__all__'


class ProductSerializerNesting(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "is_active",
            "variants",
        ]
        

class CategorySerializer(serializers.ModelSerializer):
    products = ProductSerializerNesting(many=True, read_only=True)

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "parent",
            "products",
        ]
        

class BrandSerializer(serializers.ModelSerializer):
    products = ProductSerializerNesting(many=True, read_only=True)

    class Meta:
        model = Brand
        fields = [
            "id",
            "name",
            "logo",
            "products",
        ]