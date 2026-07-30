import pytest
from rest_framework.test import APIClient
from .models import Product

@pytest.mark.django_db
def test_products_list():
    client = APIClient()
    response = client.get("/products/")
    assert response.status_code == 200
    assert len(response.data["results"]) > 0

@pytest.mark.django_db
def test_product_has_main_and_other_images():
    client = APIClient()
    product = Product.objects.first()
    response = client.get(f"/products/{product.id}/")
    assert response.status_code == 200

    data = response.data["images"]
    assert data["main"] is not None
    assert len(data["others"]) >= 1

@pytest.mark.django_db
def test_discount_price_calculation():
    client = APIClient()
    product = Product.objects.first()
    response = client.get(f"/products/{product.id}/")
    price = response.data["price_after_discount"]
    assert price == round(product.discounted_price(), 2)
