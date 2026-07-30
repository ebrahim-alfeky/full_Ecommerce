# views.py
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Code
from .serializers import (
    SignupSerializer,
    UserSerializer
    )
from .utils import generate_and_store_code, send_code_email, verify_code
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken,TokenError,AccessToken
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
import requests
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

User = get_user_model()

class SignupView(APIView):
    
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # حذف أي كود قديم للتحقق 1️⃣ 
            Code.objects.filter(user=user, purpose='verify_email').delete()

            # 2️⃣  إنشاء كود جديد
            code = generate_and_store_code(user, purpose='verify_email')

            # 3️⃣  إرسال الكود باستخدام الدالة العامة
            send_code_email(user.email, code, purpose='verify_email')

            return Response(
                {"message": "User registered successfully. Check your email for verification code."},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailView(APIView):
   
    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')

        # 1️⃣ التأكد من وجود المستخدم
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # 2️⃣ التحقق من الكود باستخدام الدالة utils.verify_code
        if verify_code(user, code, 'verify_email'):
            # 3️⃣ تفعيل الحساب
            user.is_active = True
            user.save()
            return Response({"message": "Email verified successfully."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid or expired code."}, status=status.HTTP_400_BAD_REQUEST)

class ResendCodeView(APIView):
    
    def post(self, request):
        email = request.data.get("email", "").strip()
        purpose = request.data.get("purpose", "").strip()

        if not email or not purpose:
            return Response({"detail": "Email and purpose are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "If this email exists, a code will be sent."}, status=status.HTTP_200_OK)

        # 1️⃣ حذف أي كود قديم لنفس المستخدم ونفس الغرض
        Code.objects.filter(user=user, purpose=purpose).delete()

        # 2️⃣ إنشاء كود جديد
        code = generate_and_store_code(user, purpose=purpose)

        # 3️⃣ إرسال الكود عبر البريد
        send_code_email(user.email, code,purpose)

        return Response({"detail": "If this email exists, a code will be sent."}, status=status.HTTP_200_OK)

class LoginView(TokenObtainPairView):
    
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # 1️⃣ جلب اسم المستخدم وكلمة المرور من الـ request
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '').strip()
        
        # 2️⃣ التحقق من وجود المستخدم
        user = User.objects.filter(username=username).first()
        if user is None or not user.check_password(password):
            return Response(
                {"detail": "Invalid username or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # 3️⃣ التأكد من تفعيل الحساب
        if not user.is_active:
            return Response(
                {
                    "detail": "Please activate your email first",
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 4️⃣ استدعاء الـ parent view لإصدار التوكنز (access + refresh)
        response = super().post(request, *args, **kwargs)
        access = response.data['access']
        refresh = response.data['refresh']
        
        # 5️⃣ حذف التوكنز من body
        response.data.pop('access', None)
        response.data.pop('refresh', None)

        # 6️⃣ وضع التوكنز في HttpOnly cookies

        # Refresh token cookie
        response.set_cookie(
            key=settings.REFRESH_COOKIE_NAME,
            value=refresh,
            httponly=settings.COOKIE_HTTPONLY,
            max_age=settings.REFRESH_COOKIE_MAX_AGE,
            samesite=settings.COOKIE_SAMESITE,
            secure=settings.COOKIE_SECURE,
            path=settings.COOKIE_PATH
        )

        # Access token cookie
        response.set_cookie(
            key=settings.ACCESS_COOKIE_NAME,
            value=access,
            httponly=settings.COOKIE_HTTPONLY,
            max_age=settings.ACCESS_COOKIE_MAX_AGE,
            samesite=settings.COOKIE_SAMESITE,
            secure=settings.COOKIE_SECURE,
            path=settings.COOKIE_PATH
        )

        # 7️⃣ إعداد بيانات المستخدم للـ response body
        user_id = AccessToken(access)['user_id']
        user = get_object_or_404(User, id=user_id)

        response.data = {
            'message': 'Logged in successfully',
            'user': UserSerializer(user).data  # استرجاع بيانات المستخدم فقط
        }

        # 8️⃣ تعديل status code
        response.status_code = status.HTTP_202_ACCEPTED

        # 9️⃣ إعادة Response جاهز
        print(response.cookies)
        return response

class RefreshAccessTokenView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        print('================')
        # 1️⃣ جلب refresh token من الكوكي
        refresh_cookie = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
        if not refresh_cookie:
            return Response(
                {'detail': 'Refresh token not found'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 2️⃣ إنشاء كائن RefreshToken من الكوكي
            old_refresh = RefreshToken(refresh_cookie)

            # 3️⃣ استخراج user_id
            user_id = old_refresh['user_id']

            # 4️⃣ جلب المستخدم من قاعدة البيانات
            user = get_object_or_404(User, id=user_id)

            # 5️⃣ توليد توكن جديد
            new_refresh = RefreshToken.for_user(user)
            new_access = new_refresh.access_token

            # 6️⃣ إعداد Response
            response = Response({
                'message': 'Tokens refreshed successfully'
            }, status=status.HTTP_200_OK)

            # 7️⃣ وضع Access token في كوكي
            response.set_cookie(
                key=settings.ACCESS_COOKIE_NAME,
                value=str(new_access),
                max_age=settings.ACCESS_COOKIE_MAX_AGE,
                httponly=settings.COOKIE_HTTPONLY,
                samesite=settings.COOKIE_SAMESITE,
                secure=settings.COOKIE_SECURE,
                path=settings.COOKIE_PATH
            )

            # 8️⃣ وضع Refresh token في كوكي
            response.set_cookie(
                key=settings.REFRESH_COOKIE_NAME,
                value=str(new_refresh),
                max_age=settings.REFRESH_COOKIE_MAX_AGE,
                httponly=settings.COOKIE_HTTPONLY,
                samesite=settings.COOKIE_SAMESITE,
                secure=settings.COOKIE_SECURE,
                path=settings.COOKIE_PATH
            )

            # 9️⃣ إرجاع Response
            return response

        except TokenError:
            return Response(
                {'detail': 'Invalid or expired refresh token'},
                status=status.HTTP_401_UNAUTHORIZED
            )

class VerifyAccessTokenView(APIView):
    
    permission_classes = [AllowAny]

    def post(self, request):
        # 1️⃣ جلب الـ access token من الكوكي
        access_cookie = request.COOKIES.get(settings.ACCESS_COOKIE_NAME)
        if not access_cookie:
            return Response(
                {"detail": "Access token not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 2️⃣ محاولة التحقق من التوكن
            token = AccessToken(access_cookie)

            # لو التوكن صالح، نقدر نقرأ user_id لو احتجنا
            user_id = token.get("user_id")

            # 3️⃣ Response النجاح
            return Response({
                "message": "Access token is valid",
                "user_id": user_id
            }, status=status.HTTP_200_OK)

        except TokenError:
            # لو التوكن منتهي أو غير صالح
            return Response(
                {"detail": "Invalid or expired access token"},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
class LogoutView(APIView):
    """
    تسجيل خروج المستخدم:
    - حذف كلا الكوكيز (access + refresh)
    - إرجاع رسالة نجاح
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        response = Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)

        # حذف Access token cookie
        response.delete_cookie(
            key=settings.ACCESS_COOKIE_NAME,
            path=settings.COOKIE_PATH
        )

        # حذف Refresh token cookie
        response.delete_cookie(
            key=settings.REFRESH_COOKIE_NAME,
            path=settings.COOKIE_PATH
        )

        return response

class DeleteAccountView(APIView):
    
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        password = request.data.get("password", "").strip()

        # 1️⃣ التحقق من كلمة المرور
        if not user.check_password(password):
            return Response(
                {"detail": "Incorrect password."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # 2️⃣ حذف المستخدم
        user.delete()

        # 3️⃣ إعداد response ومسح الكوكيز
        response = Response(
            {"message": "Account deleted successfully."},
            status=status.HTTP_200_OK
        )

        # مسح Access token
        response.delete_cookie(key=settings.ACCESS_COOKIE_NAME, path=settings.COOKIE_PATH)

        # مسح Refresh token
        response.delete_cookie(key=settings.REFRESH_COOKIE_NAME, path=settings.COOKIE_PATH)

        # 4️⃣ إعادة response
        return response

class ForgotPasswordView(APIView):
    
    def post(self, request):
        # 1️⃣ جلب البريد من request
        email = (request.data.get("email") or "").strip()
        if not email:
            return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        # 2️⃣ محاولة جلب المستخدم
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # 3️⃣ لو مش موجود، نرجع رد عام
            return Response({"detail": "User doesn't exsist."}, status=status.HTTP_200_OK)

        # 4️⃣ حذف أي أكواد سابقة لنفس الغرض
        Code.objects.filter(user=user, purpose="reset_password").delete()

        # 5️⃣ إنشاء كود جديد وتخزينه
        code = generate_and_store_code(user, purpose="reset_password")

        # 6️⃣ إرسال الكود عبر البريد
        send_code_email(user.email, code,"reset_password")

        # 7️⃣ الرد النهائي
        return Response({"detail": "If this email exists, a reset code will be sent."}, status=status.HTTP_200_OK)
    
class ResetPasswordView(APIView):
    
    def post(self, request):
        # 1️⃣ جلب البيانات من request
        email = (request.data.get("email") or "").strip()
        code = (request.data.get("code") or "").strip()
        new_password = request.data.get("new_password") or ""

        # 2️⃣ التأكد من وجود كل البيانات المطلوبة
        if not (email and code and new_password):
            return Response({"detail": "Email, code and new_password are required."}, status=status.HTTP_400_BAD_REQUEST)

        # 3️⃣ الحصول على المستخدم
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "Invalid or expired code."}, status=status.HTTP_400_BAD_REQUEST)

        # 4️⃣ التحقق من صلاحية الكود واستعمال الدالة من utils
        if not verify_code(user, code, 'reset_password'):
            return Response({"detail": "Invalid or expired code."}, status=status.HTTP_400_BAD_REQUEST)

        # 5️⃣ الكود صالح → إعادة تعيين كلمة المرور
        user.set_password(new_password)
        user.save()

        # 6️⃣ تسجيل الخروج من كل الأجهزة عن طريق blacklist
        try:
            # blacklist لكل Refresh tokens القديمة
            RefreshToken.for_user(user).blacklist()
        except AttributeError:
            # لو blacklist غير مفعل، يمكن تجاهل هذه الخطوة أو إدارة الـ tokens يدوياً
            pass

        # 7️⃣ الرد النهائي للمستخدم
        return Response(
            {"detail": "Password has been reset successfully. All sessions logged out."},
            status=status.HTTP_200_OK
        )
        
class ChangePasswordView(APIView):
    # 1) السماح فقط للمستخدمين المسجلين بالدخول
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 2) جلب البيانات من طلب المستخدم
        old_password = request.data.get("old_password") or ""
        new_password = request.data.get("new_password") or ""
        user = request.user

        # 3) التحقق من وجود كلمة المرور الجديدة
        if not new_password:
            return Response({"detail": "New password is required."}, status=400)

        # 4) إذا كان المستخدم لديه كلمة مرور أصلًا → نطلب كلمة المرور القديمة
        # has_usable_password() بتقول هل المستخدم عنده باسورد فعلي ولا لا
        if user.has_usable_password():

            # 4.1) التأكد من إرسال كلمة المرور القديمة
            if not old_password:
                return Response({"detail": "Old password is required."}, status=400)

            # 4.2) التأكد أن كلمة المرور القديمة صحيحة
            if not user.check_password(old_password):
                return Response({"detail": "Old password is incorrect."}, status=400)

        # 5) تعيين كلمة المرور الجديدة
        user.set_password(new_password)
        user.save()

        # 6) محاولة تسجيل خروج المستخدم من كل الجلسات (في حالة استخدام Refresh Tokens)
        try:
            RefreshToken.for_user(user).blacklist()
        except:
            pass  # لو نظام الـ blacklist مش مفعل نتجاهلها

        # 7) تجهيز الرد النهائي
        response = Response(
            {"detail": "Password changed successfully. Logged out from all sessions."},
            status=200
        )

        # 8) حذف كوكيز الـ Tokens لو موجودة (أمان)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

        # 9) إرسال الرد النهائي
        return response
            
class UpdateAccountView(APIView):
    """
    1️⃣ تحديث بيانات المستخدم الحالي (كل الحقول ماعدا البريد الإلكتروني)
    """
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user

        # 2️⃣ جلب البيانات الجديدة من request
        data = request.data

        # 3️⃣ تحديث الحقول المسموح بها فقط
        allowed_fields = ["username", "first_name", "last_name", "phone", "role"]  # البريد مش مسموح يتغير هنا
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])

        # 4️⃣ حفظ التغييرات في قاعدة البيانات
        user.save()

        # 5️⃣ إعادة البيانات بعد التحديث
        return Response(
            {
                "detail": "Account updated successfully.",
                "user": UserSerializer(user).data
            },
            status=status.HTTP_200_OK
        )

class ChangeEmailView(APIView):
    
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 1️⃣ جلب المستخدم والبريد الجديد من الطلب
        user = request.user
        new_email = (request.data.get("new_email") or "").strip()
        if not new_email:
            return Response({"detail": "New email is required."}, status=status.HTTP_400_BAD_REQUEST)

        # 2️⃣ التأكد من أن البريد الجديد غير مستخدم من قبل أي مستخدم آخر
        if User.objects.filter(email=new_email).exists():
            return Response({"detail": "This email is already in use."}, status=status.HTTP_400_BAD_REQUEST)

        # 3️⃣ حذف أي أكواد قديمة لنفس الغرض (لا يوجد is_used الآن)
        Code.objects.filter(user=user, purpose='change_email').delete()

        # 4️⃣ توليد كود جديد وتخزينه في DB
        code = generate_and_store_code(user, purpose='change_email')

        # 5️⃣ إرسال الكود إلى البريد الجديد باستخدام send_verification_email
        send_code_email(new_email, code, 'change_email')

        # 6️⃣ رد عام بأن الكود اترسل
        return Response({"detail": f"Verification code sent to {new_email}."}, status=status.HTTP_200_OK)

class VerifyChangeEmailView(APIView):
    
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 1️⃣ جلب المستخدم والبيانات
        user = request.user
        new_email = (request.data.get("new_email") or "").strip()
        code = (request.data.get("code") or "").strip()

        # 2️⃣ تحقق من توافر الحقول
        if not (new_email and code):
            return Response({"detail": "New email and code are required."}, status=status.HTTP_400_BAD_REQUEST)

        # 3️⃣ التحقق من الكود عبر الدالة الموحدة (ترجع True/False وتقوم بحذف الكود عند الصلاحية)
        if not verify_code(user, code, 'change_email'):
            return Response({"detail": "Invalid or expired code."}, status=status.HTTP_400_BAD_REQUEST)

        # 4️⃣ التأكد مرة ثانية من أن البريد الجديد لم يُستخدم أثناء الانتظار
        if User.objects.filter(email=new_email).exists():
            return Response({"detail": "This email is already in use."}, status=status.HTTP_400_BAD_REQUEST)

        # 5️⃣ الكود صالح → نغيّر البريد ونحفظ
        user.email = new_email
        user.save()

        # 6️⃣ نرد نجاح (الكود تم حذفه داخل verify_code بالفعل)
        return Response({"detail": "Email changed successfully."}, status=status.HTTP_200_OK)
    
class GoogleLoginAPIView(APIView):
    
    permission_classes = []  # AllowAny if تريد

    def post(self, request):
        # 1️⃣: جلب الكود المرسَل من الـ frontend (بمتغير JSON: {"code": "<CODE>"})
        code = request.data.get("code")
        if not code:
            return Response({"detail": "No Google code provided"},
                            status=status.HTTP_400_BAD_REQUEST)

        # 2️⃣: تجهيز بيانات طلب تبادل الكود مع Google (POST إلى /token)
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        # 3️⃣: إرسال POST إلى Google (مهم: نستخدم data= لإرسال form-encoded)
        try:
            token_response = requests.post(token_url, data=data)
        except Exception as e:
            return Response({"detail": "Failed to reach Google token endpoint", "error": str(e)},
                            status=status.HTTP_502_BAD_GATEWAY)

        # 4️⃣: لو Google رجعت حالة غير 200 — إرجاع نص الرد للمساعدة في الـ debug
        if token_response.status_code != 200:
            # حاول نرجع json لو ممكن، وإلا النص الخام
            try:
                google_body = token_response.json()
            except Exception:
                google_body = token_response.text
            return Response({
                "detail": "Failed to exchange code with Google",
                "google_response": google_body
            }, status=status.HTTP_400_BAD_REQUEST)

        # 5️⃣: قراءة التوكنز من رد Google
        tokens = token_response.json()
        id_token_value = tokens.get("id_token")
        if not id_token_value:
            return Response({"detail": "No id_token in Google response", "google_response": tokens},
                            status=status.HTTP_400_BAD_REQUEST)

        # 6️⃣: التحقق من id_token باستخدام مكتبات Google واستخراج بيانات المستخدم
        try:
            idinfo = id_token.verify_oauth2_token(
                id_token_value,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )
        except ValueError as e:
            # التوكن غير صالح أو توقيع خاطئ أو مشاكل أخرى
            return Response({"detail": "Invalid id_token", "error": str(e)},
                            status=status.HTTP_400_BAD_REQUEST)

        # 7️⃣: استخراج الحقول الأساسية من idinfo
        email = idinfo.get("email")
        fullname = idinfo.get("name") or ""
        username = email.split("@")[0] if email else None

        if not email:
            return Response({"detail": "Google token did not provide email"},
                            status=status.HTTP_400_BAD_REQUEST)

        # 8️⃣: إنشاء المستخدم إذا لم يكن موجودًا أو جلب المستخدم الموجود
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": username or email,
                "first_name": fullname.split(" ")[0] if fullname else "",
                "last_name": " ".join(fullname.split(" ")[1:]) if fullname and len(fullname.split(" ")) > 1 else ""
            }
        )

        # 9️⃣: توليد JWT داخلي (Refresh + Access) باستخدام SimpleJWT
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # 🔟: إعداد Response ووضع التوكنز في HttpOnly cookies
        response = Response({"message": "Successfully logged in with Google"}, status=status.HTTP_200_OK)

        # 11️⃣: وضع الـ Access token في كوكي
        response.set_cookie(
            key=getattr(settings, "ACCESS_COOKIE_NAME", "access_token"),
            value=access_token,
            httponly=getattr(settings, "COOKIE_HTTPONLY", True),
            secure=getattr(settings, "COOKIE_SECURE", False),
            samesite=getattr(settings, "COOKIE_SAMESITE", "Lax"),
            max_age=getattr(settings, "ACCESS_COOKIE_MAX_AGE", 3600),
            path=getattr(settings, "COOKIE_PATH", "/"),
        )

        # 12️⃣: وضع الـ Refresh token في كوكي
        response.set_cookie(
            key=getattr(settings, "REFRESH_COOKIE_NAME", "refresh_token"),
            value=refresh_token,
            httponly=getattr(settings, "COOKIE_HTTPONLY", True),
            secure=getattr(settings, "COOKIE_SECURE", False),
            samesite=getattr(settings, "COOKIE_SAMESITE", "Lax"),
            max_age=getattr(settings, "REFRESH_COOKIE_MAX_AGE", 7 * 24 * 3600),
            path=getattr(settings, "COOKIE_PATH", "/"),
        )

        # 13️⃣: (اختياري) — إرجاع بيانات المستخدم في البودي (لو تحب)
        # response.data = {
        #     "message": "Successfully logged in with Google",
        #     "user": {
        #         "id": user.id,
        #         "email": user.email,
        #         "username": user.username,
        #     }
        # }

        # 14️⃣: إعادة الـ Response النهائية
        return response

class CurrentUserAPIView(APIView):
    permission_classes = [IsAuthenticated]  # لازم يكون مسجل دخول

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)