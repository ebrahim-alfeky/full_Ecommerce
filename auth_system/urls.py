from django.contrib import admin
from django.urls import include, path
from .views import*
urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('resend-code/', ResendCodeView.as_view(), name='resend-verify-email'),
    path('login/', LoginView.as_view(), name='login'),
    path('refresh-access-token/',RefreshAccessTokenView.as_view(),name='refresh-access-token'),
    path('verify-access-token/',VerifyAccessTokenView.as_view(),name='verify-access-token'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('delete/', DeleteAccountView.as_view(), name='delete'),
    path('forget-password/', ForgotPasswordView.as_view(), name='forget-password'),
    path('rest-password/', ResetPasswordView.as_view(), name='rest-password'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('update-account/',UpdateAccountView.as_view(),name='update-account'),
    path('change-email/', ChangeEmailView.as_view(), name='change-email'),
    path('verify-change-email/', VerifyChangeEmailView.as_view(), name='verify-change-email'),
    path('google-login/', GoogleLoginAPIView.as_view(), name='google-login'),
    path('me/', CurrentUserAPIView.as_view(), name='current-user'),
    path('csrf/', get_csrf, name='get_csrf'),
]