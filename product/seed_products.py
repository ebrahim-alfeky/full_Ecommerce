from decimal import Decimal
import random

from product.models import (
    Category,
    Brand,
    Product,
    ProductVariant,
    Stock,
)

# ------------------ Categories ------------------

categories = {
    "Electronics": ["Mobiles", "Laptops", "Tablets"],
    "Fashion": ["Men", "Women", "Shoes"],
    "Home": ["Kitchen", "Furniture"],
    "Gaming": ["Consoles", "Accessories"],
}

category_objects = {}

for parent_name, children in categories.items():
    parent, _ = Category.objects.get_or_create(name=parent_name)
    category_objects[parent_name] = parent

    for child_name in children:
        child, _ = Category.objects.get_or_create(
            name=child_name,
            parent=parent
        )
        category_objects[child_name] = child


# ------------------ Brands ------------------

brand_names = [
    "Apple",
    "Samsung",
    "Dell",
    "HP",
    "Lenovo",
    "Asus",
    "Sony",
    "Nike",
    "Adidas",
    "Puma",
    "IKEA",
    "Tefal",
]

brands = {}

for name in brand_names:
    brands[name], _ = Brand.objects.get_or_create(name=name)


# ------------------ Products ------------------

products = [

    # Mobiles
    ("iPhone 16 Pro", "Mobiles", "Apple", 65000),
    ("Galaxy S25 Ultra", "Mobiles", "Samsung", 58000),

    # Laptops
    ("MacBook Air M4", "Laptops", "Apple", 76000),
    ("Dell XPS 15", "Laptops", "Dell", 70000),
    ("HP Victus", "Laptops", "HP", 43000),
    ("Lenovo Legion 5", "Laptops", "Lenovo", 56000),

    # Tablets
    ("iPad Air", "Tablets", "Apple", 39000),
    ("Galaxy Tab S10", "Tablets", "Samsung", 32000),

    # Gaming
    ("PlayStation 5", "Consoles", "Sony", 31000),

    # Fashion
    ("Air Max 270", "Shoes", "Nike", 6500),
    ("Ultraboost", "Shoes", "Adidas", 7200),

    # Home
    ("Dining Table", "Furniture", "IKEA", 12000),
    ("Office Chair", "Furniture", "IKEA", 4500),
    ("Non Stick Pan", "Kitchen", "Tefal", 900),
]

colors = [
    "Black",
    "White",
    "Blue",
    "Silver",
]

sizes = [
    "64GB",
    "128GB",
    "256GB",
    "512GB",
]

for name, category_name, brand_name, price in products:

    product = Product.objects.create(
        name=name,
        description=f"{name} Description",
        category=category_objects[category_name],
        brand=brands[brand_name],
    )

    # الموبايلات واللابتوبات والتابلت
    if category_name in ["Mobiles", "Laptops", "Tablets"]:

        for size in sizes:

            variant = ProductVariant.objects.create(
                product=product,
                name=size,
                sku=f"SKU-{random.randint(1000000,9999999)}",
                barcode=str(random.randint(100000000000,999999999999)),
                base_price=Decimal(price),
                discount_percent=random.choice([0,5,10,15]),
            )

            Stock.objects.create(
                variant=variant,
                quantity=random.randint(0,25),
            )

    # الأحذية
    elif category_name == "Shoes":

        for size in ["40", "41", "42", "43", "44"]:

            variant = ProductVariant.objects.create(
                product=product,
                name=f"Size {size}",
                sku=f"SKU-{random.randint(1000000,9999999)}",
                barcode=str(random.randint(100000000000,999999999999)),
                base_price=Decimal(price),
                discount_percent=random.choice([0,10,20]),
            )

            Stock.objects.create(
                variant=variant,
                quantity=random.randint(5,30),
            )

    # باقى المنتجات
    else:

        variant = ProductVariant.objects.create(
            product=product,
            name=random.choice(colors),
            sku=f"SKU-{random.randint(1000000,9999999)}",
            barcode=str(random.randint(100000000000,999999999999)),
            base_price=Decimal(price),
            discount_percent=random.choice([0,5,10]),
        )

        Stock.objects.create(
            variant=variant,
            quantity=random.randint(1,20),
        )

print("✅ Fake data inserted successfully.")