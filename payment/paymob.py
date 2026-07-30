import requests
from django.conf import settings
import time
class PaymobHelper:
    BASE_URL = "https://accept.paymob.com/v1"

    @classmethod
    def create_payment_intention(cls, order, payment_amount, shipping_address):
        url = f"{cls.BASE_URL}/intention/"
        amount_in_cents = int(float(payment_amount) * 100)
        
        # paymob_items = []
        # for item in order.items.all():
        #     paymob_items.append({
        #         "name": item.p_name, # اسم المنتج وقت الشراء
        #         "amount": int(float(item.price_at_purchase) * 100), # سعر القطعة الواحدة بالقروش
        #         "description": item.p_description[:250] if item.p_description else "No description",
        #         "quantity": item.quantity
        #     })
        billing_data = {
            "first_name": shipping_address.full_name.split()[0] if shipping_address.full_name else "NA",
            "last_name": shipping_address.full_name.split()[-1] if len(shipping_address.full_name.split()) > 1 else "NA",
            "phone_number": shipping_address.phone if shipping_address.phone else "NA",
            "email": order.user.email if (order.user and order.user.email) else "test@example.com",
            # "street": shipping_address.street if shipping_address.street else "NA",
            # "building": shipping_address.postal_code if shipping_address.postal_code else "NA", # لأنك خزنت الـ building_number في حقل postal_code جوه الـ OrderAddress
            # "city": shipping_address.city if shipping_address.city else "Cairo",
            # "country": "EG", # باي موب بيفضل كود الدول الثنائي (EG)
        }
        
        
        payload = {
            "amount": amount_in_cents,
            "currency": "EGP",
            "payment_methods": [
                int(settings.PAYMOB_INTEGRATION_ID) # رقم الـ Integration ID من الـ settings
            ],
            # "items": paymob_items,
            "billing_data": billing_data,
            # "special_reference": order.order_number, # بنربطه برقم الأوردر بتاعنا
            "redirection_url": settings.PAYMOB_REDIRECTION_URL, # هيروح فين بعد ما يخلص دفع
        }
        
        
        headers = {
            "Authorization": f"Token {settings.PAYMOB_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json() # بنرجع الـ Response الكامل لو نجح
        except requests.exceptions.RequestException as e:
            print(f"Paymob Intention Error: {e}")
            if e.response is not None:
                print(f"Response Error Body: {e.response.text}")
            return None