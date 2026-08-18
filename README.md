🛒 Full E-Commerce API System

A **production-oriented e-commerce REST API** built with **Django REST Framework**, designed to provide a complete backend shopping experience.

The system includes **JWT authentication, product catalog management, shopping cart, order processing, address management, reviews, Cash on Delivery, Paymob online payments, Redis, and Celery background tasks**.

The API uses **HTTP-Only Cookies** for JWT storage and implements security mechanisms such as **CSRF protection, token blacklisting, HMAC webhook verification, atomic database transactions, stock validation, and order expiration handling**.

---

## 📋 Table of Contents

* [Overview](#-overview)
* [Key Features](#-key-features)
* [Technology Stack](#-technology-stack)
* [Architecture](#-architecture)
* [Project Structure](#-project-structure)
* [Installation &amp; Setup](#-installation--setup)
* [Environment Variables](#-environment-variables)
* [API Endpoints](#-api-endpoints)
* [API Usage Examples](#-api-usage-examples)
* [Order &amp; Payment Workflow](#-order--payment-workflow)
* [Celery Background Tasks](#-celery-background-tasks)
* [Database Design](#-database-design)
* [Security](#-security)
* [Troubleshooting](#-troubleshooting)
* [Dependencies](#-dependencies)
* [Contributing](#-contributing)
* [License](#-license)
* [Author](#-author)

---

# 📌 Overview

This project is a complete **e-commerce backend API** built with Django REST Framework.

It provides the main backend components required by a modern online store:

* User authentication and account management
* Product catalog
* Product variants
* Inventory management
* Shopping cart
* Address management
* Order processing
* Cash on Delivery
* Online payments through Paymob
* Payment webhooks
* Product reviews and ratings
* Background processing with Celery
* Redis message broker
* Filtering, searching, and pagination

The application is designed around **RESTful APIs, modular Django applications, database transactions, and secure authentication**.

---

# ✨ Key Features

## 🔐 Authentication & User Management

* JWT authentication using **SimpleJWT**
* Access and refresh tokens stored in **HTTP-Only Cookies**
* Custom JWT authentication class
* Email verification
* Verification-code expiration
* Password reset using email codes
* Password change with token invalidation
* Email change with verification
* Google OAuth2 login/signup
* Account deletion with password confirmation
* CSRF protection for cookie-based authentication
* Token blacklisting on logout and sensitive operations

---

## 📦 Product Catalog

### Categories

* Category management
* Parent/child category hierarchy
* Hierarchical product organization

### Brands

* Brand management
* Brand logos

### Products

* Product information
* Product descriptions
* Active/inactive products
* Category and brand relationships

### Product Variants

Each product can have multiple variants such as:

* Size
* Color
* SKU
* Barcode
* Price
* Discount

Each variant maintains its own inventory information.

### Product Images

* Multiple images per product
* Main image designation
* Additional product images

---

## 📊 Inventory Management

The inventory system provides:

* Stock tracking per product variant
* Available quantity validation
* Low-stock thresholds
* Automatic stock creation for new variants
* Automatic product deactivation when inventory reaches zero
* Stock deduction during order creation
* Stock restoration when eligible orders expire
* Atomic stock operations to prevent inconsistent inventory

---

## 🛒 Shopping Cart

Users can:

* Add products to cart
* Update item quantities
* Remove individual items
* Clear the cart
* View cart contents
* View cart totals

The cart validates available stock before accepting quantities.

### Cart Summary

The API provides:

* Total quantity
* Total price
* Individual item totals

Each user has a persistent cart.

---

## 📋 Order Management

The order system supports:

* Creating orders from cart items
* Multiple payment methods
* Automatic order number generation
* Shipping-address snapshots
* Automatic stock deduction
* Maximum unpaid-order limits
* Order expiration
* Stock restoration after eligible expiration
* Order history
* Payment status tracking

### Payment Methods

```text
COD
EPAY
```

### Order Statuses

```text
pending
unpaid
paid
expired
```

### Order Number Format

```text
ORD-YYYYMMDD-XXXX
```

---

# 💳 Payment Integration

The system integrates with **Paymob** for online payments.

### Payment Features

* Payment initialization
* Payment intent creation
* Payment link generation
* Payment status tracking
* Payment expiration
* Payment receipt page
* Paymob webhook handling
* HMAC signature verification
* Failed payment handling
* Canceled payment handling
* Successful payment processing
* COD orders without requiring an online payment object

### Payment Statuses

```text
pending
success
failed
canceled
```

### Payment Link Lifetime

Online payment links are configured with a **10-minute lifetime**.

This is separate from the **EPAY order expiration period**, which is configured independently.

---

# 🏠 Address Management

Authenticated users can manage their shipping addresses.

Supported operations:

* Create address
* Retrieve addresses
* Update address
* Delete address
* Set default address
* Retrieve individual address

### Address Features

* Unique labels per user
* Default address support
* Ownership validation
* Address snapshotting during order creation

The order stores a snapshot of the shipping address so later changes to the user's address do not modify historical orders.

---

# ⭐ Reviews & Ratings

The review system supports:

* Create reviews
* Update reviews
* Delete reviews
* Product review listing
* User review history
* 1–5 star rating system
* One review per user per product

---

# 🔎 Filtering, Search & Pagination

Product APIs support:

* Filtering
* Searching
* Pagination

Filtering is implemented using **django-filter**.

This allows clients to efficiently query the product catalog without retrieving unnecessary records.

---

# ⚙️ Background Processing

The project uses **Celery** with **Redis** for asynchronous and scheduled background tasks.

Background jobs handle operations such as:

* Expiring unpaid orders
* Restoring stock after order expiration
* Expiring pending payments
* Other scheduled maintenance tasks

This keeps time-consuming and scheduled operations outside the main request-response cycle.

---

# 🛠️ Technology Stack

| Category              | Technology                                     |
| --------------------- | ---------------------------------------------- |
| Backend Framework     | Django 5.2.8                                   |
| API Framework         | Django REST Framework 3.16.0                   |
| Authentication        | SimpleJWT                                      |
| Database              | SQLite / PostgreSQL recommended for production |
| Task Queue            | Celery                                         |
| Message Broker        | Redis                                          |
| Payment Gateway       | Paymob                                         |
| Email                 | SMTP                                           |
| Social Authentication | Google OAuth2                                  |
| Filtering             | django-filter                                  |
| CORS                  | django-cors-headers                            |
| Configuration         | python-decouple                                |
| HTTP Requests         | Requests                                       |
| Image Processing      | Pillow                                         |

---

# 🏗️ Architecture

The project follows a modular Django architecture where each major business domain is isolated into its own application.

```text
                        ┌──────────────────────┐
                        │      Frontend        │
                        └──────────┬───────────┘
                                   │
                                   ▼
                        ┌──────────────────────┐
                        │    Django REST API   │
                        └──────────┬───────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
          ▼                        ▼                        ▼
    Authentication            Product Catalog          Shopping Cart
          │                        │                        │
          └────────────────────────┼────────────────────────┘
                                   │
                                   ▼
                           Order Management
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
                 Paymob                     PostgreSQL/SQLite
                    │
                    ▼
               Webhook/HMAC
                    │
                    ▼
              Payment Processing

                    ┌──────────────────┐
                    │      Redis       │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │     Celery       │
                    │ Worker + Beat    │
                    └──────────────────┘
```

---

# 📁 Project Structure

```text
ebrahim-alfeky-full_ecommerce/
│
├── manage.py
├── requirements.txt
├── .env
├── .gitignore
│
├── auth_system/
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── authentication.py
│   ├── utils.py
│   └── migrations/
│
├── product/
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── filters.py
│   ├── pagination.py
│   ├── signals.py
│   ├── seed_products.py
│   └── migrations/
│
├── cart/
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── signals.py
│   ├── utils.py
│   └── migrations/
│
├── order/
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── tasks.py
│   └── migrations/
│
├── payment/
│   ├── models.py
│   ├── views.py
│   ├── paymob.py
│   ├── tasks.py
│   └── migrations/
│
├── address/
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── permissions.py
│   └── migrations/
│
├── reviews/
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   └── migrations/
│
└── project/
    ├── settings.py
    ├── urls.py
    ├── celery.py
    ├── asgi.py
    └── wsgi.py
```

---

# 🚀 Installation & Setup

## 1. Clone the Repository

```bash
git clone <repository-url>
cd ebrahim-alfeky-full_ecommerce
```

---

## 2. Create Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
DJANGO_ENV=development


# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com


# Google OAuth2
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google-callback/


# Paymob
PAYMOB_INTEGRATION_ID=your-integration-id
PAYMOB_SECRET_KEY=your-secret-key
PAYMOB_PUBLIC_KEY=your-public-key
PAYMOB_REDIRECTION_URL=http://localhost:8000/payment/receipt/
PAYMOB_HMAC_TOKEN=your-hmac-token


# Redis
REDIS_URL=redis://localhost:6379/0
```

> ⚠️ Never commit `.env` to Git.

---

## 5. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 6. Create Superuser

```bash
python manage.py createsuperuser
```

---

## 7. Seed Demo Products

If the project includes the product seeding script:

```bash
python manage.py shell
```

Then execute the seeding logic from:

```text
product/seed_products.py
```

---

## 8. Start Redis

Make sure Redis is running:

```bash
redis-server
```

Or use your system/service-specific Redis setup.

---

## 9. Start Celery Worker

Open a separate terminal:

```bash
celery -A project worker --loglevel=info
```

---

## 10. Start Celery Beat

Open another terminal:

```bash
celery -A project beat --loglevel=info
```

---

## 11. Run Django

```bash
python manage.py runserver
```

---

# 📡 API Endpoints

## 🔐 Authentication

| Method | Endpoint                        | Description              | Auth |
| ------ | ------------------------------- | ------------------------ | ---- |
| POST   | `/auth/signup/`               | Register account         | ❌   |
| POST   | `/auth/verify-email/`         | Verify email             | ❌   |
| POST   | `/auth/resend-code/`          | Resend verification code | ❌   |
| POST   | `/auth/login/`                | Login                    | ❌   |
| POST   | `/auth/refresh-access-token/` | Refresh access token     | ❌   |
| POST   | `/auth/verify-access-token/`  | Validate access token    | ❌   |
| POST   | `/auth/logout/`               | Logout                   | ✅   |
| DELETE | `/auth/delete/`               | Delete account           | ✅   |
| POST   | `/auth/forget-password/`      | Request password reset   | ❌   |
| POST   | `/auth/rest-password/`        | Reset password           | ❌   |
| POST   | `/auth/change-password/`      | Change password          | ✅   |
| PUT    | `/auth/update-account/`       | Update profile           | ✅   |
| POST   | `/auth/change-email/`         | Request email change     | ✅   |
| POST   | `/auth/verify-change-email/`  | Verify new email         | ✅   |
| POST   | `/auth/google-login/`         | Google OAuth2 login      | ❌   |
| GET    | `/auth/me/`                   | Current user             | ✅   |
| GET    | `/auth/csrf/`                 | Get CSRF cookie          | ❌   |

---

# 📦 Product API

## Categories

| Method | Endpoint                      | Description      |
| ------ | ----------------------------- | ---------------- |
| GET    | `/product/categories/`      | List categories  |
| GET    | `/product/categories/{id}/` | Category details |

## Brands

| Method | Endpoint                  | Description   |
| ------ | ------------------------- | ------------- |
| GET    | `/product/brands/`      | List brands   |
| GET    | `/product/brands/{id}/` | Brand details |

## Products

| Method | Endpoint                    | Description          |
| ------ | --------------------------- | -------------------- |
| GET    | `/product/products/`      | List active products |
| GET    | `/product/products/{id}/` | Product details      |

## Variants

| Method | Endpoint                    | Description          |
| ------ | --------------------------- | -------------------- |
| GET    | `/product/variants/`      | List active variants |
| GET    | `/product/variants/{id}/` | Variant details      |

## Images & Stock

| Method | Endpoint                     | Description    |
| ------ | ---------------------------- | -------------- |
| GET    | `/product/product-images/` | Product images |
| GET    | `/product/stocks/`         | Stock records  |

---

# 🛒 Cart API

| Method | Endpoint                   | Description        | Auth |
| ------ | -------------------------- | ------------------ | ---- |
| GET    | `/cart/cart/`            | Get user's cart    | ✅   |
| POST   | `/cart/cart/`            | Add item           | ✅   |
| PUT    | `/cart/cart/`            | Update quantity    | ✅   |
| DELETE | `/cart/cart/`            | Remove/clear items | ✅   |
| GET    | `/cart/items/{item_id}/` | Get cart item      | ✅   |
| GET    | `/cart/summary/`         | Cart summary       | ✅   |

---

# 🏠 Address API

| Method | Endpoint                     | Description     | Auth |
| ------ | ---------------------------- | --------------- | ---- |
| GET    | `/address/addresses/`      | List addresses  | ✅   |
| POST   | `/address/addresses/`      | Create address  | ✅   |
| GET    | `/address/addresses/{id}/` | Address details | ✅   |
| PUT    | `/address/addresses/{id}/` | Update address  | ✅   |
| PATCH  | `/address/addresses/{id}/` | Partial update  | ✅   |
| DELETE | `/address/addresses/{id}/` | Delete address  | ✅   |

---

# 📋 Order API

| Method | Endpoint                    | Description               | Auth |
| ------ | --------------------------- | ------------------------- | ---- |
| POST   | `/order/create-order/`    | Create order from cart    | ✅   |
| GET    | `/order/get-orders/`      | Get user's orders         | ✅   |
| GET    | `/order/payment-methods/` | Available payment methods | ❌   |

---

# 💳 Payment API

| Method | Endpoint                          | Description      | Auth |
| ------ | --------------------------------- | ---------------- | ---- |
| POST   | `/payment/initiate/{order_id}/` | Initiate payment | ✅   |
| GET    | `/payment/receipt/`             | Payment receipt  | ❌   |
| POST   | `/payment/webhook/`             | Paymob webhook   | ❌   |

The webhook endpoint does not rely on CSRF authentication because it is called by the payment provider. Instead, the request is validated using **HMAC verification**.

---

# ⭐ Reviews API

| Method | Endpoint                                    | Description     | Auth |
| ------ | ------------------------------------------- | --------------- | ---- |
| GET    | `/reviews/products/reviews/`              | User's reviews  | ✅   |
| GET    | `/reviews/products/{product_id}/reviews/` | Product reviews | ✅   |
| POST   | `/reviews/products/{product_id}/reviews/` | Create review   | ✅   |
| PUT    | `/reviews/products/{product_id}/reviews/` | Update review   | ✅   |
| DELETE | `/reviews/products/{product_id}/reviews/` | Delete review   | ✅   |

---

# 📝 API Usage Examples

## Signup

```http
POST /auth/signup/
Content-Type: application/json
```

```json
{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "role": "buyer",
    "phone": "+1234567890"
}
```

---

## Login

```http
POST /auth/login/
Content-Type: application/json
```

```json
{
    "username": "john_doe",
    "password": "SecurePass123!"
}
```

The API sets the following cookies automatically:

```text
access_token
refresh_token
```

Both are configured as **HTTP-Only cookies**.

---

## Add Product to Cart

```http
POST /cart/cart/
Content-Type: application/json
Cookie: access_token=<jwt-token>
```

```json
{
    "product_variant_id": "123e4567-e89b-12d3-a456-426614174000",
    "quantity": 2
}
```

---

## Create Order

```http
POST /order/create-order/
Content-Type: application/json
Cookie: access_token=<jwt-token>
```

```json
{
    "shipping_address_id": 1,
    "payment_method": "EPAY"
}
```

The order creation process:

```text
Validate Authentication
        ↓
Validate Cart
        ↓
Validate Address
        ↓
Validate Stock
        ↓
Calculate Total
        ↓
Create Order
        ↓
Snapshot Address
        ↓
Create Order Items
        ↓
Deduct Stock
        ↓
Clear Cart
```

These operations are performed using database transactions to maintain consistency.

---

## Initiate Online Payment

```http
POST /payment/initiate/1/
Cookie: access_token=<jwt-token>
```

The API returns a Paymob payment URL.

---

## Create Review

```http
POST /reviews/products/1/reviews/
Content-Type: application/json
Cookie: access_token=<jwt-token>
```

```json
{
    "rating": 5,
    "comment": "Excellent product, very satisfied!"
}
```

---

# 🔄 Order & Payment Workflow

## EPAY Flow

```text
Create Order
     ↓
Stock Validation
     ↓
Stock Deduction
     ↓
Order = Unpaid
     ↓
Initiate Paymob Payment
     ↓
Generate Payment Link
     ↓
Customer Pays
     ↓
Paymob Webhook
     ↓
HMAC Verification
     ↓
Update Payment
     ↓
Update Order → Paid
```

If the payment is not completed within the configured order expiration period, the order can be expired and its reserved stock restored.

---

## COD Flow

```text
Create Order
     ↓
Stock Validation
     ↓
Stock Deduction
     ↓
Order = Unpaid
     ↓
No Online Payment Required
     ↓
Order Remains Active
     ↓
Expires After Configured Period
```

When an eligible COD order expires, its stock is restored.

---

# ⚙️ Configuration

## JWT & Cookies

```python
ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"

ACCESS_COOKIE_MAX_AGE = 60 * 5
REFRESH_COOKIE_MAX_AGE = 7 * 24 * 3600

COOKIE_HTTPONLY = True
COOKIE_SAMESITE = "Lax"

# Development
COOKIE_SECURE = False

# Production
# COOKIE_SECURE = True
```

---

## Order Configuration

```python
MAX_UNPAID_ORDERS_PER_USER = 3
MAX_QTY_PER_ITEM = 15

ORDER_EXPIRE_MINUTES = 15
COD_ORDER_EXPIRE_DAYS = 3

PAYMENT_LINK_LIFETIME_SECONDS = 600

COOLING_PERIOD_AFTER_EXPIRY = 10
```

---

## Celery Configuration

```python
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
```

---

# 🗄️ Database Design

## User

Main fields:

```text
username
email
password
role
phone
is_active
```

Relationships:

```text
User
 ├── Cart
 ├── Orders
 ├── Addresses
 └── Reviews
```

---

## Product

```text
Product
 ├── Category
 ├── Brand
 ├── ProductVariant
 └── ProductImage
```

---

## ProductVariant

Main fields:

```text
name
sku
barcode
base_price
discount_percent
is_active
```

Calculated property:

```text
discounted_price
```

Relationship:

```text
ProductVariant ─── Stock
```

---

## Cart

```text
Cart
 └── CartItem
       └── ProductVariant
```

The cart provides calculated:

```text
total_price
total_quantity
```

---

## Order

```text
Order
 ├── User
 ├── OrderAddress
 └── OrderItem
       └── ProductVariant
```

Order statuses:

```text
pending
unpaid
paid
expired
```

---

## Payment

```text
Payment
 ├── Order
 └── User
```

Main fields:

```text
amount
status
provider
provider_payment_id
payment_url
```

Payment statuses:

```text
pending
success
failed
canceled
```

---

# 🔄 Celery Background Tasks

## `clean_unpaid_orders`

Runs periodically through **Celery Beat**.

Responsibilities include:

* Detect expired unpaid orders
* Expire eligible COD orders
* Expire eligible EPAY orders
* Restore reserved stock
* Update order status

---

## `expire_pending_payments`

Runs periodically and:

* Finds pending payments
* Checks payment lifetime
* Marks expired payments as canceled

---

# 🛡️ Security

The application implements multiple security mechanisms.

### JWT Security

* HTTP-Only cookies
* Refresh token rotation
* Token blacklisting
* Token invalidation after sensitive operations

### Cookie Security

Production configuration should use:

```python
COOKIE_HTTPONLY = True
COOKIE_SECURE = True
COOKIE_SAMESITE = "Lax"
```

### CSRF Protection

Because authentication uses cookies, CSRF protection is implemented for browser-originated authenticated requests.

Payment webhooks are handled separately and validated using **HMAC signatures**.

### Payment Security

Paymob callbacks are verified using:

```text
HMAC verification
```

This prevents unauthorized requests from being treated as valid payment notifications.

### Database Consistency

Critical operations such as order creation and stock modification use **atomic database transactions**.

This helps prevent situations where:

```text
Order created
but stock was not deducted
```

or:

```text
Stock deducted
but order creation failed
```

---

### Authentication

* Signup
* Email verification
* Login
* JWT authentication
* Refresh token
* Logout
* Password reset
* Password change
* Email change
* Account deletion

### Products

* Product retrieval
* Variant retrieval
* Filtering
* Searching
* Pagination
* Stock validation

### Cart

* Add item
* Update quantity
* Remove item
* Stock limits
* Cart totals

### Orders

* Order creation
* Stock deduction
* Address snapshot
* Unpaid order limits
* Order expiration
* Stock restoration

### Payments

* Payment initialization
* Webhook validation
* HMAC verification
* Successful payment
* Failed payment
* Payment expiration

### Reviews

* Create review
* Update review
* Delete review
* One-review-per-user constraint

---

# 🐛 Troubleshooting

## Email Verification

If verification fails:

* Check SMTP credentials.
* Check that the account is inactive until verification.
* Request a new verification code.
* Check the code expiration time.

---

## Maximum Unpaid Orders

If the API returns:

```text
You have reached the maximum of 3 unpaid orders.
```

The user must:

* Complete an existing payment
* Wait for eligible orders to expire

---

## Insufficient Stock

If an order cannot be created:

* Check the variant's available stock.
* Reduce the requested quantity.
* Select another variant.

---

## Paymob HMAC Mismatch

Check:

* `PAYMOB_HMAC_TOKEN`
* Webhook configuration
* HMAC calculation
* Incoming webhook payload

---

## Celery Tasks Not Running

Make sure Redis is running:

```bash
redis-server
```

Then start the worker:

```bash
celery -A project worker --loglevel=info
```

And Celery Beat:

```bash
celery -A project beat --loglevel=info
```

---

# 🔒 Production Checklist

Before deploying:

* [ ] Set `DEBUG=False`
* [ ] Use HTTPS
* [ ] Set `COOKIE_SECURE=True`
* [ ] Keep secrets in environment variables
* [ ] Never commit `.env`
* [ ] Use PostgreSQL or another production-grade database
* [ ] Configure production CORS origins
* [ ] Configure secure email credentials
* [ ] Configure Paymob production credentials
* [ ] Run Redis securely
* [ ] Run Celery Worker
* [ ] Run Celery Beat
* [ ] Configure proper logging
* [ ] Configure monitoring
* [ ] Keep dependencies updated
* [ ] Verify payment webhooks
* [ ] Verify HMAC validation
* [ ] Run automated tests before deployment

---

# 📦 Dependencies

```text
Django==5.2.8
djangorestframework==3.16.0
djangorestframework-simplejwt==5.5.0
django-cors-headers==4.7.0
django-filter==25.1
python-decouple==3.8
django-environ==0.12.0
requests==2.32.4
google-auth==2.40.1
celery==5.5.1
redis==5.2.1
django-celery-beat==2.7.0
django-celery-results==2.5.1
Pillow==11.3.0
```

---

# 🤝 Contributing

1. Fork the repository.
2. Create a feature branch:

```bash
git checkout -b feature/amazing-feature
```

3. Commit your changes:

```bash
git commit -m "Add amazing feature"
```

4. Push the branch:

```bash
git push origin feature/amazing-feature
```

5. Open a Pull Request.

---

# 📄 License

This project is proprietary and confidential.

---

# 👨‍💻 Author

**Ebrahim Alfeky**

Backend Developer — Django & REST APIs

---

# 🙏 Acknowledgments

* Django
* Django REST Framework
* SimpleJWT
* Celery
* Redis
* Paymob
* Google OAuth2
* django-filter
