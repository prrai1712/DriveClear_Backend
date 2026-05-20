from django.urls import path

from apps.auth.views import (
    SendOTPView,
    VerifyOTPView,
    FirebaseVerifyView,
    RefreshTokenView,
    LogoutView,
)

urlpatterns = [
    path("firebase/verify/", FirebaseVerifyView.as_view(), name="firebase-verify"),
    path("otp/send/", SendOTPView.as_view(), name="otp-send"),
    path("otp/verify/", VerifyOTPView.as_view(), name="otp-verify"),
    path("token/refresh/", RefreshTokenView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
