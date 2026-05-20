from django.urls import path

from apps.payments.views import (
    CheckoutInitiateView,
    CheckoutVerifyView,
    CreateRazorpayOrderView,
    RazorpayWebhookView,
    VerifyPaymentView,
)

urlpatterns = [
    path("checkout/initiate/", CheckoutInitiateView.as_view(), name="checkout-initiate"),
    path("checkout/verify/", CheckoutVerifyView.as_view(), name="checkout-verify"),
    path("razorpay/create/", CreateRazorpayOrderView.as_view(), name="razorpay-create"),
    path("razorpay/verify/", VerifyPaymentView.as_view(), name="razorpay-verify"),
    path("razorpay/webhook/", RazorpayWebhookView.as_view(), name="razorpay-webhook"),
]
